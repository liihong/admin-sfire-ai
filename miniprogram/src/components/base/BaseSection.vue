<template>
  <view :class="['base-section', { 'base-section--accent': accent }, customClass]">
    <text :class="['base-section__title', { 'base-section__title--accent': accent }]">
      <slot></slot>
    </text>
  </view>
</template>

<script setup lang="ts">
interface Props {
  accent?: boolean
  customClass?: string
}

withDefaults(defineProps<Props>(), {
  accent: false,
  customClass: ''
})
</script>

<style lang="scss" scoped>
@import '@/styles/_variables.scss';

.base-section {
  padding: $spacing-lg 0 $spacing-sm;
  
  &--accent {
    padding: $spacing-lg 0 $spacing-md;
  }
  
  &__title {
    font-size: $font-size-md;
    font-weight: 900;
    color: $text-second;
    
    &--accent {
      font-size: $font-size-lg;
      font-weight: 700;
      background: linear-gradient(135deg, $primary-orange 0%, $primary-orange-alt 100%);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      background-clip: text;
    }
  }
}
</style>
