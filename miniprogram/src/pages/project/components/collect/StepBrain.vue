<template>
  <scroll-view class="step-content" scroll-y>
    <view class="step-wrapper">
      <!-- 标题 -->
      <view class="step-header">
        <text class="step-title">激活 AI 创作大脑</text>
        <text class="step-subtitle">基于你的设定，AI 已为你提炼出创作关键词</text>
      </view>
      
      <!-- 关键词展示 -->
      <view class="keywords-section">
        <view 
          v-for="(keyword, index) in keywords"
          :key="index"
          class="keyword-tag"
        >
          <text class="keyword-text">{{ keyword }}</text>
        </view>
        <view 
          v-if="keywords.length === 0 && !isGeneratingKeywords"
          class="keyword-placeholder"
        >
          <text class="placeholder-text">正在生成关键词...</text>
        </view>
      </view>
      
      <!-- 添加补充 -->
      <view class="form-section">
        <TagInput
          :model-value="keywords"
          @update:model-value="handleKeywordsUpdate"
          placeholder="添加补充"
        />
      </view>
      
      <!-- 说明信息框 -->
      <view class="info-box">
        <u-icon name="info-circle" color="#F37021" size="20"></u-icon>
        <view class="info-content">
          <text class="info-title">下一步说明</text>
          <text class="info-text">点击确认后，你的IP信息将同步至创作台。AI将严格遵守上述人设参数，为你提供符合IP风格的文案和选题建议。</text>
        </view>
      </view>
    </view>
  </scroll-view>
</template>

<script setup lang="ts">
import TagInput from '@/components/form/TagInput.vue'

interface Props {
  keywords: string[]
  isGeneratingKeywords: boolean
}

const props = defineProps<Props>()

const emit = defineEmits<{
  'update:keywords': [keywords: string[]]
}>()

function handleKeywordsUpdate(keywords: string[]) {
  emit('update:keywords', keywords)
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
  }
}

.keywords-section {
  display: flex;
  flex-wrap: wrap;
  gap: $spacing-sm;
  margin-bottom: $spacing-lg;
  
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
  
  .keyword-placeholder {
    width: 100%;
    text-align: center;
    padding: $spacing-lg;
    
    .placeholder-text {
      font-size: $font-size-md;
      color: $text-second;
    }
  }
}

.form-section {
  margin-bottom: $spacing-lg;
}

.info-box {
  background: rgba($text-main, 0.05);
  border-radius: $radius-md;
  padding: $spacing-md;
  display: flex;
  gap: $spacing-sm;
  
  
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

