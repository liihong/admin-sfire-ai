<template>
  <view class="form-item">
    <text class="form-item__label" v-if="label">{{ label }}</text>
    <view class="tag-input-wrapper" :class="{ 'tag-input-wrapper--taboo': variant === 'taboo' }">
      <view
        v-for="(tag, idx) in tags"
        :key="idx"
        class="tag-item"
        :class="{ 'tag-item--taboo': variant === 'taboo' }"
      >
        <text class="tag-text">{{ tag }}</text>
        <text class="tag-remove" @tap="handleRemove(idx)">×</text>
      </view>
      <input
        class="tag-input"
        v-model="inputValue"
        :placeholder="placeholder"
        @confirm="handleAdd"
        @blur="handleAdd"
      />
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'

interface Props {
  modelValue: string[]
  label?: string
  placeholder?: string
  variant?: 'default' | 'taboo'
}

const props = withDefaults(defineProps<Props>(), {
  modelValue: () => [],
  label: '',
  placeholder: '+ 添加',
  variant: 'default'
})

const emit = defineEmits<{
  'update:modelValue': [value: string[]]
  change: [value: string[]]
}>()

const tags = ref<string[]>([...props.modelValue])
const inputValue = ref('')

watch(() => props.modelValue, (newVal) => {
  tags.value = [...newVal]
}, { deep: true })

function handleAdd() {
  const value = inputValue.value.trim()
  if (value && !tags.value.includes(value)) {
    const newTags = [...tags.value, value]
    tags.value = newTags
    inputValue.value = ''
    emit('update:modelValue', newTags)
    emit('change', newTags)
  } else {
    inputValue.value = ''
  }
}

function handleRemove(index: number) {
  const newTags = tags.value.filter((_, i) => i !== index)
  tags.value = newTags
  emit('update:modelValue', newTags)
  emit('change', newTags)
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

.tag-input-wrapper {
  display: flex;
  flex-wrap: wrap;
  gap: $spacing-sm;
  padding: $spacing-sm;
  background: $bg-light;
  border-radius: $radius-md;
  min-height: 100rpx;
  
  &--taboo {
    background: rgba($color-error, 0.05);
  }
  
  .tag-item {
    display: flex;
    align-items: center;
    gap: 8rpx;
    padding: 12rpx 20rpx;
    background: linear-gradient(135deg, rgba($color-info, 0.1) 0%, rgba($color-info, 0.15) 100%);
    border-radius: 24rpx;
    
    &--taboo {
      background: linear-gradient(135deg, rgba($color-error, 0.1) 0%, rgba($color-error, 0.15) 100%);
      
      .tag-text {
        color: $color-error;
      }
      
      .tag-remove {
        color: $color-error;
      }
    }
    
    .tag-text {
      font-size: $font-size-sm;
      color: $color-info;
    }
    
    .tag-remove {
      font-size: $font-size-md;
      color: $color-info;
      line-height: 1;
      cursor: pointer;
    }
  }
  
  .tag-input {
    flex: 1;
    min-width: 200rpx;
    height: 56rpx;
    font-size: $font-size-md;
    color: $text-main;
    background: transparent;
    border: none;
  }
}
</style>
