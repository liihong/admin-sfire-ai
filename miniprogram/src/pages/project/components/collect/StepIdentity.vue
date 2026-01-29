<template>
  <scroll-view class="step-content" scroll-y>
    <view class="step-wrapper">
      <TipCard title="设定身份" desc="为您的IP设定一个名称和所属行业，这是IP定位的基础信息" />
      
      <!-- 项目名称输入 -->
      <view class="form-section">
        <text class="form-label">项目名称</text>
        <input 
          class="form-input"
          :value="formData.name"
          @input="handleInput('name', $event)"
          placeholder="请输入项目名称"
          maxlength="20"
        />
      </view>
      
      <!-- 行业赛道选择 -->
      <view class="form-section">
        <FormPicker
          :model-value="formData.industry"
          @update:model-value="handleIndustryChange"
          label="行业赛道"
          :range="industryOptionsList"
          placeholder="请选择赛道"
        />
      </view>
      
      <!-- IP画像预览 -->
      <IPPreviewCard :data="previewData" />
    </view>
  </scroll-view>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import TipCard from './TipCard.vue'
import IPPreviewCard from '../IPPreviewCard.vue'
import FormPicker from '@/components/form/FormPicker.vue'
import type { DictOption } from '@/api/project'

interface PreviewData {
  name: string
  industry: string
  tone: string
  target_audience: string
  keywords: string[]
}

interface Props {
  formData: {
    name: string
    industry: string
  }
  industryOptions: DictOption[]
  previewData: PreviewData
}

const props = defineProps<Props>()

const emit = defineEmits<{
  'update:formData': [data: Partial<Props['formData']>]
}>()

// 将 DictOption[] 转换为字符串数组供 FormPicker 使用
const industryOptionsList = computed(() => {
  return props.industryOptions.map(item => item.value || item.label)
})

function handleInput(field: string, e: any) {
  emit('update:formData', { [field]: e.detail.value })
}

function handleIndustryChange(value: string | number) {
  emit('update:formData', { industry: String(value) })
}
</script>

<style lang="scss" scoped>
@import '@/styles/_variables.scss';

.step-content {
  height: 100%;
}

.step-wrapper {
  padding: $spacing-lg;
  padding-bottom: $spacing-xl;
}

.form-section {
  margin-bottom: $spacing-lg;
  
  .form-label {
    display: block;
    font-size: $font-size-md;
    color: $text-main;
    font-weight: 500;
    margin-bottom: $spacing-sm;
  }
  
  .form-input {
    width: 100%;
    height: 88rpx;
    background: $bg-light;
    border-radius: $radius-md;
    padding: 0 $spacing-md;
    font-size: $font-size-md;
    color: $text-main;
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

