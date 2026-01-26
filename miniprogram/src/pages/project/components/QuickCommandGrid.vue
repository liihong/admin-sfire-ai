<template>
  <view class="quick-command-grid">
    <view
v-for="entry in quickEntryList" :key="entry.id"
      class="command-card"
@tap="handleClick(entry)"
    >
      <view class="command-icon-wrapper">
       <AgentIcon :iconName="entry.icon_class" :size="48" />
      </view>
      <view class="command-content">
       <text class="command-title">{{ entry.title }}</text>
        <text class="command-desc">{{ entry.subtitle || '' }}</text>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { AgentIcon } from '@/components/base'
import { getQuickEntries, type QuickEntry } from '@/api/quickEntry'
import { type ResponseData } from '@/utils/request'
import { useAgentStore } from '@/stores/agent'
import { useQuickEntryStore } from '@/stores/quickEntry'

// ============== Store ==============
const agentStore = useAgentStore()
const quickEntryStore = useQuickEntryStore()

// 快捷入口列表数据
const quickEntryList = ref<QuickEntry[]>([])

/**
 * 加载快捷入口列表
 */
async function loadQuickEntries() {
  try {
    const response: ResponseData<{ entries: QuickEntry[] }> = await getQuickEntries('command')

    // 后端返回格式: {code: 200, data: {entries: [...]}, msg: "..."}
    if (response.code === 200 && response.data?.entries) {
      quickEntryList.value = response.data.entries
    } else {
      const errorMsg = response.msg || '获取快捷入口列表失败'
      console.error('获取快捷入口列表失败:', errorMsg)
      uni.showToast({
        title: errorMsg,
        icon: 'none'
      })
    }
  } catch (error) {
    const errorMessage = error instanceof Error ? error.message : '加载快捷入口列表失败'
    console.error('加载快捷入口列表失败:', error)
    uni.showToast({
      title: errorMessage,
      icon: 'none'
    })
  }
}

const emit = defineEmits<{
  click: [route: string]
}>()

/**
 * 处理点击事件，根据 action_type 跳转到相应页面
 */
function handleClick(entry: QuickEntry) {
  let route = ''

  // 根据 action_type 构建路由
  if (entry.action_type === 'agent') {
    // 设置选中的快捷指令到 store（自动保存到 storage）
    quickEntryStore.setActiveQuickEntry(entry)
    // 根据 agentId 从 API 获取智能体详情并设置到 store（自动保存到 storage）
    agentStore.setActiveAgentById(entry.action_value)
    // 跳转到 copywriting 页面，只传递 agentId
    route = `/pages/copywriting/index?agentId=${entry.action_value}`
  } else if (entry.action_type === 'skill') {
    // TODO: 跳转到 skill 页面
    route = ''
  } else if (entry.action_type === 'prompt') {
    // TODO: 处理 prompt 类型
    route = ''
  }

  if (route) {
    console.log('route', route)
    emit('click', route)
  }
}

// 组件挂载时加载数据
onMounted(() => {
  loadQuickEntries()
})
</script>

<style lang="scss" scoped>
@import '@/styles/_variables.scss';
@import '@/styles/_mixins.scss';

.quick-command-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: $spacing-md;
  margin-bottom: $spacing-lg;
  
  .command-card {
    @include card-style;
    padding: $spacing-md;
    display: flex;
    align-items: center;
    gap: 20rpx;
    transition: all $transition-base;
    
    &:active {
      transform: scale(0.98);
      background: $bg-light;
    }
    
    .command-icon-wrapper {
      :deep(.agent-icon) {
        box-shadow: 0 2rpx 8rpx rgba(0, 0, 0, 0.15);
      }
    }
    
    .command-content {
      display: flex;
      flex-direction: column;
      gap: 6rpx;
      flex: 1;
      min-width: 0;
      
      .command-title {
        font-size: $font-size-md;
        font-weight: 600;
        color: $text-main;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
      }
      
      .command-desc {
        font-size: $font-size-xs;
        color: $text-second;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        max-width: 240rpx; // 设置固定最大宽度，超出显示省略号
      }
    }
  }
}
</style>
