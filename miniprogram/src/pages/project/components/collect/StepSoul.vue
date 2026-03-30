<template>
  <scroll-view class="step-content" scroll-y>
    <view class="step-wrapper">
     <view class="step-header">
        <text class="step-desc">描述产品、人群与优势，帮助 AI 理解您的变现逻辑</text>
      </view>
      <view class="form-card">
        <view class="form-section">
          <text class="form-label">主要产品/服务 <text class="required-mark">*</text></text>
          <input class="form-input" :value="formData.cl_mainProducts" placeholder="例如：麻将馄饨，手工香皂等" maxlength="200"
            @input="handleInput('cl_mainProducts', $event)" />
        </view>


      <view class="form-section">
         <text class="form-label">目标人群 <text class="required-mark">*</text></text>
         <textarea class="form-textarea" :value="formData.cl_targetPopulation" placeholder="例：想变美变瘦的20-40岁女性"
            maxlength="500" :auto-height="true" :adjust-position="true" :cursor-spacing="20" :show-confirm-bar="false"
            @input="handleInput('cl_targetPopulation', $event)" />
        </view>

      <view class="form-section">
         <text class="form-label">目标人群痛点 <text class="required-mark">*</text></text>
         <textarea class="form-textarea" :value="formData.cl_painPoints" placeholder="例：没时间做早餐，工作忙没时间健身..."
            maxlength="500" :auto-height="true" :adjust-position="true" :cursor-spacing="20" :show-confirm-bar="false"
            @input="handleInput('cl_painPoints', $event)" />
        </view>
       <view class="form-section">
          <text class="form-label">产品优势</text>
          <textarea class="form-textarea" :value="formData.cl_advantages" placeholder="描述原材料、工艺或价格优势" maxlength="500"
            :auto-height="true" :adjust-position="true" :cursor-spacing="20" :show-confirm-bar="false"
            @input="handleInput('cl_advantages', $event)" />
        </view>

        <view class="form-section">
          <text class="form-label">客户反馈</text>
          <textarea class="form-textarea" :value="formData.cl_feedback" placeholder="例如：孩子每天都盼着吃我的早餐..." maxlength="500"
            :auto-height="true" :adjust-position="true" :cursor-spacing="20" :show-confirm-bar="false"
            @input="handleInput('cl_feedback', $event)" />
        </view>
      </view>
    </view>
  </scroll-view>
</template>

<script setup lang="ts">
import type { ProjectFormData } from '@/types/project'

interface PreviewData {
  name: string
  industry: string
  style_tones: string
  cl_targetPopulation: string
  keywords: string[]
}

interface Props {
  formData: ProjectFormData
  previewData: PreviewData
}

defineProps<Props>()

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
  padding-bottom: 150rpx;
  
    .step-header {
      margin-bottom: $spacing-lg;
  
      .step-title {
        display: block;
        font-size: $font-size-xxl;
        font-weight: 600;
        color: $text-main;
        margin-bottom: $spacing-sm;
      }
  
      .step-desc {
        display: block;
        font-size: $font-size-sm;
        color: $text-second;
        line-height: 1.6;
      }
    }
  
    .form-card {
      background: $white;
      border-radius: $radius-lg;
      padding: $spacing-lg;
      padding-bottom: 200rpx;
      box-shadow: 0 8rpx 32rpx rgba(0, 0, 0, 0.06);
    }
}

.form-section {
  margin-bottom: $spacing-lg;

  &:last-child {
      margin-bottom: 0;
    }
  }
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

.form-textarea {
  width: 100%;
  min-height: 160rpx;
  background: $bg-light;
  border-radius: $radius-md;
  padding: $spacing-md;
  font-size: $font-size-md;
  color: $text-main;
  border: 2rpx solid transparent;
  box-sizing: border-box;
  line-height: 1.6;

  &:focus {
    border-color: $primary-orange;
    background: $white;
  }

  &::placeholder {
    color: $text-placeholder;
  }
}
</style>

