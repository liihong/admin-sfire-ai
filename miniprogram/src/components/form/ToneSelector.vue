<template>
  <view class="form-item">
    <text class="form-item__label" v-if="label">{{ label }}</text>
    <view class="tone-options">
      <view
        v-for="tone in options"
        :key="tone"
        class="tone-tag"
        :class="{ selected: modelValue === tone }"
        @tap="handleSelect(tone)"
      >
        <text class="tag-text">{{ tone }}</text>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
interface Props {
  modelValue: string
  label?: string
  options: string[]
}

const props = withDefaults(defineProps<Props>(), {
  modelValue: '',
  label: '',
  options: () => []
})

const emit = defineEmits<{
  'update:modelValue': [value: string]
  change: [value: string]
}>()

function handleSelect(tone: string) {
  emit('update:modelValue', tone)
  emit('change', tone)
}
</script>

<style lang="scss" scoped>
@import '@/styles/_variables.scss';

.form-item {
  margin-bottom: $spacing-lg;
  
  &__label {
    font-size: $font-size-md;
    color: $text-main;
    margin-bottom: $spacing-sm;
    display: block;
    font-weight: 500;
  }
}

.tone-options {
  display: flex;
  flex-wrap: wrap;
  gap: $spacing-sm;
  
  .tone-tag {
    padding: 16rpx 24rpx;
    background: $bg-light;
    border-radius: 32rpx;
    border: 2rpx solid transparent;
    transition: all $transition-base;
    
    &.selected {
      background: linear-gradient(135deg, rgba($primary-orange, 0.1) 0%, rgba($primary-orange, 0.15) 100%);
      border-color: $primary-orange;
      
      .tag-text {
        color: $primary-orange;
        font-weight: 600;
      }
    }
    
    .tag-text {
      font-size: $font-size-md;
      color: $text-second;
    }
  }
}
</style>
