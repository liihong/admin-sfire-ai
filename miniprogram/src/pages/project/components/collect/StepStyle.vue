<template>
  <scroll-view class="step-content" scroll-y>
    <view class="step-wrapper">
      <TipCard title="定义风格" desc="设定IP的语气风格和详细描述，帮助AI更好地理解您的IP特色" />
      
      <!-- 语气风格选择 -->
      <view class="form-section">
        <text class="form-label">语气风格</text>
        <view class="option-buttons">
          <view
            v-for="item in toneOptions"
            :key="item.value"
            class="option-btn"
            :class="{ selected: formData.tone === item.value }"
            @tap="handleSelect('tone', item.value)"
          >
            <text class="option-text">{{ item.label }}</text>
          </view>
        </view>
      </view>
      
      <!-- IP概况描述 -->
      <view class="form-section">
        <text class="form-label">IP概况描述 <text class="required-mark">*</text></text>
        <textarea 
          class="form-textarea"
          :value="formData.introduction"
          @input="handleInput('introduction', $event)"
          placeholder="请详细描述您的IP定位、特色、核心价值等（至少50字）"
          maxlength="500"
          :auto-height="true"
        />
        <view class="char-count">{{ formData.introduction.length }}/500</view>
      </view>
      
      <!-- 口头禅输入 -->
      <view class="form-section">
        <text class="form-label">口头禅（可选）</text>
        <input 
          class="form-input"
          :value="formData.catchphrase"
          @input="handleInput('catchphrase', $event)"
          placeholder="例如：今天也要加油呀"
          maxlength="20"
        />
      </view>
      
      <!-- IP画像预览 -->
      <IPPreviewCard :data="previewData" />
    </view>
  </scroll-view>
</template>

<script setup lang="ts">
import { watch, onMounted } from 'vue'
import TipCard from './TipCard.vue'
import IPPreviewCard from '../IPPreviewCard.vue'
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
  toneOptions: DictOption[]
  previewData: PreviewData
}

const props = defineProps<Props>()

const emit = defineEmits<{
  'update:formData': [data: Partial<Props['formData']>]
}>()

// IP概况描述模板
function getIntroductionTemplate(name?: string): string {
  const nameLine = name ? `名字：${name}\n` : ''
  return `${nameLine}个人经历：
为什么做这个项目：
行业/项目：
产品或服务特色：
东西咋来的：
目标客户：
客户啥烦恼：
你的想法和信念：
真实小故事或别人咋说：
现在咋样，以后咋打算：`
}

// 初始化：如果 introduction 为空，则设置模板
onMounted(() => {
  if (!props.formData.introduction || props.formData.introduction.trim() === '') {
    const template = getIntroductionTemplate(props.formData.name)
    emit('update:formData', { introduction: template })
  }
})

// 监听名字变化，如果 introduction 是模板且名字变化了，更新模板中的名字
watch(() => props.previewData.name, (newName) => {
  if (newName && props.formData.introduction) {
    // 检查是否是模板格式（包含"名字："）
    if (props.formData.introduction.includes('名字：') && 
        props.formData.introduction.includes('个人经历：')) {
      // 更新模板中的名字
      const template = getIntroductionTemplate(newName)
      emit('update:formData', { introduction: template })
    }
  }
})

function handleInput(field: string, e: any) {
  emit('update:formData', { [field]: e.detail.value })
}

function handleSelect(field: string, value: string) {
  emit('update:formData', { [field]: value })
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
    min-height: 200rpx;
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
}

.option-buttons {
  display: flex;
  flex-wrap: wrap;
  gap: $spacing-sm;
  
  .option-btn {
    padding: 10rpx 20rpx;
    background: $bg-light;
    border-radius: 32rpx;
    border: 2rpx solid transparent;
    transition: all $transition-base;
    
    &.selected {
      background: linear-gradient(135deg, rgba($primary-orange, 0.1) 0%, rgba($primary-orange, 0.15) 100%);
      border-color: $primary-orange;
      
      .option-text {
        color: $primary-orange;
        font-weight: 600;
      }
    }
    
    .option-text {
      font-size: $font-size-md;
      color: $text-second;
    }
  }
}
</style>

