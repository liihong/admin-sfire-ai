<template>
  <BaseCard class="ip-preview-card">
    <view class="card-header">
      <SvgIcon name="agent" size="24" color="#F37021" />
      <text class="card-title">您的IP画像</text>
    </view>
    
    <view class="card-content">
      <!-- 基本信息 -->
      <view class="info-row">
        <text class="info-label">名称：</text>
        <text class="info-value">{{ data.name }}</text>
      </view>
      
      <view class="info-row">
        <text class="info-label">行业：</text>
        <text class="info-value">{{ data.industry }}</text>
      </view>
      
      <!-- 风格标签 -->
      <view class="info-row" v-if="data.tone && data.tone !== '未选择'">
        <text class="info-label">风格：</text>
        <BaseTag variant="primary" size="small">{{ data.tone }}</BaseTag>
      </view>
      
      <!-- 目标受众 -->
      <view class="info-row" v-if="data.target_audience && data.target_audience !== '未填写'">
        <text class="info-label">受众：</text>
        <text class="info-value">{{ data.target_audience }}</text>
      </view>
      
      <!-- 关键词 -->
      <view class="info-row" v-if="data.keywords && data.keywords.length > 0">
        <text class="info-label">关键词：</text>
        <view class="keywords-list">
          <BaseTag 
            v-for="(keyword, index) in data.keywords.slice(0, 5)"
            :key="index"
            variant="primary"
            size="small"
          >
            {{ keyword }}
          </BaseTag>
          <text v-if="data.keywords.length > 5" class="more-keywords">+{{ data.keywords.length - 5 }}</text>
        </view>
      </view>
    </view>
  </BaseCard>
</template>

<script setup lang="ts">
import BaseCard from '@/components/base/BaseCard.vue'
import BaseTag from '@/components/base/BaseTag.vue'
import SvgIcon from '@/components/base/SvgIcon.vue'

interface PreviewData {
  name: string
  industry: string
  tone: string
  target_audience: string
  keywords: string[]
}

interface Props {
  data: PreviewData
}

defineProps<Props>()
</script>

<style lang="scss" scoped>
@import '@/styles/_variables.scss';
@import '@/styles/_mixins.scss';

.ip-preview-card {
  margin-top: $spacing-lg;
  
  .card-header {
    display: flex;
    align-items: center;
    gap: $spacing-xs;
    margin-bottom: $spacing-md;
    
    .card-title {
      font-size: $font-size-lg;
      font-weight: 600;
      color: $text-main;
    }
  }
  
  .card-content {
    @include flex-column;
    gap: $spacing-sm;
  }
  
  .info-row {
    display: flex;
    align-items: flex-start;
    gap: $spacing-xs;
    
    .info-label {
      font-size: $font-size-sm;
      color: $text-second;
      flex-shrink: 0;
    }
    
    .info-value {
      font-size: $font-size-sm;
      color: $text-main;
      flex: 1;
    }
    
    .keywords-list {
      display: flex;
      flex-wrap: wrap;
      gap: $spacing-xs;
      align-items: center;
      flex: 1;
      
      .more-keywords {
        font-size: $font-size-xs;
        color: $text-second;
      }
    }
  }
}
</style>

