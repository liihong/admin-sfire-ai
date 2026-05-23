<template>
  <view class="inspire-fab" :style="fabStyle" @tap="$emit('click')">
    <view class="inspire-fab__btn">
      <SvgIcon name="linggan" :size="44" color="#FFFFFF" />
    </view>
  </view>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import SvgIcon from '@/components/base/SvgIcon.vue'

interface Props {
  bottom?: number
  right?: number
}

const props = withDefaults(defineProps<Props>(), {
  bottom: 180,
  right: 32
})

defineEmits<{
  click: []
}>()

const fabStyle = computed(() => ({
  bottom: `${props.bottom}rpx`,
  right: `${props.right}rpx`
}))
</script>

<style lang="scss" scoped>
@import '@/styles/_variables.scss';

.inspire-fab {
  position: fixed;
  z-index: $z-index-fixed;

  &__btn {
    width: 104rpx;
    height: 104rpx;
    border-radius: 52rpx;
    background: linear-gradient(135deg, $accent-gold 0%, #b45309 100%);
    box-shadow: 0 16rpx 40rpx rgba(217, 75, 54, 0.28);
    display: flex;
    align-items: center;
    justify-content: center;
    transition: transform $transition-base;
    /* 持续微微「呼吸发光」，吸引注意但不刺眼 */
    animation: inspire-fab-glow 2.6s ease-in-out infinite;

    &:active {
      transform: scale(0.92);
      animation: none;
    }
  }
}

@keyframes inspire-fab-glow {
  0%,
  100% {
    box-shadow:
      0 16rpx 40rpx rgba(217, 75, 54, 0.26),
      0 0 0 0 rgba(217, 75, 54, 0.25);
  }
  50% {
    box-shadow:
      0 18rpx 52rpx rgba(217, 75, 54, 0.38),
      0 0 28rpx 6rpx rgba(217, 75, 54, 0.35);
  }
}
</style>
