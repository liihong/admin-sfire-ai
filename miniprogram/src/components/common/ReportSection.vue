<template>
  <view class="report-section">
    <view class="section-header">
      <text v-if="number" class="section-number">{{ number }}.</text>
      <text class="section-title">{{ title }}</text>
    </view>
    <view class="section-content">
      <slot></slot>
    </view>
  </view>
</template>

<script setup lang="ts">
interface Props {
  number?: string | number  // 章节编号
  title: string  // 章节标题
}

defineProps<Props>()
</script>

<style lang="scss" scoped>
@import '@/styles/_variables.scss';
@import '@/styles/_mixins.scss';

.report-section {
  @include card-style;
  
  .section-header {
    @include flex-center-vertical;
    gap: $spacing-sm;
    margin-bottom: $spacing-md;
    padding-bottom: $spacing-sm;
    border-bottom: 2rpx solid $border-color;
    
    .section-number {
      font-size: $font-size-lg;
      font-weight: 600;
      color: $primary-orange;
    }
    
    .section-title {
      font-size: $font-size-lg;
      font-weight: 600;
      color: $text-main;
    }
  }
  
  .section-content {
    @include flex-column;
    gap: $spacing-md;
  }
}
</style>

