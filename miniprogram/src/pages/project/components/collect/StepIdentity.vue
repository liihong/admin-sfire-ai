<template>
  <scroll-view class="step-content" scroll-y>
    <view class="step-wrapper">
     <TipCard title="设定身份" desc="请您尽可能详细的填写该问卷，这将帮助AI更好地理解您的IP，从而生成更符合您需求的内容" />
      
      <!-- 项目名称输入 -->
      <view class="form-section">
       <text class="form-label">IP名称</text>
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
      
<!-- 行业理解 -->
      <view class="form-section">
        <text class="form-label">你对这个行业的理解</text>
        <input class="form-input" :value="formData.industry_understanding"
          @input="handleInput('industry_understanding', $event)" placeholder="请输入你对这个行业的理解" maxlength="200" />
      </view>

      <!-- 对行业不同的看法 -->
      <view class="form-section">
        <text class="form-label">对行业不同的看法</text>
        <input class="form-input" :value="formData.unique_views" @input="handleInput('unique_views', $event)"
          placeholder="请输入你对行业不同的看法" maxlength="200" />
      </view>
    </view>
  </scroll-view>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import TipCard from './TipCard.vue'
import IPPreviewCard from '../IPPreviewCard.vue'
import FormPicker from '@/components/form/FormPicker.vue'
import type { DictOption } from '@/api/project'
import type { ProjectFormData } from '@/types/project'

interface PreviewData {
  name: string
  industry: string
  tone: string
  target_audience: string
  keywords: string[]
}

interface Props {
  formData: ProjectFormData
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

