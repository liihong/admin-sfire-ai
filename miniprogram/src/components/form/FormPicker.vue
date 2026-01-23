<template>
  <view class="form-item">
    <text class="form-item__label" v-if="label">{{ label }}</text>
    <picker
      mode="selector"
      :range="range"
      :value="selectedIndex"
      @change="handleChange"
    >
      <view class="form-item__picker">
        <text class="picker-value" :class="{ 'picker-value--placeholder': !modelValue }">
          {{ displayValue || placeholder }}
        </text>
        <text class="picker-arrow">▼</text>
      </view>
    </picker>
  </view>
</template>

<script setup lang="ts">
import { computed } from 'vue'

interface Props {
  modelValue?: string | number
  label?: string
  placeholder?: string
  range: string[] | number[]
}

const props = withDefaults(defineProps<Props>(), {
  modelValue: '',
  label: '',
  placeholder: '请选择',
  range: () => []
})

const emit = defineEmits<{
  'update:modelValue': [value: string | number]
  change: [value: string | number]
}>()

const selectedIndex = computed(() => {
  if (typeof props.modelValue === 'number') {
    return props.modelValue >= 0 && props.modelValue < props.range.length ? props.modelValue : 0
  }
  const index = props.range.indexOf(props.modelValue)
  return index >= 0 ? index : 0
})

const displayValue = computed(() => {
  if (props.modelValue === '' || props.modelValue === null || props.modelValue === undefined) {
    return ''
  }
  if (typeof props.modelValue === 'number') {
    return props.range[props.modelValue]
  }
  return props.modelValue
})

function handleChange(e: any) {
  const index = e.detail.value
  const value = props.range[index]
  emit('update:modelValue', value)
  emit('change', value)
}
</script>

<style lang="scss" scoped>
@import '@/styles/_variables.scss';
@import '@/styles/_mixins.scss';

.form-item {
  margin-bottom: $spacing-lg;
  
  &__label {
    font-size: $font-size-md;
    color: $text-main;
    margin-bottom: $spacing-sm;
    display: block;
    font-weight: 500;
  }
  
  &__picker {
    @include input-base;
    display: flex;
    align-items: center;
    justify-content: space-between;
    
    .picker-value {
      font-size: $font-size-md;
      color: $text-main;
      
      &--placeholder {
        color: $text-placeholder;
      }
    }
    
    .picker-arrow {
      font-size: 20rpx;
      color: $text-second;
    }
  }
}
</style>
