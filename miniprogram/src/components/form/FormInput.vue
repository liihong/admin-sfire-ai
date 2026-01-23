<template>
  <view class="form-item">
    <text class="form-item__label" v-if="label">{{ label }}</text>
    <input
      class="form-item__input"
      :value="modelValue"
      :placeholder="placeholder"
      :type="type"
      :disabled="disabled"
      :maxlength="maxlength"
      @input="handleInput"
      @blur="handleBlur"
      @focus="handleFocus"
    />
  </view>
</template>

<script setup lang="ts">
interface Props {
  modelValue?: string | number
  label?: string
  placeholder?: string
  type?: string
  disabled?: boolean
  maxlength?: number
}

const props = withDefaults(defineProps<Props>(), {
  modelValue: '',
  label: '',
  placeholder: '',
  type: 'text',
  disabled: false,
  maxlength: -1
})

const emit = defineEmits<{
  'update:modelValue': [value: string | number]
  input: [value: string | number]
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
  
  &__input {
    @include input-base;
  }
}
</style>
