<template>
  <view class="feature-grid">
    <view
      class="feature-item"
v-for="(item, index) in displayFeatureList"
      :key="index"
      @tap="handleFeatureClick(item)"
    >
      <view class="feature-icon-wrapper">
        <u-icon :name="item.icon" color="#FF8800" :size="item.iconSize || 48" />
      </view>
      <text class="feature-label">{{ item.label }}</text>
    </view>
  </view>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { FeaturedModuleItem } from '@/api/home'
import { useAgentStore } from '@/stores/agent'

export interface FeatureItem {
  icon: string
  label: string
  route?: string
  iconSize?: number
}

interface Props {
  featureList?: FeaturedModuleItem[]
}

// 默认功能列表（当没有从数据库获取到数据时使用）
// 全能对话使用 aichat 页面，不传 IP 信息，直接与智能体对话
const defaultFeatureList: FeatureItem[] = [
  { icon: 'edit-pen', label: '脚本洗稿', route: '/pages/aichat/index?agentId=1', iconSize: 20 },
  { icon: 'folder', label: '图文封面', route: '/pages/aichat/index?agentId=1', iconSize: 20 },
  { icon: 'star', label: '爆款标题', route: '/pages/aichat/index?agentId=1', iconSize: 20 },
  { icon: 'chat', label: '全能对话', route: '/pages/aichat/index?agentId=1', iconSize: 20 }
]

const props = withDefaults(defineProps<Props>(), {
  featureList: () => []
})

// 使用传入的数据，如果没有则使用默认数据
const displayFeatureList = computed(() => {
  return props.featureList && props.featureList.length > 0
    ? props.featureList
    : defaultFeatureList
})

const emit = defineEmits<{
  featureClick: [item: FeatureItem]
}>()

const agentStore = useAgentStore()

const handleFeatureClick = (item: FeaturedModuleItem | FeatureItem) => {
  emit('featureClick', item)
  if (item.route) {
    // 如果入口路由带有 agentId，则把 label 写入 active_agent_info
    // 这样对话页标题可以优先展示 label，而不是落回默认值
    const match = /[?&]agentId=([^&]+)/.exec(item.route)
    if (match) {
      const agentId = decodeURIComponent(match[1])
      agentStore.setActiveAgent(
        {
          id: agentId,
          name: item.label,
          label: item.label,
          icon: '',
          description: ''
        },
        { persist: true }
      )
    }
    uni.navigateTo({ url: item.route })
  }
}
</script>

<style scoped lang="scss">
@import '@/styles/_variables.scss';

.feature-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 24rpx;
  padding: 32rpx 24rpx;
  background: $white;
  margin-bottom: $spacing-md;
  margin-left: $spacing-md;
  margin-right: $spacing-md;
  border-radius: $radius-md;

  .feature-item {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 12rpx;

    .feature-icon-wrapper {
      width: 96rpx;
      height: 96rpx;
      border-radius: 16rpx;
      background: rgba(255, 136, 0, 0.06);
      display: flex;
      align-items: center;
      justify-content: center;
      border: 2rpx solid rgba(255, 136, 0, 0.15);
      margin-bottom: 8rpx;
    }

    .feature-label {
      font-size: 24rpx;
      color: $text-main;
      text-align: center;
      font-weight: 400;
    }
  }
}
</style>
