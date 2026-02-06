<template>
  <view class="top-bar">
   <view class="user-info-left" @tap="handleSwitchIP" v-if="projectName">
      <view class="user-dot"></view>
      <text class="user-name">{{ projectName || userName || '创作者' }}</text>
     <SvgIcon name="qiehuan" :size="35" />
    </view>
    <!-- <view class="user-info-right">
      <view class="points-icon">💎</view>
      <text class="user-points">{{ userPoints || 1280 }} 点数</text>
    </view> -->
  </view>
</template>

<script setup lang="ts">
import SvgIcon from '@/components/base/SvgIcon.vue'

interface Props {
  projectName?: string
  userName?: string
  userPoints?: number
}

withDefaults(defineProps<Props>(), {
  projectName: '',
  userName: '',
  userPoints: 1280
})

// Emits
const emit = defineEmits<{
  'switch-project': []
}>()

/**
 * 处理IP切换
 * 触发切换项目事件，由父组件处理
 */
function handleSwitchIP() {
  emit('switch-project')
}
</script>

<style lang="scss" scoped>
@import '@/styles/_variables.scss';

.top-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 24rpx 32rpx 20rpx;
  background: $white;
  position: relative;
  z-index: 10;
  box-shadow: 0 2rpx 12rpx rgba(0, 0, 0, 0.04);
  
  .user-info-left {
    display: flex;
    align-items: center;
    gap: 12rpx;
    
    .user-dot {
      width: 10rpx;
      height: 10rpx;
      border-radius: 50%;
      background: linear-gradient(135deg, $primary-orange 0%, $primary-orange-alt 100%);
      box-shadow: 0 0 8rpx rgba($primary-orange, 0.4);
      animation: pulse 2s ease-in-out infinite;
    }
    
    .user-name {
      font-size: $font-size-lg;
      font-weight: 600;
      color: $text-main;
      letter-spacing: -0.5rpx;
    }
    
    // IP切换按钮
    .switch-btn {
      width: 48rpx;
      height: 48rpx;
      display: flex;
      align-items: center;
      justify-content: center;
      background: linear-gradient(135deg, rgba($primary-orange, 0.1) 0%, rgba($primary-orange, 0.15) 100%);
      border-radius: 50%;
      margin-left: 8rpx;
      transition: all 0.2s ease;
      
      &:active {
        transform: scale(0.95);
        background: linear-gradient(135deg, rgba($primary-orange, 0.2) 0%, rgba($primary-orange, 0.25) 100%);
      }
      
      .switch-icon {
        font-size: 28rpx;
        opacity: 0.8;
      }
    }
  }
  
  .user-info-right {
    display: flex;
    align-items: center;
    gap: 8rpx;
    padding: 10rpx 20rpx;
    background: linear-gradient(135deg, $bg-light 0%, #F1F3F5 100%);
    border-radius: 24rpx;
    border: 1rpx solid rgba(0, 0, 0, 0.05);
    
    .points-icon {
      font-size: $font-size-sm;
      opacity: 0.8;
    }
    
    .user-points {
      font-size: $font-size-sm;
      color: $text-second;
      font-weight: 500;
    }
  }
}
</style>
