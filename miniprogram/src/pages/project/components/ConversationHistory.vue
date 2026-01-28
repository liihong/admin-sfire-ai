<template>
  <view class="conversation-history">
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
import { ref, computed, watch, onMounted, nextTick } from 'vue'
import { getConversationList, type Conversation } from '@/api/conversation'
import { useProjectStore } from '@/stores/project'

// Store
const projectStore = useProjectStore()
const activeProject = computed(() => projectStore.activeProject)

// 对话列表数据
const conversationList = ref<Conversation[]>([])
const loading = ref(false)

// 定义事件
const emit = defineEmits<{
  click: [conversation: Conversation]
}>()

/**
 * 加载历史对话列表
 */
async function loadConversations() {
  console.log('[ConversationHistory] loadConversations 被调用')
  console.log('[ConversationHistory] activeProject.value:', activeProject.value)
  
  // 如果没有激活的项目，不发送请求
  if (!activeProject.value?.id) {
    console.log('[ConversationHistory] 没有激活的项目，跳过加载')
    conversationList.value = []
    loading.value = false
    return
  }

  loading.value = true
  try {
    const projectId = parseInt(activeProject.value.id)
    console.log('[ConversationHistory] 准备请求，projectId:', projectId)
    
    if (isNaN(projectId)) {
      console.error('[ConversationHistory] 项目ID无效:', activeProject.value.id)
      conversationList.value = []
      loading.value = false
      return
    }

    console.log('[ConversationHistory] 开始请求对话列表...')
    const response = await getConversationList({
      pageNum: 1,
      pageSize: 5, // 显示最近 5 条对话
      status: 'active',
      project_id: projectId,
    })

    console.log('[ConversationHistory] 请求响应:', response)

    if (response.code === 200 && response.data?.list) {
      conversationList.value = response.data.list
      console.log('[ConversationHistory] 加载成功，对话数量:', response.data.list.length)
    } else {
      console.error('[ConversationHistory] 获取对话列表失败:', response.msg)
      conversationList.value = []
    }
  } catch (error) {
    console.error('[ConversationHistory] 加载历史对话失败:', error)
    conversationList.value = []
    // 不显示错误提示，避免干扰用户体验
  } finally {
    loading.value = false
  }
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

// 组件挂载时检查并加载
onMounted(() => {
  console.log('[ConversationHistory] 组件挂载')
  console.log('[ConversationHistory] 当前 activeProject:', activeProject.value)
  
  // 等待下一个 tick，确保父组件的初始化完成
  nextTick(() => {
    console.log('[ConversationHistory] nextTick 后 activeProject:', activeProject.value)
    // 如果已经有激活项目，立即加载
    if (activeProject.value?.id) {
      loadConversations()
    } else {
      // 如果没有激活项目，等待一段时间后重试（给父组件时间初始化）
      setTimeout(() => {
        console.log('[ConversationHistory] setTimeout 后 activeProject:', activeProject.value)
        if (activeProject.value?.id) {
          loadConversations()
        }
      }, 500)
    }
  })
})

// 监听项目变化，重新加载对话列表
// 使用 immediate: true 确保在组件挂载时如果已有激活项目也会加载
watch(
  () => activeProject.value?.id,
  (newId, oldId) => {
    console.log('[ConversationHistory] watch 触发，newId:', newId, 'oldId:', oldId)
    if (newId && newId !== oldId) {
      // 只有当项目ID变化时才加载，避免重复请求
      loadConversations()
    } else if (!newId) {
      // 如果没有激活项目，清空列表
      conversationList.value = []
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
}
</style>

