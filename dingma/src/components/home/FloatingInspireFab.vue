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
    background: linear-gradient(135deg, $primary-orange 0%, $primary-orange-alt 100%);
    box-shadow: 0 12rpx 32rpx rgba($primary-orange, 0.45);
    display: flex;
    align-items: center;
    justify-content: center;
    transition: transform $transition-base;

    &:active {
      transform: scale(0.92);
    }
  }
}
</style>
