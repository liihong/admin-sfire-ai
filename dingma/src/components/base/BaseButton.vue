<template>
  <u-button
    :type="uviewType"
    :size="size"
    :plain="variant === 'outline'"
    :custom-style="mergedStyle"
    :class="['base-button', `base-button--${variant}`, customClass]"
    v-bind="$attrs"
  >
    <slot></slot>
  </u-button>
</template>

<script setup lang="ts">
import { computed } from 'vue'

interface Props {
  variant?: 'primary' | 'outline' | 'text'
  size?: 'small' | 'normal' | 'large'
  customClass?: string
  customStyle?: Record<string, any>
}

const props = withDefaults(defineProps<Props>(), {
  variant: 'primary',
  size: 'normal',
  customClass: '',
  customStyle: () => ({})
})

// 将 variant 映射到 uview-plus 的 type
const uviewType = computed(() => {
  if (props.variant === 'outline' || props.variant === 'text') {
    return 'primary'
  }
  return 'primary'
})

// 合并自定义样式
const mergedStyle = computed(() => {
  const baseStyle: Record<string, any> = {}
  
  if (props.variant === 'primary') {
    baseStyle.background = 'linear-gradient(135deg, #FF7700 0%, #F37021 100%)'
    baseStyle.borderRadius = '16rpx'
  }
  
  return { ...baseStyle, ...props.customStyle }
})
</script>

<style lang="scss" scoped>
@import '@/styles/_variables.scss';

.base-button {
  &--outline {
    background: transparent !important;
    border: 2rpx solid $primary-orange !important;
    color: $primary-orange !important;
  }
  
  &--text {
    background: transparent !important;
    border: none !important;
    color: $primary-orange !important;
  }
}
</style>
