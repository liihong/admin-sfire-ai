<template>
  <view class="notification-bar" @tap="handleClick">
    <view class="notification-left">
      <!-- <u-icon name="flash" color="#FF8800" size="32" /> -->
     <SvgIcon name="agent" size="32" color="#FF8800" />
      <text class="notification-label">智能体动态</text>
      <view class="divider"></view>
    </view>
    <view class="notification-content">
      <text class="notification-text">{{ notificationText }}</text>
    </view>
    <u-icon name="arrow-right" color="#C9CDD4" size="20" />
  </view>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import SvgIcon from '@/components/base/SvgIcon.vue'

const notificationText = ref('火源 AI 算力节点已完成扩容')

const handleClick = () => {
  console.log('点击通知栏')
}
</script>

<style scoped lang="scss">
@import '@/styles/_variables.scss';

.notification-bar {
  display: flex;
  align-items: center;
  padding: 24rpx 32rpx;
  background: $white;
  margin-bottom: $spacing-md;
  margin-left: $spacing-md;
  margin-right: $spacing-md;
  border-radius: $radius-md;

  .notification-left {
    display: flex;
    align-items: center;
    margin-right: 16rpx;
    gap: 8rpx;

    .notification-label {
      font-size: 24rpx;
      font-weight: 600;
      color: $brand-orange;
    }

    .divider {
      width: 2rpx;
      height: 32rpx;
      background: #E4E7ED;
      margin-left: 16rpx;
      margin-right: 16rpx;
    }
  }

  .notification-content {
    flex: 1;
    overflow: hidden;

    .notification-text {
      font-size: 24rpx;
      color: $text-second;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }
  }
}
</style>
