<template>
  <view class="page-creation-records">
    <!-- 自定义顶栏 -->
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

    <!-- 有小节标题时固定在顶栏下方，仅下列表区域滚动 -->
    <view v-if="list.length > 0" class="section-head-strip">
      <view class="section-head">
        <text class="section-icon">🕒</text>
        <text class="section-text">往期爆单对话归档 (共 {{ total }} 个)</text>
      </view>
    </view>

    <scroll-view
      class="list-scroll"
      scroll-y
      :refresher-enabled="true"
      :refresher-triggered="refreshing"
      @refresherrefresh="handleRefresh"
      @scrolltolower="handleLoadMore"
    >
      <view v-if="loading && list.length === 0" class="state-wrap">
        <text class="state-text">加载中...</text>
      </view>

      <template v-else-if="list.length > 0">
        <view class="record-list">
          <view
            v-for="(item, index) in list"
            :key="item.id"
            class="record-card"
            @tap="openConversation(item)"
          >
            <view class="record-main">
              <text class="record-title">{{ displayTitle(item, index) }}</text>
              <text class="record-time">{{ formatCreateTime(item.created_at) }}</text>
            </view>
            <text class="record-action">载入查看 ›</text>
          </view>
        </view>
      </template>

      <view v-else class="state-wrap">
        <text class="state-emoji">💬</text>
        <text class="state-text">暂无历史对话</text>
        <text class="state-hint">在爆款助手与 AI 对话后，历史会保存在这里</text>
      </view>

      <view v-if="loadingMore" class="footer-state">
        <text>加载中...</text>
      </view>
      <view v-else-if="!hasMore && list.length > 0" class="footer-state muted">
        <text>没有更多了</text>
      </view>

      <view class="bottom-safe" />
    </scroll-view>
  </view>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, nextTick } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import { getConversationList, type Conversation } from '@/api/conversation'
import { useAuthStore } from '@/stores/auth'
import { useSafeArea } from '@/composables/useSafeArea'

const authStore = useAuthStore()
const { safeArea, updateSafeArea } = useSafeArea()
const PAGE_SIZE = 20

const TITLE_EMOJIS = ['🔥', '💡', '🎬', '✨', '📣', '🛒']

const list = ref<Conversation[]>([])
const loading = ref(false)
const loadingMore = ref(false)
const refreshing = ref(false)
const pageNum = ref(1)
const total = ref(0)

const hasMore = computed(() => list.value.length < total.value)

function goBack() {
  uni.navigateBack({
    fail: () => uni.switchTab({ url: '/pages/mine/index' }),
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

function displayTitle(item: Conversation, index: number): string {
  const title = (item.title || '未命名对话').trim()
  if (/^[\u{1F300}-\u{1FAFF}\u2600-\u27BF]/u.test(title)) return title
  return `${TITLE_EMOJIS[index % TITLE_EMOJIS.length]} ${title}`
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

async function loadList(isRefresh = false) {
  if (!authStore.isLoggedIn) {
    list.value = []
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
    })

    if (response.code === 200 && response.data) {
      const chunk = response.data.list || []
      total.value = response.data.total ?? 0

      if (isRefresh || pageNum.value === 1) {
        list.value = chunk
      } else {
        list.value = [...list.value, ...chunk]
      }
      pageNum.value++
    }
  } catch (e) {
    console.error('[creation-records]', e)
    uni.showToast({ title: '加载失败', icon: 'none' })
  } finally {
    loading.value = false
    loadingMore.value = false
    refreshing.value = false
  }
}

async function handleRefresh() {
  await loadList(true)
}

async function handleLoadMore() {
  if (loadingMore.value || loading.value || !hasMore.value) return
  await loadList(false)
}

function openConversation(conv: Conversation) {
  const q = [`conversationId=${encodeURIComponent(String(conv.id))}`]
  if (conv.agent_id) {
    q.push(`agentId=${encodeURIComponent(String(conv.agent_id))}`)
  }
  uni.navigateTo({
    url: `/pages/aichat/index?${q.join('&')}`,
    fail: () => uni.showToast({ title: '页面打开失败', icon: 'none' }),
  })
}

function ensureLogin() {
  if (authStore.isLoggedIn) return true
  uni.showToast({ title: '请先登录', icon: 'none' })
  setTimeout(() => {
    uni.navigateTo({ url: '/pages/login/index' })
  }, 400)
  return false
}

onMounted(async () => {
  updateSafeArea()
  if (!ensureLogin()) return
  await nextTick()
  loadList(false)
})

onShow(() => {
  if (!authStore.isLoggedIn) {
    list.value = []
    total.value = 0
    return
  }
})
</script>

<style scoped lang="scss">
@import '@/styles/_variables.scss';

$text-primary: #332d2b;
$text-muted: #998b82;
$accent: #b8864d;

.page-creation-records {
  display: flex;
  flex-direction: column;
  height: 100vh;
  overflow: hidden;
  background: $white;
}

.page-nav {
  flex-shrink: 0;
  background: $white;
}

/** 不参与滚动：与白底列表区隔开层次 */
.section-head-strip {
  flex-shrink: 0;
  box-sizing: border-box;
  width: 100%;
  padding: 18rpx 32rpx 14rpx;
  background: $white;
  border-bottom: 1rpx solid rgba(44, 30, 26, 0.06);
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
  border: 1rpx solid rgba(44, 30, 26, 0.08);
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

.list-scroll {
  flex: 1;
  height: 0;
  min-height: 0;
  box-sizing: border-box;
  padding: 8rpx 32rpx 0;
}

.section-head {
  display: flex;
  align-items: center;
  gap: 10rpx;
  padding: 0;
}

.section-icon {
  font-size: 28rpx;
  line-height: 1;
}

.section-text {
  font-size: 28rpx;
  font-weight: 600;
  color: $text-primary;
}

.record-list {
  display: flex;
  flex-direction: column;
  gap: 28rpx;
}

.record-card {
  display: flex;
  flex-direction: row;
  align-items: center;
  justify-content: space-between;
  gap: 20rpx;
  padding: 28rpx 30rpx;
  background: $white;
  border: 1rpx solid rgba(44, 30, 26, 0.08);
  border-radius: 36rpx;
  box-sizing: border-box;
  box-shadow: $shadow-card-elevated-list;
  transition:
    opacity 0.2s ease,
    transform 0.22s cubic-bezier(0.33, 0.86, 0.42, 1),
    box-shadow 0.22s cubic-bezier(0.33, 0.86, 0.42, 1);

  &:active {
    opacity: 0.98;
    transform: translateY(2rpx) scale(0.992);
    box-shadow: $shadow-card-elevated-list-active;
  }
}

.record-main {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 12rpx;
}

.record-title {
  font-size: 30rpx;
  font-weight: 600;
  color: $text-primary;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.record-time {
  font-size: 24rpx;
  color: $text-muted;
}

.record-action {
  flex-shrink: 0;
  font-size: 24rpx;
  color: $accent;
  white-space: nowrap;
}

.state-wrap {
  padding: 160rpx 32rpx;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16rpx;
}

.state-emoji {
  font-size: 64rpx;
  margin-bottom: 8rpx;
}

.state-text {
  font-size: 28rpx;
  color: $text-muted;
}

.state-hint {
  font-size: 24rpx;
  color: $text-muted;
  text-align: center;
  line-height: 1.6;
  opacity: 0.85;
}

.footer-state {
  padding: 32rpx;
  text-align: center;
  font-size: 24rpx;
  color: $text-muted;

  &.muted {
    opacity: 0.75;
  }
}

.bottom-safe {
  height: calc(32rpx + env(safe-area-inset-bottom));
}
</style>
