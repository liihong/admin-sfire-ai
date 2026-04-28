<template>
  <view class="tip-card">
    <text class="tip-title">{{ title }}</text>
    <text class="tip-desc">{{ desc }}</text>
  </view>
</template>

<script setup lang="ts">
interface Props {
  title: string
  desc: string
}

defineProps<Props>()
</script>

<style lang="scss" scoped>
@import '@/styles/_variables.scss';

.tip-card {
  background: linear-gradient(135deg, rgba($primary-orange, 0.1) 0%, rgba($primary-orange, 0.05) 100%);
  border-radius: $radius-md;
  padding: $spacing-md;
  margin-bottom: $spacing-lg;
  
  .tip-title {
    display: block;
    font-size: $font-size-lg;
    font-weight: 600;
    color: $primary-orange;
    margin-bottom: $spacing-xs;
  }
  
  .tip-desc {
    display: block;
    font-size: $font-size-sm;
    color: $text-second;
    line-height: 1.6;
  }
}
</style>

