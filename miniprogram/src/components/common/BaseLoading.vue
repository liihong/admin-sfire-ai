<template>
  <view class="loading-overlay" v-if="visible">
    <view class="loading-spinner"></view>
    <text class="loading-text" v-if="text">{{ text }}</text>
  </view>
</template>

<script setup lang="ts">
interface Props {
  visible: boolean
  text?: string
}

withDefaults(defineProps<Props>(), {
  visible: false,
  text: '加载中...'
})
</script>

<style lang="scss" scoped>
@import '@/styles/_variables.scss';
@import '@/styles/_mixins.scss';
@import '@/styles/_animations.scss';

// 加载样式（从 _components.scss 复制，因为 scoped 无法使用全局类）
.loading-spinner {
  width: 60rpx;
  height: 60rpx;
  border: 4rpx solid $border-color;
  border-top-color: $primary-orange;
  border-radius: $radius-circle;
  animation: spin 0.8s linear infinite;
}

.loading-overlay {
  @include fixed-fullscreen;
  background: rgba(255, 255, 255, 0.9);
  backdrop-filter: blur(4px);
  z-index: $z-index-modal;
  @include flex-center;
  @include flex-column;
  gap: $spacing-md;
  
  .loading-text {
    font-size: $font-size-md;
    color: $text-second;
  }
}
</style>
