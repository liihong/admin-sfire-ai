<template>
  <view class="conversation-list-page">
    <BaseHeader title="历史对话" @back="goBack" />

    <scroll-view
      class="list-container"
      scroll-y
      :refresher-enabled="true"
      :refresher-triggered="refreshing"
      @refresherrefresh="handleRefresh"
      @scrolltolower="handleLoadMore"
    >
      <!-- 加载中（首次） -->
      <view v-if="loading && conversationList.length === 0" class="loading-wrapper">
        <text class="loading-text">加载中...</text>
      </view>

      <!-- 对话列表 -->
      <view v-else-if="conversationList.length > 0" class="conversation-list">
        <view
          v-for="conversation in conversationList"
          :key="conversation.id"
          class="conversation-item"
          @tap="handleClick(conversation)"
        >
          <view class="conversation-content">
            <text class="conversation-title">{{ conversation.title }}</text>
            <view class="conversation-meta">
              <text v-if="conversation.agent_name" class="agent-name">
                {{ conversation.agent_name }}
              </text>
              <text class="time-text">{{ formatTime(conversation.created_at) }}</text>
            </view>
          </view>
          <view class="conversation-arrow">
            <text class="arrow-icon">›</text>
          </view>
        </view>
      </view>

      <!-- 空状态 -->
      <view v-else-if="!loading" class="empty-wrapper">
        <text class="empty-text">暂无历史对话</text>
      </view>

      <!-- 加载更多 -->
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
import BaseHeader from '@/components/base/BaseHeader.vue'

const projectStore = useProjectStore()
const PAGE_SIZE = 20

const conversationList = ref<Conversation[]>([])
const loading = ref(false)
const loadingMore = ref(false)
const refreshing = ref(false)
const pageNum = ref(1)
const total = ref(0)
const projectId = ref<number | null>(null)

const hasMore = computed(() => conversationList.value.length < total.value)

function goBack() {
  uni.navigateBack({
    fail: () => {
      uni.switchTab({ url: '/pages/project/index' })
    }
  })
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

function formatTime(timeStr: string): string {
  const date = new Date(timeStr)
  const now = new Date()
  const diff = now.getTime() - date.getTime()
  const minutes = Math.floor(diff / 60000)
  const hours = Math.floor(diff / 3600000)
  const days = Math.floor(diff / 86400000)

  if (minutes < 1) return '刚刚'
  if (minutes < 60) return `${minutes}分钟前`
  if (hours < 24) return `${hours}小时前`
  if (days < 7) return `${days}天前`
  return date.toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' })
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
  if (!projectId.value && projectStore.activeProject?.id) {
    const pid = parseInt(projectStore.activeProject.id)
    if (!isNaN(pid)) projectId.value = pid
  }
  loadConversations(true)
})
</script>

<style lang="scss" scoped>
@import '@/styles/_variables.scss';

.conversation-list-page {
  min-height: 100vh;
  background: linear-gradient(180deg, #FAFBFC 0%, #F5F7FA 100%);
}

.list-container {
  height: calc(100vh - 120rpx);
  padding: 24rpx $spacing-lg;
}

.loading-wrapper {
  padding: $spacing-xl;
  text-align: center;
  .loading-text {
    font-size: $font-size-sm;
    color: $text-placeholder;
  }
}

.conversation-list {
  display: flex;
  flex-direction: column;
  gap: $spacing-sm;

  .conversation-item {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: $spacing-md;
    background: $white;
    border-radius: $radius-md;
    box-shadow: 0 2rpx 8rpx rgba(0, 0, 0, 0.06);

    &:active {
      transform: scale(0.98);
      background: $bg-light;
    }

    .conversation-content {
      flex: 1;
      min-width: 0;
      display: flex;
      flex-direction: column;
      gap: 8rpx;

      .conversation-title {
        font-size: $font-size-md;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
      }

      .conversation-meta {
        display: flex;
        align-items: center;
        gap: $spacing-sm;

        .agent-name {
          font-size: $font-size-xs;
          color: $primary-orange;
          padding: 2rpx 8rpx;
          background: rgba($primary-orange, 0.1);
          border-radius: $radius-sm;
        }

        .time-text {
          font-size: $font-size-xs;
          color: $text-placeholder;
        }
      }
    }

    .conversation-arrow {
      margin-left: $spacing-sm;
      flex-shrink: 0;
      .arrow-icon {
        font-size: 48rpx;
        color: $text-placeholder;
        font-weight: 300;
      }
    }
  }
}

.empty-wrapper {
  padding: $spacing-xl;
  text-align: center;
  .empty-text {
    font-size: $font-size-sm;
    color: $text-placeholder;
  }
}

.load-more,
.no-more {
  padding: $spacing-md;
  text-align: center;
  font-size: $font-size-xs;
  color: $text-placeholder;
}

.bottom-safe-area {
  height: calc(40rpx + env(safe-area-inset-bottom));
}
</style>
