<template>
  <view class="recent-landing">
    <view class="landing-header">
      <text class="section-title">最近落地</text>
    </view>
  </view>
</template>

<script setup lang="ts">
</script>

<style scoped lang="scss">
@import '@/styles/_variables.scss';

.recent-landing {
  padding: 0 $spacing-md;
  margin-bottom: $spacing-md;

  .landing-header {
    margin-bottom: $spacing-md;

    .section-title {
      font-size: $font-size-sm;
      font-weight: 700;
      color: $text-main;
    }
  }
}
</style>
