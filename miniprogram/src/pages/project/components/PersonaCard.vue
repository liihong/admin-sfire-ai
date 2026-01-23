<template>
  <view class="persona-card" @tap="$emit('click')">
    <view class="persona-card-content">
      <view class="persona-left">
        <view class="persona-icon-wrapper">
          <view class="icon-circle">
            <AgentIcon iconName="Star" :size="48" />
          </view>
          <view class="active-dot"></view>
        </view>
        <view class="persona-info">
          <text class="persona-label">当前活跃人设</text>
          <text class="persona-name">{{ projectName || '选择人设' }}</text>
          <text class="persona-desc">{{ tone }}·智囊型</text>
        </view>
      </view>
      <view class="persona-toggle">
        <u-icon name="setting" color="#6C757D" size="22"></u-icon>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { AgentIcon } from '@/components/base'
import { DEFAULT_PERSONA_SETTINGS } from '@/stores/project'

interface Props {
  projectName?: string
  tone?: string
}

withDefaults(defineProps<Props>(), {
  projectName: '',
  tone: DEFAULT_PERSONA_SETTINGS.tone
})

defineEmits<{
  click: []
}>()
</script>

<style lang="scss" scoped>
@import '@/styles/_variables.scss';

.persona-card {
  background: $white;
  border-radius: $radius-lg;
  padding: $spacing-lg;
  margin-bottom: $spacing-lg;
  box-shadow: 0 4rpx 20rpx rgba(0, 0, 0, 0.06), 0 1rpx 3rpx rgba(0, 0, 0, 0.04);
  transition: all $transition-slow cubic-bezier(0.4, 0, 0.2, 1);
  border: 1rpx solid rgba(0, 0, 0, 0.04);
  
  &:active {
    transform: scale(0.98);
    box-shadow: 0 2rpx 12rpx rgba(0, 0, 0, 0.08), 0 1rpx 2rpx rgba(0, 0, 0, 0.06);
  }
  
  .persona-card-content {
    display: flex;
    align-items: center;
    justify-content: space-between;
  }
  
  .persona-left {
    display: flex;
    align-items: center;
    gap: 20rpx;
    
    .persona-icon-wrapper {
      position: relative;
      display: flex;
      align-items: center;
      justify-content: center;
      
      .icon-circle {
        width: 96rpx;
        height: 96rpx;
        border-radius: 50%;
        background: linear-gradient(135deg, #F0F4FF 0%, #E8F0FE 100%);
        display: flex;
        align-items: center;
        justify-content: center;
        border: 2rpx solid rgba(59, 130, 246, 0.1);
        box-shadow: 0 4rpx 16rpx rgba(59, 130, 246, 0.08), inset 0 1rpx 0 rgba(255, 255, 255, 0.8);
        position: relative;
        
        :deep(.agent-icon) {
          filter: drop-shadow(0 2rpx 8rpx rgba(59, 130, 246, 0.2));
        }
      }
      
      .active-dot {
        position: absolute;
        top: -2rpx;
        right: -2rpx;
        width: 20rpx;
        height: 20rpx;
        background: linear-gradient(135deg, $color-success 0%, #34D399 100%);
        border-radius: 50%;
        border: 3rpx solid $white;
        box-shadow: 0 0 12rpx rgba($color-success, 0.5), 0 2rpx 8rpx rgba(0, 0, 0, 0.15);
        animation: pulse-dot 2s ease-in-out infinite;
      }
    }
    
    .persona-info {
      display: flex;
      flex-direction: column;
      gap: 8rpx;
      
      .persona-label {
        font-size: $font-size-sm;
        color: #94A3B8;
        font-weight: 400;
      }
      
      .persona-name {
        font-size: $font-size-xl;
        font-weight: 700;
        color: $text-main;
        line-height: 1.2;
        letter-spacing: -0.5rpx;
      }
      
      .persona-desc {
        font-size: $font-size-md;
        color: $text-second;
        line-height: 1.2;
      }
    }
  }
  
  .persona-toggle {
    width: 48rpx;
    height: 48rpx;
    display: flex;
    align-items: center;
    justify-content: center;
  }
}
</style>
