<template>
  <view :class="['base-grid', `base-grid--${columns}`, customClass]" :style="gridStyle">
    <slot></slot>
  </view>
</template>

<script setup lang="ts">
import { computed } from 'vue'

interface Props {
  columns?: 2 | 3 | 4 | 5
  gap?: number
  customClass?: string
}

const props = withDefaults(defineProps<Props>(), {
  columns: 2,
  gap: 16,
  customClass: ''
})

const gridStyle = computed(() => ({
  gap: `${props.gap}rpx`
}))
</script>

<style lang="scss" scoped>
.base-grid {
  display: grid;
  
  &--2 {
    grid-template-columns: repeat(2, 1fr);
  }
  
  &--3 {
    grid-template-columns: repeat(3, 1fr);
  }
  
  &--4 {
    grid-template-columns: repeat(4, 1fr);
  }
  
  &--5 {
    grid-template-columns: repeat(5, 1fr);
  }
}
</style>
