<template>
  <view class="fab-container" :style="fabStyle" @tap="$emit('click')">
    <view class="fab-button">
      <u-icon name="edit-pen" color="#FFFFFF" size="24"></u-icon>
    </view>
  </view>
</template>

<script setup lang="ts">
import { computed } from 'vue'

interface Props {
  bottom?: number // 距离底部距离（rpx）
  right?: number // 距离右侧距离（rpx）
}

const props = withDefaults(defineProps<Props>(), {
  bottom: 140,
  right: 32
})

defineEmits<{
  click: []
}>()

const fabStyle = computed(() => {
  return {
    bottom: `${props.bottom}rpx`,
    right: `${props.right}rpx`
  }
})
</script>

<style lang="scss" scoped>
@import '@/styles/_variables.scss';

.fab-container {
  position: fixed;
  z-index: $z-index-fixed;
  
  .fab-button {
    width: 96rpx;
    height: 96rpx;
    border-radius: 48rpx;
    background: linear-gradient(135deg, $primary-orange 0%, $primary-orange-alt 100%);
    box-shadow: 0 8rpx 24rpx rgba($primary-orange, 0.4);
    display: flex;
    align-items: center;
    justify-content: center;
    transition: all $transition-base;
    
    &:active {
      transform: scale(0.92);
      box-shadow: 0 4rpx 16rpx rgba($primary-orange, 0.4);
    }
  }
}
</style>


