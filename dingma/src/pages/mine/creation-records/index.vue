<template>
  <view class="page-creation-records">
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

      <view v-else-if="list.length > 0" class="record-list">
        <view
          v-for="item in list"
          :key="item.id"
          class="record-card"
          @tap="openConversation(item)"
        >
          <view class="record-main">
            <text class="record-title">{{ item.title || '未命名对话' }}</text>
            <view class="record-meta">
              <text v-if="item.agent_name" class="meta-tag">{{ item.agent_name }}</text>
              <text class="meta-time">{{ formatTime(item.updated_at || item.created_at) }}</text>
            </view>
          </view>
          <text class="record-chevron">›</text>
        </view>
      </view>

      <view v-else class="state-wrap">
        <text class="state-text">暂无创作记录</text>
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
import { ref, computed, onMounted } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import { getConversationList, type Conversation } from '@/api/conversation'
import { useAuthStore } from '@/stores/auth'

const authStore = useAuthStore()
const PAGE_SIZE = 20

const list = ref<Conversation[]>([])
const loading = ref(false)
const loadingMore = ref(false)
const refreshing = ref(false)
const pageNum = ref(1)
const total = ref(0)

const hasMore = computed(() => list.value.length < total.value)

function formatTime(timeStr: string): string {
  if (!timeStr) return ''
  const date = new Date(timeStr)
  const now = new Date()
  const diff = now.getTime() - date.getTime()
  const minutes = Math.floor(diff / 60000)
  const hours = Math.floor(diff / 3600000)
  const days = Math.floor(diff / 86400000)

  if (minutes < 1) return '刚刚'
  if (minutes < 60) return `${minutes} 分钟前`
  if (hours < 24) return `${hours} 小时前`
  if (days < 7) return `${days} 天前`
  return date.toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' })
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

onMounted(() => {
  if (!ensureLogin()) return
  loadList(true)
})

onShow(() => {
  if (!authStore.isLoggedIn) {
    list.value = []
    return
  }
})
</script>

<style scoped lang="scss">
.page-creation-records {
  min-height: 100vh;
  background: #f1f5f9;
}

.list-scroll {
  height: 100vh;
  box-sizing: border-box;
  padding: 24rpx;
}

.state-wrap {
  padding: 120rpx 32rpx;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16rpx;
}

.state-text {
  font-size: 28rpx;
  color: #64748b;
}

.state-hint {
  font-size: 24rpx;
  color: #94a3b8;
  text-align: center;
  line-height: 1.5;
}

.record-list {
  display: flex;
  flex-direction: column;
  gap: 20rpx;
}

.record-card {
  background: #fff;
  border-radius: 24rpx;
  padding: 28rpx 32rpx;
  display: flex;
  flex-direction: row;
  align-items: center;
  justify-content: space-between;
  box-shadow: 0 4rpx 20rpx rgba(15, 23, 42, 0.05);

  &:active {
    opacity: 0.92;
    background: #fafbfc;
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
  color: #0f172a;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.record-meta {
  display: flex;
  flex-direction: row;
  align-items: center;
  flex-wrap: wrap;
  gap: 12rpx 16rpx;
}

.meta-tag {
  font-size: 22rpx;
  color: #2563eb;
  background: rgba(37, 99, 235, 0.08);
  padding: 4rpx 14rpx;
  border-radius: 999rpx;
}

.meta-time {
  font-size: 22rpx;
  color: #94a3b8;
}

.record-chevron {
  font-size: 40rpx;
  color: #cbd5e1;
  font-weight: 300;
  flex-shrink: 0;
  margin-left: 16rpx;
}

.footer-state {
  padding: 28rpx;
  text-align: center;
  font-size: 24rpx;
  color: #64748b;

  &.muted {
    color: #94a3b8;
  }
}

.bottom-safe {
  height: calc(40rpx + env(safe-area-inset-bottom));
}
</style>
