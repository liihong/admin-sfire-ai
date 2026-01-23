<template>
  <view class="top-bar">
    <view class="user-info-left">
      <view class="user-dot"></view>
      <text class="user-name">{{ projectName || userName || '创作者' }}</text>
    </view>
    <view class="user-info-right">
      <view class="points-icon">💎</view>
      <text class="user-points">{{ userPoints || 1280 }} 点数</text>
    </view>
  </view>
</template>

<script setup lang="ts">
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
