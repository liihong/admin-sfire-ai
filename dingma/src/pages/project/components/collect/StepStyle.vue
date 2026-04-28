<template>
  <scroll-view class="step-content" scroll-y :enhanced="true" :enable-passive="true">
    <view class="step-wrapper">
      <view class="step-header">
      </view>

      <view class="form-card">
        <view class="form-section">
          <text class="form-label">语气风格（单选） <text class="required-mark">*</text></text>
          <text class="form-sub">设定IP的语气风格，帮助AI更好地理解您的IP特色</text>
          <view class="tone-grid">
            <view v-for="item in toneOptions" :key="item.value" class="tone-chip"
              :class="{ selected: formData.style_tones === item.value }" @tap="handleSelect('style_tones', item.value)">
              <text v-if="formData.style_tones === item.value" class="tone-check">✓</text>
              <text class="tone-text">{{ item.label }}</text>
            </view>
          </view>
        </view>

        <view class="form-section">
          <text class="form-label">个人口头禅（可选）</text>
          <input class="form-input" :value="formData.style_mantra" placeholder="例如：加油呀，姐妹们" maxlength="40"
            @input="handleInput('style_mantra', $event)" />
        </view>
      </view>
    </view>
  </scroll-view>
</template>

<script setup lang="ts">
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
  toneOptions: DictOption[]
  previewData: PreviewData
}

defineProps<Props>()

const emit = defineEmits<{
  'update:formData': [data: Partial<Props['formData']>]
}>()

function handleInput(field: string, e: any) {
  emit('update:formData', { [field]: e.detail.value })
}

function handleSelect(field: string, value: string) {
  emit('update:formData', { [field]: value })
}
</script>

<style lang="scss" scoped>
@import '@/styles/_variables.scss';
@import '@/styles/_mixins.scss';

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
    }
  }
  
  .form-card {
    background: $white;
    border-radius: $radius-lg;
    padding: $spacing-lg;
    box-shadow: 0 8rpx 32rpx rgba(0, 0, 0, 0.06);
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
  margin-bottom: $spacing-xs;
    .required-mark {
      color: $color-error;
    }
  }
.form-sub {
  display: block;
  font-size: $font-size-xs;
  color: $text-second;
  margin-bottom: $spacing-md;
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
.tone-grid {
  display: flex;
  flex-wrap: wrap;
  gap: $spacing-sm;
}

.tone-chip {
  position: relative;
  width: calc(50% - 8rpx);
  box-sizing: border-box;
  min-height: 80rpx;
  padding: 16rpx 20rpx;
  background: $bg-light;
  border-radius: $radius-md;
    border: 2rpx solid transparent;
  @include flex-center;
  transition: all $transition-base;
    &.selected {
    background: rgba($primary-orange, 0.08);
      border-color: $primary-orange;
    .tone-text {
        color: $primary-orange;
        font-weight: 600;
      }
    }
        .tone-check {
          position: absolute;
          top: 8rpx;
          right: 12rpx;
          font-size: $font-size-xs;
          color: $primary-orange;
          font-weight: 700;
        }
  
        .tone-text {
      font-size: $font-size-md;
      color: $text-second;
    text-align: center;
      line-height: 1.35;
  }
}
</style>

