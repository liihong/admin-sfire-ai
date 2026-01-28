<template>
  <view class="feature-grid">
    <view
      class="feature-item"
      v-for="(item, index) in featureList"
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
export interface FeatureItem {
  icon: string
  label: string
  route?: string
  iconSize?: number
}

interface Props {
  featureList?: FeatureItem[]
}

const props = withDefaults(defineProps<Props>(), {
  featureList: () => [
    { icon: 'edit-pen', label: '脚本洗稿', route: '/pages/copywriting/index', iconSize: 20 },
    { icon: 'folder', label: '图文封面', route: '/pages/cover/index', iconSize: 20 },
    { icon: 'star', label: '爆款标题', route: '/pages/title/index', iconSize: 20 },
    { icon: 'chat', label: '全能对话', route: '/pages/chat/index', iconSize: 20 }
  ]
})

const emit = defineEmits<{
  featureClick: [item: FeatureItem]
}>()

const handleFeatureClick = (item: FeatureItem) => {
  emit('featureClick', item)
  if (item.route) {
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
