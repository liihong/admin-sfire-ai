<template>
  <u-input
    :value="modelValue"
    :placeholder="placeholder"
    :type="type"
    :disabled="disabled"
    :maxlength="maxlength"
    :custom-style="inputStyle"
    :class="['base-input', customClass]"
    @input="handleInput"
    @blur="handleBlur"
    @focus="handleFocus"
    v-bind="$attrs"
  />
</template>

<script setup lang="ts">
import { computed } from 'vue'

interface Props {
  modelValue?: string | number
  placeholder?: string
  type?: 'text' | 'number' | 'idcard' | 'digit' | 'password'
  disabled?: boolean
  maxlength?: number
  customClass?: string
}

const props = withDefaults(defineProps<Props>(), {
  modelValue: '',
  placeholder: '',
  type: 'text',
  disabled: false,
  maxlength: -1,
  customClass: ''
})

const emit = defineEmits<{
  'update:modelValue': [value: string | number]
  input: [value: string | number]
  blur: [event: any]
  focus: [event: any]
}>()

const inputStyle = computed(() => ({
  height: '88rpx',
  background: '#F5F7FA',
  borderRadius: '16rpx',
  padding: '0 24rpx',
  fontSize: '28rpx'
}))

function handleInput(value: string | number) {
  emit('update:modelValue', value)
  emit('input', value)
}

function handleBlur(event: any) {
  emit('blur', event)
}

function handleFocus(event: any) {
  emit('focus', event)
}
</script>

<style lang="scss" scoped>
@import '@/styles/_variables.scss';
@import '@/styles/_mixins.scss';

.base-input {
  @include input-base;
}
</style>
