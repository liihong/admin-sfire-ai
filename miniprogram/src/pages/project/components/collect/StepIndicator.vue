<template>
  <view class="step-indicator">
    <view 
      class="step-item"
      v-for="(step, index) in steps"
      :key="index"
      :class="{ 
        active: currentStep === index, 
        completed: currentStep > index 
      }"
    >
      <view class="step-dot">
        <text v-if="currentStep > index" class="step-check">✓</text>
        <view v-else-if="currentStep === index" class="step-icon-wrapper">
          <u-icon v-if="step.iconType === 'u-icon'" :name="step.icon" color="#FFFFFF" size="24"></u-icon>
          <SvgIcon v-else :name="step.icon" size="24" color="#FFFFFF" />
        </view>
        <text v-else class="step-number">{{ index + 1 }}</text>
      </view>
      <text class="step-label">{{ step.label }}</text>
    </view>
  </view>
</template>

<script setup lang="ts">
import SvgIcon from '@/components/base/SvgIcon.vue'

interface Step {
  label: string
  icon: string
  iconType?: 'u-icon' | 'svg-icon'
  key: string
}

interface Props {
  steps: Step[]
  currentStep: number
}

defineProps<Props>()
</script>

<style lang="scss" scoped>
@import '@/styles/_variables.scss';
@import '@/styles/_mixins.scss';

.step-indicator {
  display: flex;
  align-items: center;
  justify-content: space-around;
  padding: $spacing-md $spacing-lg;
  background: $white;
  border-bottom: 1rpx solid $border-color;
  box-shadow: $shadow-sm;
  
  .step-item {
    @include flex-column;
    align-items: center;
    gap: $spacing-xs;
    flex: 1;
    
    .step-dot {
      width: 56rpx;
      height: 56rpx;
      border-radius: $radius-circle;
      background: $border-color;
      @include flex-center;
      transition: all $transition-base;
      
      .step-number {
        font-size: $font-size-sm;
        color: $text-second;
        font-weight: 600;
      }
      
      .step-icon-wrapper {
        @include flex-center;
        
        :deep(.u-icon) {
          color: $white;
        }
      }
      
      .step-check {
        font-size: $font-size-md;
        color: $white;
        font-weight: 600;
      }
    }
    
    .step-label {
      font-size: $font-size-xs;
      color: $text-second;
      transition: all $transition-base;
    }
    
    &.active {
      .step-dot {
        background: $primary-orange;
        box-shadow: 0 4rpx 12rpx rgba($primary-orange, 0.3);
      }
      
      .step-label {
        color: $primary-orange;
        font-weight: 500;
      }
    }
    
    &.completed {
      .step-dot {
        background: $color-success;
        box-shadow: 0 4rpx 12rpx rgba($color-success, 0.3);
      }
      
      .step-label {
        color: $color-success;
        font-weight: 500;
      }
    }
  }
}
</style>

