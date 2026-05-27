<template>
  <view class="conversation-list-page">
    <view class="page-nav" :style="{ paddingTop: safeArea.top + 'px' }">
      <view class="nav-bar">
        <view class="nav-back" @tap="goBack">
          <text class="nav-back-icon">‹</text>
        </view>
        <text class="nav-title">历史对话</text>
        <view class="nav-more" @tap="onMoreTap">
          <text class="nav-more-dots">••</text>
        </view>
      </view>
    </view>

    <scroll-view
      class="list-container"
      scroll-y
      :style="{ height: scrollHeight }"
      :refresher-enabled="true"
      :refresher-triggered="refreshing"
      @refresherrefresh="handleRefresh"
      @scrolltolower="handleLoadMore"
    >
      <view v-if="loading && conversationList.length === 0" class="loading-wrapper">
        <text class="loading-text">加载中...</text>
      </view>

      <template v-else-if="conversationList.length > 0">
        <view class="section-head">
          <SvgIcon name="history" :size="26" color="#998b82" />
          <text class="section-text">往期爆单对话归档 (共 {{ total }} 个)</text>
        </view>

        <view class="conversation-list">
          <view
            v-for="(conversation, index) in conversationList"
            :key="conversation.id"
            class="conversation-item"
            @tap="handleClick(conversation)"
          >
            <view class="conversation-icon-wrap" :class="recordIconVariant(index).bg">
              <SvgIcon
                :name="recordIconVariant(index).icon"
                :size="36"
                :color="recordIconVariant(index).color"
              />
            </view>
            <view class="conversation-content">
              <text class="conversation-title">{{ displayTitle(conversation) }}</text>
              <text class="time-text">{{ formatCreateTime(conversation.created_at) }}</text>
            </view>
            <view class="conversation-action-wrap">
              <text class="conversation-action">载入查看</text>
              <SvgIcon name="chevron-right" :size="28" color="#b8864d" />
            </view>
          </view>
        </view>
      </template>

      <view v-else-if="!loading" class="empty-wrapper">
        <SvgIcon name="history" :size="72" color="#d6d3d1" />
        <text class="empty-text">暂无历史对话</text>
      </view>

      <view v-if="loadingMore" class="load-more">
        <text>加载中...</text>
      </view>
      <view v-else-if="!hasMore && conversationList.length > 0" class="no-more">
        <text>没有更多了</text>
      </view>

      <view class="bottom-safe-area"></view>
    </scroll-view>
  </view>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { onLoad } from '@dcloudio/uni-app'
import { getConversationList, type Conversation } from '@/api/conversation'
import { useProjectStore } from '@/stores/project'
import { useSafeArea } from '@/composables/useSafeArea'
import SvgIcon from '@/components/base/SvgIcon.vue'

const projectStore = useProjectStore()
const { safeArea, updateSafeArea } = useSafeArea()
const PAGE_SIZE = 20
const RECORD_ICON_VARIANTS = [
  { icon: 'trending-up', color: '#EA580C', bg: 'conversation-icon-wrap--orange' },
  { icon: 'lightbulb', color: '#D97706', bg: 'conversation-icon-wrap--amber' },
  { icon: 'clapperboard', color: '#7C3AED', bg: 'conversation-icon-wrap--violet' },
  { icon: 'sparkles', color: '#CA8A04', bg: 'conversation-icon-wrap--gold' },
  { icon: 'megaphone', color: '#DB2777', bg: 'conversation-icon-wrap--pink' },
  { icon: 'send', color: '#2563EB', bg: 'conversation-icon-wrap--blue' },
] as const

const conversationList = ref<Conversation[]>([])
const loading = ref(false)
const loadingMore = ref(false)
const refreshing = ref(false)
const pageNum = ref(1)
const total = ref(0)
const projectId = ref<number | null>(null)

const hasMore = computed(() => conversationList.value.length < total.value)

const scrollHeight = computed(() => {
  const navH = safeArea.value.top + 44
  return `calc(100vh - ${navH}px)`
})

function goBack() {
  uni.navigateBack({
    fail: () => {
      uni.switchTab({ url: '/pages/project/index' })
    },
  })
}

function onMoreTap() {
  uni.showActionSheet({
    itemList: ['刷新列表'],
    success: (res) => {
      if (res.tapIndex === 0) handleRefresh()
    },
  })
}

function recordIconVariant(index: number) {
  return RECORD_ICON_VARIANTS[index % RECORD_ICON_VARIANTS.length]
}

function stripLeadingEmoji(s: string): string {
  return s.replace(/^[\uFE0F\s]*(?:[\u{1F300}-\u{1FAFF}\u2600-\u27BF]\uFE0F?\s*)+/u, '').trim() || s
}

function displayTitle(item: Conversation): string {
  const title = (item.title || '未命名对话').trim()
  return stripLeadingEmoji(title)
}

function formatCreateTime(timeStr: string): string {
  if (!timeStr) return '创建时间：—'
  const date = new Date(timeStr)
  if (Number.isNaN(date.getTime())) return '创建时间：—'

  const now = new Date()
  const pad = (n: number) => String(n).padStart(2, '0')
  const timePart = `${pad(date.getHours())}:${pad(date.getMinutes())}`

  const startOfToday = new Date(now.getFullYear(), now.getMonth(), now.getDate())
  const startOfDate = new Date(date.getFullYear(), date.getMonth(), date.getDate())
  const dayDiff = Math.floor((startOfToday.getTime() - startOfDate.getTime()) / 86400000)

  if (dayDiff === 0) return `创建时间：今天 ${timePart}`
  if (dayDiff === 1) return `创建时间：昨天 ${timePart}`
  if (dayDiff === 2) return `创建时间：前天 ${timePart}`
  if (dayDiff < 7) return `创建时间：${dayDiff}天前 ${timePart}`
  const datePart = date.toLocaleDateString('zh-CN', { month: 'numeric', day: 'numeric' })
  return `创建时间：${datePart} ${timePart}`
}

async function loadConversations(isRefresh = false) {
  const pid = projectId.value
  if (!pid || isNaN(pid)) {
    conversationList.value = []
    loading.value = false
    return
  }

  if (isRefresh) {
    pageNum.value = 1
    refreshing.value = true
  } else if (pageNum.value === 1) {
    loading.value = true
  } else {
    loadingMore.value = true
  }

  try {
    const response = await getConversationList({
      pageNum: pageNum.value,
      pageSize: PAGE_SIZE,
      status: 'active',
      project_id: pid,
    })

    if (response.code === 200 && response.data) {
      const list = response.data.list || []
      total.value = response.data.total ?? 0

      if (isRefresh || pageNum.value === 1) {
        conversationList.value = list
      } else {
        conversationList.value = [...conversationList.value, ...list]
      }
      pageNum.value++
    }
  } catch (error) {
    console.error('[ConversationList] 加载失败:', error)
    uni.showToast({ title: '加载失败', icon: 'none' })
  } finally {
    loading.value = false
    loadingMore.value = false
    refreshing.value = false
  }
}

async function handleRefresh() {
  await loadConversations(true)
}

async function handleLoadMore() {
  if (loadingMore.value || !hasMore.value) return
  await loadConversations(false)
}

function handleClick(conversation: Conversation) {
  const params: Record<string, string> = {
    conversationId: String(conversation.id),
  }
  if (conversation.agent_id) {
    params.agentId = String(conversation.agent_id)
  }
  const query = Object.entries(params)
    .map(([k, v]) => `${k}=${encodeURIComponent(v)}`)
    .join('&')
  uni.navigateTo({
    url: `/pages/copywriting/index?${query}`,
    fail: () => uni.showToast({ title: '页面跳转失败', icon: 'none' }),
  })
}

onLoad((options?: { projectId?: string }) => {
  if (options?.projectId) {
    const pid = parseInt(options.projectId)
    if (!isNaN(pid)) projectId.value = pid
  }
})

onMounted(() => {
  updateSafeArea()
  if (!projectId.value && projectStore.activeProject?.id) {
    const pid = parseInt(projectStore.activeProject.id)
    if (!isNaN(pid)) projectId.value = pid
  }
  loadConversations(true)
})
</script>

<style lang="scss" scoped>
$page-bg: #fdfbf7;
$text-primary: #332d2b;
$text-muted: #998b82;
$accent: #b8864d;
$card-border: #f2e6d8;

.conversation-list-page {
  min-height: 100vh;
  background: $page-bg;
}

.page-nav {
  background: $page-bg;
}

.nav-bar {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  height: 88rpx;
  padding: 0 32rpx;
}

.nav-back {
  position: absolute;
  left: 24rpx;
  width: 64rpx;
  height: 64rpx;
  display: flex;
  align-items: center;
  justify-content: center;

  &:active {
    opacity: 0.6;
  }
}

.nav-back-icon {
  font-size: 48rpx;
  font-weight: 300;
  color: $text-primary;
  line-height: 1;
}

.nav-title {
  font-size: 34rpx;
  font-weight: 700;
  color: $text-primary;
}

.nav-more {
  position: absolute;
  right: 32rpx;
  min-width: 72rpx;
  height: 56rpx;
  padding: 0 20rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(255, 255, 255, 0.85);
  border: 1rpx solid $card-border;
  border-radius: 999rpx;

  &:active {
    opacity: 0.75;
  }
}

.nav-more-dots {
  font-size: 22rpx;
  letter-spacing: 2rpx;
  color: $text-muted;
  line-height: 1;
}

.list-container {
  box-sizing: border-box;
  padding: 8rpx 32rpx 0;
}

.section-head {
  display: flex;
  align-items: center;
  gap: 10rpx;
  padding: 24rpx 0 28rpx;
}

.section-text {
  font-size: 28rpx;
  font-weight: 600;
  color: $text-primary;
}

.loading-wrapper {
  padding: 120rpx 32rpx;
  text-align: center;

  .loading-text {
    font-size: 28rpx;
    color: $text-muted;
  }
}

.conversation-list {
  display: flex;
  flex-direction: column;
  gap: 24rpx;

  .conversation-item {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 20rpx;
    padding: 28rpx 30rpx;
    background: #fff;
    border: 1rpx solid $card-border;
    border-radius: 24rpx;

    &:active {
      background: #fffaf5;
    }

    .conversation-icon-wrap {
      flex-shrink: 0;
      width: 72rpx;
      height: 72rpx;
      border-radius: 18rpx;
      display: flex;
      align-items: center;
      justify-content: center;

      &--orange {
        background: #fff7ed;
        border: 1rpx solid #fed7aa;
      }

      &--amber {
        background: #fffbeb;
        border: 1rpx solid #fde68a;
      }

      &--violet {
        background: #f5f3ff;
        border: 1rpx solid #ddd6fe;
      }

      &--gold {
        background: #fefce8;
        border: 1rpx solid #fef08a;
      }

      &--pink {
        background: #fdf2f8;
        border: 1rpx solid #fbcfe8;
      }

      &--blue {
        background: #eff6ff;
        border: 1rpx solid #bfdbfe;
      }
    }

    .conversation-content {
      flex: 1;
      min-width: 0;
      display: flex;
      flex-direction: column;
      gap: 12rpx;

      .conversation-title {
        font-size: 30rpx;
        font-weight: 600;
        color: $text-primary;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
      }

      .time-text {
        font-size: 24rpx;
        color: $text-muted;
      }
    }

    .conversation-action-wrap {
      flex-shrink: 0;
      display: flex;
      flex-direction: row;
      align-items: center;
      gap: 4rpx;
    }

    .conversation-action {
      font-size: 24rpx;
      color: $accent;
      white-space: nowrap;
    }
  }
}

.empty-wrapper {
  padding: 160rpx 32rpx;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16rpx;

  .empty-text {
    font-size: 28rpx;
    color: $text-muted;
  }
}

.load-more,
.no-more {
  padding: 32rpx;
  text-align: center;
  font-size: 24rpx;
  color: $text-muted;
}

.bottom-safe-area {
  height: calc(32rpx + env(safe-area-inset-bottom));
}
</style>
