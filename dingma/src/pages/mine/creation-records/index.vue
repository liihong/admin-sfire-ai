<template>
  <view class="page-creation-records">
    <!-- 自定义顶栏：原生 view/text，仿小程序胶囊 -->
    <view class="page-nav" :style="{ paddingTop: safeArea.top + 'px' }">
      <view class="nav-bar">
        <view class="nav-back" @tap="goBack">
          <text class="nav-back-icon">&lt;</text>
        </view>
        <text class="nav-title">历史对话</text>
        <view class="nav-capsule">
          <view class="nav-cap-btn" @tap="onMoreTap">
            <text class="nav-cap-ico">⋯</text>
          </view>
          <view class="nav-cap-split" />
          <view class="nav-cap-btn" @tap="goHomeTab">
            <text class="nav-cap-target">◎</text>
          </view>
        </view>
      </view>
    </view>

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
        <view class="native-spinner" aria-hidden="true">
          <view class="native-spinner-dot" />
          <view class="native-spinner-dot native-spinner-dot--delay1" />
          <view class="native-spinner-dot native-spinner-dot--delay2" />
        </view>
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
            <view class="record-left">
              <text class="record-title">{{ displayTitle(item, index) }}</text>
              <text v-if="conversationPreview(item)" class="record-preview">{{
                conversationPreview(item)
              }}</text>
              <text class="record-time">{{ formatCreateTime(item.created_at) }}</text>
            </view>
            <text class="record-action">载入查看 ></text>
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

function goHomeTab() {
  uni.switchTab({ url: '/pages/home/index' })
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
  const rawFull = (item.title || '未命名对话').trim()
  const firstLine = rawFull.split(/\r?\n/).map((l) => l.trim()).find(Boolean) || '未命名对话'

  /** 首行已带 emoji 则整行作为标题（不再重复加） */
  if (/^[\u{1F300}-\u{1FAFF}\u2600-\u27BF]/u.test(firstLine)) return firstLine

  const withoutEmoji = stripLeadingEmoji(firstLine)
  return `${TITLE_EMOJIS[index % TITLE_EMOJIS.length]} ${withoutEmoji}`
}

/** 去掉首行 emoji 后用于从标题中取「纯文案」前缀 */
function stripLeadingEmoji(s: string): string {
  return s.replace(/^[\uFE0F\s]*(?:[\u{1F300}-\u{1FAFF}\u2600-\u27BF]\uFE0F?\s*)+/u, '').trim() || s
}

/** 摘要行：接口暂无 last_message 时，用标题中换行后的内容模拟列表第二行预览 */
function conversationPreview(item: Conversation): string {
  const t = (item.title || '').trim()
  const lines = t.split(/\r?\n/).map((x) => x.trim()).filter(Boolean)
  if (lines.length >= 2) return truncateOneLine(lines.slice(1).join(' '), 76)
  if (item.agent_name) return truncateOneLine(item.agent_name, 76)
  return ''
}

function truncateOneLine(s: string, max: number): string {
  if (s.length <= max) return s
  return `${s.slice(0, max)}…`
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

$page-bg: #f7f7f7;
$text-primary: #1a1a1a;
$text-muted: #8e8e8e;
$accent-load: #c9a227;

.page-creation-records {
  display: flex;
  flex-direction: column;
  height: 100vh;
  overflow: hidden;
  background: $page-bg;
}

.page-nav {
  flex-shrink: 0;
  background: #ffffff;
}

.section-head-strip {
  flex-shrink: 0;
  box-sizing: border-box;
  width: 100%;
  padding: 18rpx 32rpx 14rpx;
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

.nav-capsule {
  position: absolute;
  right: 24rpx;
  top: 50%;
  transform: translateY(-50%);
  height: 56rpx;
  padding: 0 8rpx;
  display: flex;
  flex-direction: row;
  align-items: center;
  background: rgba(255, 255, 255, 0.92);
  border: 1rpx solid rgba(0, 0, 0, 0.1);
  border-radius: 999rpx;
  box-sizing: border-box;
}

.nav-cap-btn {
  min-width: 56rpx;
  height: 48rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0 12rpx;

  &:active {
    opacity: 0.65;
  }
}

.nav-cap-ico {
  font-size: 28rpx;
  line-height: 1;
  color: rgba(0, 0, 0, 0.55);
}

.nav-cap-target {
  font-size: 26rpx;
  line-height: 1;
  color: rgba(0, 0, 0, 0.55);
}

.nav-cap-split {
  width: 1rpx;
  height: 28rpx;
  background: rgba(0, 0, 0, 0.12);
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
  font-size: 26rpx;
  line-height: 1;
  opacity: 0.72;
}

.section-text {
  font-size: 26rpx;
  font-weight: 500;
  color: rgba(142, 142, 142, 0.95);
}

.record-list {
  display: flex;
  flex-direction: column;
  gap: 28rpx;
}

/** 左文右链：与设计稿一致的卡片排版 */
.record-card {
  display: flex;
  flex-direction: row;
  align-items: stretch;
  justify-content: space-between;
  gap: 20rpx;
  padding: 28rpx 30rpx;
  background: #ffffff;
  border-radius: 24rpx;
  box-sizing: border-box;
  box-shadow:
    0 6rpx 24rpx rgba(0, 0, 0, 0.05),
    0 2rpx 8rpx rgba(0, 0, 0, 0.03);

  &:active {
    opacity: 0.96;
  }
}

.record-left {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 10rpx;
  padding-top: 2rpx;
  padding-bottom: 2rpx;
}

.record-title {
  font-size: 30rpx;
  font-weight: 700;
  color: $text-primary;
  line-height: 1.45;
  word-break: break-all;
}

.record-preview {
  font-size: 24rpx;
  color: #6b6b6b;
  line-height: 1.5;
  display: -webkit-box;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2;
  overflow: hidden;
}

.record-time {
  font-size: 22rpx;
  color: $text-muted;
}

.record-action {
  flex-shrink: 0;
  align-self: center;
  font-size: 24rpx;
  color: $accent-load;
  white-space: nowrap;
}

.native-spinner {
  display: flex;
  flex-direction: row;
  align-items: center;
  justify-content: center;
  gap: 10rpx;
}

.native-spinner-dot {
  width: 12rpx;
  height: 12rpx;
  border-radius: 50%;
  background: $accent-load;
  animation: cr-spinner 1.2s ease-in-out infinite;

  &--delay1 {
    animation-delay: 0.15s;
  }

  &--delay2 {
    animation-delay: 0.3s;
  }
}

@keyframes cr-spinner {
  0%,
  80%,
  100% {
    transform: scale(0.65);
    opacity: 0.45;
  }
  40% {
    transform: scale(1);
    opacity: 1;
  }
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
