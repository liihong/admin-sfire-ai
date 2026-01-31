<template>
  <scroll-view class="step-content" scroll-y>
    <view class="step-wrapper">
      <!-- 标题 -->
      <view class="step-header">
       <text class="step-title">确认信息</text>
        <text class="step-subtitle">请确认以下信息是否正确，如需修改请返回上一步进行编辑</text>
      </view>

    <!-- 信息展示区域 -->
      <view class="info-display-section">
        <!-- 基本信息 -->
        <view class="info-group">
          <text class="group-title">基本信息</text>

          <view class="info-item">
            <text class="info-label">IP名称</text>
            <view class="info-value">{{ formData.name || '未填写' }}</view>
          </view>
         <view class="info-item">
            <text class="info-label">行业赛道</text>
            <view class="info-value">{{ industryLabel || formData.industry || '未选择' }}</view>
          </view>
        </view>

       <!-- 行业理解 -->
        <view class="info-group">
          <text class="group-title">行业理解</text>

        <view class="info-item">
            <text class="info-label">对行业的理解</text>
            <view class="info-value">{{ formData.industry_understanding || '未填写' }}</view>
          </view>

          <view class="info-item">
            <text class="info-label">对行业不同的看法</text>
            <view class="info-value">{{ formData.unique_views || '未填写' }}</view>
          </view>
        </view>

        <!-- 受众定位 -->
        <view class="info-group">
          <text class="group-title">受众定位</text>

          <view class="info-item">
            <text class="info-label">目标人群</text>
            <view class="info-value">{{ formData.target_audience || '未填写' }}</view>
          </view>

          <view class="info-item">
            <text class="info-label">目标人群痛点</text>
            <view class="info-value">{{ formData.target_pains || '未填写' }}</view>
          </view>
        </view>

        <!-- 风格定位 -->
        <view class="info-group">
          <text class="group-title">风格定位</text>

          <view class="info-item">
            <text class="info-label">语气风格</text>
            <view class="info-value">{{ toneLabel || formData.tone || '未选择' }}</view>
          </view>
          <view class="info-item">
            <text class="info-label">口头禅</text>
            <view class="info-value">{{ formData.catchphrase || '未填写' }}</view>
          </view>
          <view class="info-item">
            <text class="info-label">IP概况描述</text>
            <view class="info-value info-text">{{ formData.introduction || '未填写' }}</view>
          </view>
        </view>
        <!-- 关键词 -->
        <view class="info-group">
          <text class="group-title">创作关键词</text>
          <view class="keywords-display" v-if="formData.keywords && formData.keywords.length > 0">
            <view v-for="(keyword, index) in formData.keywords" :key="index" class="keyword-tag">
              <text class="keyword-text">{{ keyword }}</text>
            </view>
          </view>
          <view class="keywords-empty" v-else>
            <text class="empty-text">暂无关键词</text>
          </view>
        </view>
      </view>
      
      <!-- 说明信息框 -->
      <view class="info-box">
        <u-icon name="info-circle" color="#F37021" size="20"></u-icon>
        <view class="info-content">
          <text class="info-title">下一步说明</text>
         <text class="info-text">确认无误后，点击下方"生成IP定位报告"按钮，你的IP信息将同步至创作台。AI将严格遵守上述人设参数，为你提供符合IP风格的文案和选题建议。</text>
        </view>
      </view>
    </view>
  </scroll-view>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { ProjectFormData } from '@/types/project'
import type { DictOption } from '@/api/project'

interface Props {
  formData: ProjectFormData
  industryOptions?: DictOption[]
  toneOptions?: DictOption[]
}

const props = defineProps<Props>()

// 获取行业标签
const industryLabel = computed(() => {
  if (!props.industryOptions || !props.formData.industry) return ''
  const option = props.industryOptions.find(opt => opt.value === props.formData.industry)
  return option?.label || props.formData.industry
})

// 获取语气风格标签
const toneLabel = computed(() => {
  if (!props.toneOptions || !props.formData.tone) return ''
  const option = props.toneOptions.find(opt => opt.value === props.formData.tone)
  return option?.label || props.formData.tone
})
</script>

<style lang="scss" scoped>
@import '@/styles/_variables.scss';
@import '@/styles/_mixins.scss';

.step-content {
  height: 100%;
}

.step-wrapper {
  padding: $spacing-lg;
  padding-bottom: $spacing-xl;
}

.step-header {
  text-align: center;
  margin-bottom: $spacing-xl;
  
  .step-title {
    display: block;
    font-size: $font-size-xxl;
    font-weight: 600;
    color: $text-main;
    margin-bottom: $spacing-sm;
  }
  
  .step-subtitle {
    display: block;
    font-size: $font-size-md;
    color: $text-second;
    line-height: 1.5;
    }
    }
    
    .info-display-section {
      margin-bottom: $spacing-lg;
    }
    
    .info-group {
      background: $bg-light;
      border-radius: $radius-md;
      padding: $spacing-md;
      margin-bottom: $spacing-md;
    
      .group-title {
        display: block;
        font-size: $font-size-lg;
        font-weight: 600;
        color: $text-main;
        margin-bottom: $spacing-md;
        padding-bottom: $spacing-sm;
        border-bottom: 2rpx solid rgba($text-main, 0.1);
      }
    
      .info-item {
        margin-bottom: $spacing-md;
    
        &:last-child {
          margin-bottom: 0;
        }
    
        .info-label {
          display: block;
          font-size: $font-size-sm;
          color: $text-second;
          margin-bottom: $spacing-xs;
          font-weight: 500;
        }
    
        .info-value {
          font-size: $font-size-md;
          color: $text-main;
          padding: $spacing-sm $spacing-md;
          background: $white;
          border-radius: $radius-sm;
          min-height: 44rpx;
          line-height: 1.6;
          word-break: break-all;
    
          &.info-text {
            min-height: auto;
            padding: $spacing-md;
            white-space: pre-wrap;
          }
        }
  }
}

.keywords-display {
  display: flex;
  flex-wrap: wrap;
  gap: $spacing-sm;
  
  .keyword-tag {
    padding: 12rpx 20rpx;
    background: linear-gradient(135deg, rgba($primary-orange, 0.1) 0%, rgba($primary-orange, 0.15) 100%);
    border-radius: 24rpx;
    border: 2rpx solid $primary-orange;
    
    .keyword-text {
      font-size: $font-size-sm;
      color: $primary-orange;
      font-weight: 500;
    }
  }
}

.keywords-empty {
  padding: $spacing-md;
  text-align: center;
  
  .empty-text {
      font-size: $font-size-sm;
      color: $text-placeholder;
}

.info-box {
  background: rgba($primary-orange, 0.05);
  border-radius: $radius-md;
  padding: $spacing-md;
  display: flex;
  gap: $spacing-sm;
  border: 2rpx solid rgba($primary-orange, 0.2);
  
  .info-content {
    flex: 1;
    @include flex-column;
    gap: $spacing-xs;
    
    .info-title {
      font-size: $font-size-md;
      font-weight: 600;
      color: $text-main;
    }
    
    .info-text {
      font-size: $font-size-sm;
      color: $text-second;
      line-height: 1.6;
    }
  }
}
</style>

