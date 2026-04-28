<template>
  <view class="progress-indicator">
    <view class="progress-text">{{ currentText }}</view>
    <view class="progress-bar">
      <view class="progress-bar-fill" :style="{ width: progress + '%' }"></view>
    </view>
  </view>
</template>

<script setup lang="ts">
interface Props {
  currentText: string  // 当前进度文本
  progress: number  // 进度百分比（0-100）
}

defineProps<Props>()
</script>

<style lang="scss" scoped>
@import '@/styles/_variables.scss';
@import '@/styles/_mixins.scss';

.progress-indicator {
  @include flex-column;
  gap: $spacing-sm;
  
  .progress-text {
    font-size: $font-size-md;
    color: $text-main;
    text-align: center;
  }
  
  .progress-bar {
    width: 100%;
    height: 8rpx;
    background: rgba($primary-orange, 0.1);
    border-radius: 4rpx;
    overflow: hidden;
    
    .progress-bar-fill {
      height: 100%;
      background: linear-gradient(90deg, $primary-orange 0%, $primary-orange-alt 100%);
      border-radius: 4rpx;
      transition: width 0.3s ease;
    }
  }
}
</style>

