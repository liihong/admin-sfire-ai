<template>
  <view :class="['base-card', `base-card--${variant}`, customClass]">
    <slot></slot>
  </view>
</template>

<script setup lang="ts">
interface Props {
  variant?: 'default' | 'outline' | 'flat'
  customClass?: string
}

withDefaults(defineProps<Props>(), {
  variant: 'default',
  customClass: ''
})
</script>

<style lang="scss" scoped>
@import '@/styles/_variables.scss';
@import '@/styles/_mixins.scss';

.base-card {
  @include card-style;
  
  &--outline {
    background: transparent;
    border: 1rpx solid $border-color;
    box-shadow: none;
  }
  
  &--flat {
    @include card-flat;
  }
}
</style>
