<template>
  <view class="conversation-history">
    <!-- 标题栏 + 更多按钮 -->
    <BaseSection>
      历史对话
      <template #right>
        <view
          v-if="showMoreButton"
          class="more-btn-inline"
          hover-class="more-btn-hover"
          hover-stay-time="0"
          @tap.stop="handleMoreClick"
        >
          <text class="more-btn-text">更多</text>
        </view>
      </template>
    </BaseSection>

    <!-- 加载中状态 -->
    <view v-if="loading" class="loading-wrapper">
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
    <view v-else class="empty-wrapper">
      <text class="empty-text">暂无历史对话</text>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { getConversationList, type Conversation } from '@/api/conversation'
import { useProjectStore } from '@/stores/project'
import BaseSection from '@/components/base/BaseSection.vue'

// Store
const projectStore = useProjectStore()
const activeProject = computed(() => projectStore.activeProject)

// 对话列表数据
const conversationList = ref<Conversation[]>([])
const loading = ref(false)
const totalCount = ref(0)

// 是否显示更多按钮：有对话且总数>5 时显示
const showMoreButton = computed(() => {
  if (conversationList.value.length === 0) return false
  return totalCount.value > 5
})

// 定义事件
const emit = defineEmits<{
  click: [conversation: Conversation]
}>()

const DEFAULT_PAGE_SIZE = 5

/**
 * 加载历史对话列表
 * @param pageSize 每页数量，默认 5
 */
async function loadConversations(pageSize: number = DEFAULT_PAGE_SIZE) {
  // 如果没有激活的项目，不发送请求
  if (!activeProject.value?.id) {
    conversationList.value = []
    loading.value = false
    return
  }

  loading.value = true
  try {
    const projectId = parseInt(activeProject.value.id)

    if (isNaN(projectId)) {
      console.error('[ConversationHistory] 项目ID无效:', activeProject.value.id)
      conversationList.value = []
      loading.value = false
      return
    }

    const response = await getConversationList({
      pageNum: 1,
      pageSize,
      status: 'active',
      project_id: projectId,
    })

    if (response.code === 200 && response.data) {
      conversationList.value = response.data.list || []
      totalCount.value = response.data.total ?? 0
    } else {
      console.error('[ConversationHistory] 获取对话列表失败:', response.msg)
      conversationList.value = []
      totalCount.value = 0
    }
  } catch (error) {
    console.error('[ConversationHistory] 加载历史对话失败:', error)
    conversationList.value = []
    totalCount.value = 0
    // 不显示错误提示，避免干扰用户体验
  } finally {
    loading.value = false
  }
}

/**
 * 更多按钮点击：跳转到历史对话列表页
 */
function handleMoreClick() {
  const projectId = activeProject.value?.id
  if (!projectId) {
    uni.showToast({ title: '请先选择项目', icon: 'none' })
    return
  }
  uni.navigateTo({
    url: `/pages/conversation/list?projectId=${encodeURIComponent(projectId)}`,
    fail: () => uni.showToast({ title: '页面跳转失败', icon: 'none' }),
  })
}

/**
 * 格式化时间显示
 */
function formatTime(timeStr: string): string {
  const date = new Date(timeStr)
  const now = new Date()
  const diff = now.getTime() - date.getTime()
  const minutes = Math.floor(diff / 60000)
  const hours = Math.floor(diff / 3600000)
  const days = Math.floor(diff / 86400000)

  if (minutes < 1) {
    return '刚刚'
  } else if (minutes < 60) {
    return `${minutes}分钟前`
  } else if (hours < 24) {
    return `${hours}小时前`
  } else if (days < 7) {
    return `${days}天前`
  } else {
    return date.toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' })
  }
}

/**
 * 处理对话点击事件
 */
function handleClick(conversation: Conversation) {
  emit('click', conversation)
}

// 监听项目变化，重新加载对话列表
// 使用 immediate: true 确保在组件挂载时如果已有激活项目也会加载
watch(
  () => activeProject.value?.id,
  (newId, oldId) => {
    if (newId && newId !== oldId) {
      loadConversations(DEFAULT_PAGE_SIZE)
    } else if (!newId) {
      conversationList.value = []
      totalCount.value = 0
      loading.value = false
    }
  },
  { immediate: true }
)
</script>

<style lang="scss" scoped>
@import '@/styles/_variables.scss';

.conversation-history {
  margin-bottom: $spacing-lg;

  .loading-wrapper {
    padding: $spacing-lg;
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
      transition: all $transition-base;

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
    padding: $spacing-lg;
    text-align: center;

    .empty-text {
      font-size: $font-size-sm;
      color: $text-placeholder;
    }
  }

  .more-btn-inline {
    padding: 12rpx 28rpx;
    min-height: 56rpx;
    min-width: 88rpx;
    display: flex;
    align-items: center;
    justify-content: center;

    .more-btn-text {
      font-size: $font-size-sm;
      color: $primary-orange;
      font-weight: 500;
    }
  }

  .more-btn-hover {
    opacity: 0.7;
  }
}
</style>

