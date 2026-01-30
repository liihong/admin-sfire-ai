<template>
  <scroll-view class="step-content" scroll-y>
    <view class="step-wrapper">
      <TipCard title="注入灵魂" desc="描述您的IP目标受众，让AI更好地理解您的IP定位" />
      
      <!-- 目标受众输入 -->
      <view class="form-section">
        <text class="form-label">目标受众 <text class="required-mark">*</text></text>
        <input 
          class="form-input"
          :value="formData.target_audience"
          @input="handleInput('target_audience', $event)"
          placeholder="例如：25-40岁关注健康的职场人群"
          maxlength="100"
        />
        <view class="form-tip">描述您的IP主要面向的用户群体，包括年龄、职业、兴趣等特征</view>
      </view>

    <!-- 目标人群痛点 -->
      <view class="form-section">
        <text class="form-label">目标人群痛点 <text class="required-mark">*</text></text>
        <input class="form-input" :value="formData.target_pains" @input="handleInput('target_pains', $event)"
          placeholder="例如：工作压力大，需要减压" maxlength="100" />
        <view class="form-tip">描述您的IP主要面向的用户群体，包括年龄、职业、兴趣等特征</view>
      </view>
      <!-- IP画像预览 -->
      <IPPreviewCard :data="previewData" />
    </view>
  </scroll-view>
</template>

<script setup lang="ts">
import TipCard from './TipCard.vue'
import IPPreviewCard from '../IPPreviewCard.vue'
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
  previewData: PreviewData
}

const props = defineProps<Props>()

const emit = defineEmits<{
  'update:formData': [data: Partial<Props['formData']>]
}>()

function handleInput(field: string, e: any) {
  emit('update:formData', { [field]: e.detail.value })
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
    
    .required-mark {
      color: $color-error;
    }
  }
  
  .form-tip {
    font-size: $font-size-xs;
    color: $text-second;
    margin-top: $spacing-xs;
    line-height: 1.5;
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

