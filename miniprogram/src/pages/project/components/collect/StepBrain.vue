<template>
  <scroll-view class="step-content" scroll-y>
    <view class="step-wrapper">
      <view class="step-header">
        <text class="step-title">确认信息</text>
        <text class="step-subtitle">请确认以下信息，AI将根据以下内容进行定位分析</text>
      </view>

      <view class="info-display-section">
        <!-- IP 个人定位 -->
        <view class="info-group">
          <text class="group-title">IP 个人定位</text>
          <view class="info-row">
            <view class="info-item info-item-horizontal">
              <text class="info-label">名称</text>
              <text class="info-value info-value-plain">{{ formData.name || '未填写' }}</text>
            </view>
            <view class="info-item info-item-horizontal">
              <text class="info-label">所属行业</text>
              <text class="info-value info-value-plain">{{ industryLabel || formData.industry || '未选择' }}</text>
            </view>
          </view>
          <view class="info-row">
            <view class="info-item info-item-horizontal">
              <text class="info-label">年龄</text>
              <text class="info-value info-value-plain">{{ formData.ip_age || '未填写' }}</text>
            </view>
            <view class="info-item info-item-horizontal">
              <text class="info-label">城市</text>
              <text class="info-value info-value-plain">{{ formData.ip_city || '未填写' }}</text>
            </view>
          </view>
          <view class="info-item">
            <text class="info-label">身份标签</text>
            <view class="info-value">{{ formData.ip_identityTag || '未填写' }}</view>
          </view>
          <view class="info-item">
            <text class="info-label">经历介绍</text>
            <view class="info-value info-text">{{ formData.ip_experience || '未填写' }}</view>
          </view>
        </view>

        <!-- 商业定位 -->
        <view class="info-group">
          <text class="group-title">商业定位</text>
          <view class="info-item">
            <text class="info-label">主要产品/服务</text>
            <view class="info-value">{{ formData.cl_mainProducts || '未填写' }}</view>
          </view>
          <view class="info-item">
            <text class="info-label">目标人群</text>
            <view class="info-value">{{ formData.cl_targetPopulation || '未填写' }}</view>
          </view>
          <view class="info-item">
            <text class="info-label">目标人群痛点</text>
            <view class="info-value">{{ formData.cl_painPoints || '未填写' }}</view>
          </view>
          <view class="info-item">
            <text class="info-label">产品优势</text>
            <view class="info-value">{{ formData.cl_advantages || '未填写' }}</view>
          </view>
          <view class="info-item">
            <text class="info-label">客户反馈</text>
            <view class="info-value">{{ formData.cl_feedback || '未填写' }}</view>
          </view>
        </view>

        <!-- 风格定位 -->
        <view class="info-group">
          <text class="group-title">风格定位</text>
          <view class="info-item">
            <text class="info-label">语气风格</text>
            <view class="info-value">{{ toneLabel || formData.style_tones || '未选择' }}</view>
          </view>
          <view class="info-item">
            <text class="info-label">个人口头禅</text>
            <view class="info-value">{{ formData.style_mantra || '未填写' }}</view>
          </view>
        </view>

        <!-- 创作关键词 -->
        <view class="info-group">
          <text class="group-title">创作关键词</text>
          <view v-if="formData.keywords && formData.keywords.length > 0" class="keywords-display">
            <view v-for="(keyword, index) in formData.keywords" :key="index" class="keyword-tag">
              <text class="keyword-text">{{ keyword }}</text>
            </view>
          </view>
          <view v-else class="keywords-empty">
            <text class="empty-text">暂无关键词</text>
          </view>
        </view>
      </view>

      <view class="info-box">
        <u-icon name="info-circle" color="#F37021" size="20"></u-icon>
        <view class="info-content">
          <text class="info-title">下一步说明</text>
          <text class="info-text">确认无误后，点击下方「生成IP定位报告」按钮，你的IP信息将同步至创作台。AI将严格遵守上述人设参数，为你提供符合IP风格的文案和选题建议。</text>
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

const industryLabel = computed(() => {
  if (!props.industryOptions || !props.formData.industry) return ''
  const option = props.industryOptions.find((opt) => opt.value === props.formData.industry)
  return option?.label || props.formData.industry
})

const toneLabel = computed(() => {
  if (!props.toneOptions || !props.formData.style_tones) return ''
  const option = props.toneOptions.find((opt) => opt.value === props.formData.style_tones)
  return option?.label || props.formData.style_tones
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
  margin-bottom: $spacing-md;

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
  margin-bottom: 100rpx;
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
    margin-bottom: 10rpx;
    padding-bottom: 10rpx;
    border-bottom: 2rpx solid rgba($text-main, 0.1);
  }

  .info-row {
    display: flex;
    gap: $spacing-md;
    margin-bottom: $spacing-md;
  }

  .info-item {
    margin-bottom: $spacing-md;

    &:last-child {
      margin-bottom: 0;
    }

    &.info-item-horizontal {
      flex: 1;
      margin-bottom: 0;
      display: flex;
      flex-direction: column;
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

      &.info-value-plain {
        background: transparent;
        padding: 0;
        border-radius: 0;
        min-height: auto;
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
