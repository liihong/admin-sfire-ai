<template>
  <view class="form-item">
    <text class="form-item__label" v-if="label">{{ label }}</text>
    <textarea
      class="form-item__textarea"
      :value="modelValue"
      :placeholder="placeholder"
      :disabled="disabled"
      :maxlength="maxlength"
      :auto-height="autoHeight"
      @input="handleInput"
      @blur="handleBlur"
      @focus="handleFocus"
    />
  </view>
</template>

<script setup lang="ts">
interface Props {
  modelValue?: string
  label?: string
  placeholder?: string
  disabled?: boolean
  maxlength?: number
  autoHeight?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  modelValue: '',
  label: '',
  placeholder: '',
  disabled: false,
  maxlength: -1,
  autoHeight: false
})

const emit = defineEmits<{
  'update:modelValue': [value: string]
  input: [value: string]
  blur: [event: any]
  focus: [event: any]
}>()

function handleInput(e: any) {
  const value = e.detail.value
  emit('update:modelValue', value)
  emit('input', value)
}

function handleBlur(e: any) {
  emit('blur', e)
}

function handleFocus(e: any) {
  emit('focus', e)
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
  
  &__textarea {
    width: 100%;
    min-height: 160rpx;
    background: $bg-light;
    border-radius: $radius-md;
    padding: $spacing-md $spacing-lg;
    font-size: $font-size-md;
    color: $text-main;
    line-height: 1.6;
    border: 2rpx solid transparent;
    box-sizing: border-box;
    
    &:focus {
      border-color: $primary-orange;
      background: $white;
    }
    
    &::placeholder {
      color: $text-placeholder;
    }
  }
}
</style>
