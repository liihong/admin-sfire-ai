<template>
  <scroll-view class="step-content" scroll-y>
    <view class="step-wrapper">
     <view class="step-header">
        <text class="step-desc">请您尽可能详细的填写该问卷，这将帮助AI更好地理解您的IP，从而生成更符合您需求的内容</text>
      </view>
    <view class="form-card">
        <!-- 名称 + 年龄 -->
        <view class="form-row">
          <view class="form-col">
            <text class="form-label">名称 <text class="required-mark">*</text></text>
            <input class="form-input" :value="formData.name"
placeholder="隔壁老陈 / 丽姐" maxlength="20"
             @input="handleNameInput"
/>
          </view>
         <view class="form-col">
            <text class="form-label">年龄</text>
            <input class="form-input" :value="formData.ip_age" placeholder="36 / 1990" maxlength="20"
              @input="handleInput('ip_age', $event)" />
          </view>
        </view>

      <!-- 城市 + 所属行业 -->
        <view class="form-row">
          <view class="form-col">
            <text class="form-label">城市</text>
            <input class="form-input" :value="formData.ip_city" placeholder="北京/朝阳区 河南/新乡市" maxlength="50"
              @input="handleInput('ip_city', $event)" />
          </view>
          <view class="form-col form-col-picker">
            <FormPicker
label="所属行业"
:model-value="formData.industry"
:range="industryOptionsList" placeholder="通用"
             @update:model-value="handleIndustryChange"
/>
          </view>
       </view>

      <view class="form-section">
         <text class="form-label">身份标签</text>
          <input class="form-input" :value="formData.ip_identityTag" placeholder="宝妈，二胎妈妈，前HR，程序员转行，85后北漂10年"
            maxlength="100" @input="handleInput('ip_identityTag', $event)" />
        </view>

      <view class="form-section">
         <text class="form-label">经历介绍</text>
          <textarea class="form-textarea" :value="formData.ip_experience" placeholder="请涵盖：过往职业、转折点、从业初衷、最大挑战..."
            maxlength="2000" :auto-height="true" :adjust-position="true" :cursor-spacing="20" :show-confirm-bar="false"
            @input="handleInput('ip_experience', $event)" />
          <view class="char-count">{{ formData.ip_experience.length }}/2000</view>
        </view>
      </view>
    </view>
  </scroll-view>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import FormPicker from '@/components/form/FormPicker.vue'
import type { DictOption } from '@/api/project'
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
  industryOptions: DictOption[]
  previewData: PreviewData
}

const props = defineProps<Props>()

const emit = defineEmits<{
  'update:formData': [data: Partial<Props['formData']>]
}>()

const industryOptionsList = computed(() => {
  return props.industryOptions.map(item => item.value || item.label)
})

function handleNameInput(e: any) {
  const v = e.detail.value
  emit('update:formData', { name: v, ip_name: v })
}

function handleInput(field: string, e: any) {
  emit('update:formData', { [field]: e.detail.value })
}

function handleIndustryChange(value: string | number) {
  const s = String(value)
  emit('update:formData', { industry: s, ip_industry: s })
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
  }
  
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
    box-shadow: 0 8rpx 32rpx rgba(0, 0, 0, 0.06);
  }
  
  .form-row {
    display: flex;
    gap: $spacing-md;
    margin-bottom: $spacing-lg;
  
    .form-col {
      flex: 1;
      min-width: 0;
    }
  
    .form-col-picker {
      :deep(.form-item) {
        margin-bottom: 0;
      }
  
      :deep(.form-item__picker) {
        background-color: $bg-light;
        border: 2rpx solid transparent;
        box-shadow: none;
      }
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
  min-height: 220rpx;
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

.char-count {
  text-align: right;
  font-size: $font-size-xs;
  color: $text-second;
  margin-top: $spacing-xs;
}
</style>

