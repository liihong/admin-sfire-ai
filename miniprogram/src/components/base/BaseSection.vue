<template>
 <view :class="['base-section', customClass]">
    <view class="base-section__header">
      <view class="base-section__header-left">
        <text class="base-section__title">
          <slot></slot>
        </text>
      </view>
     <view v-if="$slots.right" class="base-section__header-right">
        <slot name="right"></slot>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
interface Props {
  customClass?: string
}

withDefaults(defineProps<Props>(), {
  customClass: ''
})
</script>

<style lang="scss" scoped>
@import '@/styles/_variables.scss';

.base-section {
  padding: $spacing-sm 0 $spacing-sm;
  
  &__header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      margin-bottom: 24rpx;
  }
  
                                                                                                                                &__header-left {
                                                                                                                                  .base-section__title {
                                                                                                                                    font-size: $font-size-sm;
                                                                                                                                    font-weight: 700;
                                                                    color: $text-main;
                                                                    }
                                                                    }
                                
}
</style>
