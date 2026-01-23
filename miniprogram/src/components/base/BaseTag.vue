<template>
  <view :class="['base-tag', `base-tag--${variant}`, `base-tag--${size}`, customClass]">
    <slot></slot>
  </view>
</template>

<script setup lang="ts">
interface Props {
  variant?: 'default' | 'primary' | 'success' | 'warning' | 'error'
  size?: 'small' | 'medium' | 'large'
  customClass?: string
}

withDefaults(defineProps<Props>(), {
  variant: 'default',
  size: 'medium',
  customClass: ''
})
</script>

<style lang="scss" scoped>
@import '@/styles/_variables.scss';

.base-tag {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: $radius-md;
  padding: 8rpx 16rpx;
  font-size: $font-size-sm;
  font-weight: 500;
  
  &--small {
    padding: 4rpx 12rpx;
    font-size: $font-size-xs;
  }
  
  &--medium {
    padding: 8rpx 16rpx;
    font-size: $font-size-sm;
  }
  
  &--large {
    padding: 12rpx 24rpx;
    font-size: $font-size-md;
  }
  
  &--default {
    background: $bg-light;
    color: $text-second;
  }
  
  &--primary {
    background: rgba($primary-orange, 0.1);
    color: $primary-orange;
  }
  
  &--success {
    background: rgba($color-success, 0.1);
    color: $color-success;
  }
  
  &--warning {
    background: rgba($color-warning, 0.1);
    color: $color-warning;
  }
  
  &--error {
    background: rgba($color-error, 0.1);
    color: $color-error;
  }
}
</style>
