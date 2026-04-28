<template>
  <view class="score-display">
    <view class="score-number-wrapper">
      <text class="score-number">{{ score }}</text>
      <text class="score-label">{{ label }}</text>
    </view>
    <view class="score-bar">
      <view class="score-bar-fill" :style="{ width: score + '%' }"></view>
    </view>
    <text v-if="reason" class="score-reason">{{ reason }}</text>
  </view>
</template>

<script setup lang="ts">
interface Props {
  score: number  // 评分（0-100）
  label?: string  // 评分标签，默认"分"
  reason?: string  // 评分理由
}

const props = withDefaults(defineProps<Props>(), {
  label: '分',
  reason: ''
})
</script>

<style lang="scss" scoped>
@import '@/styles/_variables.scss';
@import '@/styles/_mixins.scss';

.score-display {
  @include flex-column;
  align-items: center;
  gap: $spacing-md;
  background: linear-gradient(135deg, rgba($primary-orange, 0.1) 0%, rgba($primary-orange, 0.05) 100%);
  border-radius: $radius-lg;
  padding: $spacing-lg;
  
  .score-number-wrapper {
    @include flex-center;
    gap: $spacing-xs;
    
    .score-number {
      font-size: 72rpx;
      font-weight: 700;
      color: $primary-orange;
      line-height: 1;
    }
    
    .score-label {
      font-size: $font-size-lg;
      color: $text-second;
      margin-top: 8rpx;
    }
  }
  
  .score-bar {
    width: 100%;
    height: 12rpx;
    background: rgba($primary-orange, 0.1);
    border-radius: 6rpx;
    overflow: hidden;
    
    .score-bar-fill {
      height: 100%;
      background: linear-gradient(90deg, $primary-orange 0%, $primary-orange-alt 100%);
      border-radius: 6rpx;
      transition: width 0.5s ease;
    }
  }
  
  .score-reason {
    font-size: $font-size-sm;
    color: $text-second;
    line-height: 1.6;
    text-align: center;
  }
}
</style>

