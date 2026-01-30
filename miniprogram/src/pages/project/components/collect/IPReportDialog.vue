<template>
  <view class="ip-report-dialog" v-if="visible" @tap.stop>
    <view class="dialog-mask" @tap="handleCancel"></view>
    <view class="dialog-content">
      <scroll-view class="report-scroll" scroll-y>
        <view class="report-wrapper">
          <!-- 标题 -->
          <view class="report-header">
            <text class="report-title">IP 数字化人格定位报告</text>
            <text class="report-subtitle">{{ reportData.name }}</text>
          </view>
          
          <!-- 评分展示 -->
          <view class="score-section">
            <view class="score-display">
              <text class="score-number">{{ reportData.score }}</text>
              <text class="score-label">分</text>
            </view>
            <view class="score-bar">
              <view class="score-bar-fill" :style="{ width: reportData.score + '%' }"></view>
            </view>
            <text class="score-reason">{{ reportData.score_reason }}</text>
          </view>
          
          <!-- 报告内容 -->
          <view class="report-content">
            <!-- 01. 数字化人格画像 -->
            <view class="report-section">
              <view class="section-header">
                <text class="section-number">01.</text>
                <text class="section-title">数字化人格画像</text>
              </view>
              <view class="section-content">
                <view class="persona-tags">
                  <view 
                    v-for="(tag, index) in reportData.report.persona_tags"
                    :key="index"
                    class="tag-item"
                  >
                    <text class="tag-text">{{ tag }}</text>
                  </view>
                </view>
                <view class="persona-info">
                  <text class="info-label">核心原型：</text>
                  <text class="info-value">{{ reportData.report.core_archetype }}</text>
                </view>
                <view class="persona-info">
                  <text class="info-label">一句话简介：</text>
                  <text class="info-value">{{ reportData.report.one_line_intro }}</text>
                </view>
              </view>
            </view>
            
            <!-- 02. 内容护城河 -->
            <view class="report-section">
              <view class="section-header">
                <text class="section-number">02.</text>
                <text class="section-title">内容护城河</text>
              </view>
              <view class="section-content">
                <view class="content-item">
                  <text class="item-label">反共识洞察：</text>
                  <text class="item-text">{{ reportData.report.content_moat.insight }}</text>
                </view>
                <view class="content-item">
                  <text class="item-label">情感钩子：</text>
                  <text class="item-text">{{ reportData.report.content_moat.emotional_hook }}</text>
                </view>
              </view>
            </view>
            
            <!-- 03. 语言指纹分析 -->
            <view class="report-section">
              <view class="section-header">
                <text class="section-number">03.</text>
                <text class="section-title">语言指纹分析</text>
              </view>
              <view class="section-content">
                <view class="content-item">
                  <text class="item-label">语感建模：</text>
                  <text class="item-text">{{ reportData.report.language_fingerprint.tone_modeling }}</text>
                </view>
                <view class="content-item">
                  <text class="item-label">标志性氛围：</text>
                  <text class="item-text">{{ reportData.report.language_fingerprint.atmosphere }}</text>
                </view>
              </view>
            </view>
            
            <!-- 04. 商业潜力与避坑指南 -->
            <view class="report-section">
              <view class="section-header">
                <text class="section-number">04.</text>
                <text class="section-title">商业潜力与避坑指南</text>
              </view>
              <view class="section-content">
                <view class="content-item">
                  <text class="item-label">爆款潜质：</text>
                  <text class="item-text">{{ reportData.report.business_potential.viral_potential }}</text>
                </view>
                <view class="content-item">
                  <text class="item-label">人设红线：</text>
                  <text class="item-text">{{ reportData.report.business_potential.red_lines }}</text>
                </view>
              </view>
            </view>
            
            <!-- 05. 专家寄语 -->
            <view class="report-section">
              <view class="section-header">
                <text class="section-number">05.</text>
                <text class="section-title">专家寄语</text>
              </view>
              <view class="section-content">
                <text class="expert-message">{{ reportData.report.expert_message }}</text>
              </view>
            </view>
          </view>
        </view>
      </scroll-view>
      
      <!-- 底部操作栏 -->
      <view class="dialog-footer">
        <view class="footer-btn export-btn" @tap="handleExport">
          <u-icon name="download" color="#F37021" size="20"></u-icon>
          <text class="btn-text">导出报告</text>
        </view>
        <view class="footer-btn confirm-btn" @tap="handleConfirm">
          <text class="btn-text">确认并创建 IP</text>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import type { IPReportResponse } from '@/api/project'

interface Props {
  visible: boolean
  reportData: IPReportResponse
}

const props = defineProps<Props>()

const emit = defineEmits<{
  'confirm': []
  'cancel': []
}>()

function handleConfirm() {
  emit('confirm')
}

function handleCancel() {
  emit('cancel')
}

async function handleExport() {
  try {
    // 小程序canvas导出功能实现说明：
    // 1. 需要使用canvas组件渲染报告内容
    // 2. 使用uni.canvasToTempFilePath转换为临时文件
    // 3. 使用uni.saveImageToPhotosAlbum保存到相册
    // 
    // 由于报告内容较长且复杂，建议：
    // - 方案1：后端生成图片（推荐，性能更好）
    // - 方案2：前端使用canvas组件逐块渲染（复杂，性能较差）
    // 
    // 当前实现：提示用户截图保存
    
    uni.showModal({
      title: '导出报告',
      content: '报告导出功能正在开发中。您可以长按屏幕截图保存当前报告内容，或联系客服获取完整报告。',
      showCancel: true,
      cancelText: '取消',
      confirmText: '知道了',
      success: (res) => {
        if (res.confirm) {
          // 用户确认，可以添加其他操作
        }
      }
    })
  } catch (error: any) {
    console.error('导出报告失败:', error)
    uni.showToast({
      title: error.message || '导出失败，请重试',
      icon: 'none',
      duration: 2000
    })
  }
}
</script>

<style lang="scss" scoped>
@import '@/styles/_variables.scss';
@import '@/styles/_mixins.scss';

.ip-report-dialog {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: $z-index-modal;
  @include flex-center;
}

.dialog-mask {
  @include fixed-fullscreen;
  background: rgba(0, 0, 0, 0.5);
  backdrop-filter: blur(4rpx);
}

.dialog-content {
  position: relative;
  width: 90%;
  max-width: 700rpx;
  max-height: 85vh;
  background: $white;
  border-radius: $radius-xl;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  box-shadow: $shadow-lg;
}

.report-scroll {
  flex: 1;
  height: 0;
}

.report-wrapper {
  padding: $spacing-xl;
  padding-bottom: $spacing-lg;
}

.report-header {
  text-align: center;
  margin-bottom: $spacing-xl;
  
  .report-title {
    display: block;
    font-size: $font-size-xxl;
    font-weight: 600;
    color: $text-main;
    margin-bottom: $spacing-sm;
  }
  
  .report-subtitle {
    display: block;
    font-size: $font-size-lg;
    color: $primary-orange;
    font-weight: 500;
  }
}

.score-section {
  background: linear-gradient(135deg, rgba($primary-orange, 0.1) 0%, rgba($primary-orange, 0.05) 100%);
  border-radius: $radius-lg;
  padding: $spacing-lg;
  margin-bottom: $spacing-xl;
  text-align: center;
  
  .score-display {
    @include flex-center;
    gap: $spacing-xs;
    margin-bottom: $spacing-md;
    
    .score-number {
      font-size: 72rpx;
      font-weight: 700;
      color: $primary-orange;
      line-height: 1;
    }
    
    .score-label {
      font-size: $font-size-lg;
      color: $text-second;
      margin-top: 8rpx;
    }
  }
  
  .score-bar {
    width: 100%;
    height: 12rpx;
    background: rgba($primary-orange, 0.1);
    border-radius: 6rpx;
    overflow: hidden;
    margin-bottom: $spacing-md;
    
    .score-bar-fill {
      height: 100%;
      background: linear-gradient(90deg, $primary-orange 0%, $primary-orange-alt 100%);
      border-radius: 6rpx;
      transition: width 0.5s ease;
    }
  }
  
  .score-reason {
    font-size: $font-size-sm;
    color: $text-second;
    line-height: 1.6;
  }
}

.report-content {
  @include flex-column;
  gap: $spacing-lg;
}

.report-section {
  @include card-style;
  
  .section-header {
    @include flex-center-vertical;
    gap: $spacing-sm;
    margin-bottom: $spacing-md;
    padding-bottom: $spacing-sm;
    border-bottom: 2rpx solid $border-color;
    
    .section-number {
      font-size: $font-size-lg;
      font-weight: 600;
      color: $primary-orange;
    }
    
    .section-title {
      font-size: $font-size-lg;
      font-weight: 600;
      color: $text-main;
    }
  }
  
  .section-content {
    @include flex-column;
    gap: $spacing-md;
  }
}

.persona-tags {
  display: flex;
  flex-wrap: wrap;
  gap: $spacing-sm;
  margin-bottom: $spacing-md;
  
  .tag-item {
    padding: 8rpx 16rpx;
    background: linear-gradient(135deg, rgba($primary-orange, 0.1) 0%, rgba($primary-orange, 0.15) 100%);
    border-radius: 20rpx;
    border: 2rpx solid $primary-orange;
    
    .tag-text {
      font-size: $font-size-sm;
      color: $primary-orange;
      font-weight: 500;
    }
  }
}

.persona-info {
  @include flex-column;
  gap: $spacing-xs;
  
  .info-label {
    font-size: $font-size-sm;
    color: $text-second;
    font-weight: 500;
  }
  
  .info-value {
    font-size: $font-size-md;
    color: $text-main;
    line-height: 1.6;
  }
}

.content-item {
  @include flex-column;
  gap: $spacing-xs;
  
  .item-label {
    font-size: $font-size-sm;
    color: $text-second;
    font-weight: 500;
  }
  
  .item-text {
    font-size: $font-size-md;
    color: $text-main;
    line-height: 1.6;
  }
}

.expert-message {
  font-size: $font-size-md;
  color: $text-main;
  line-height: 1.8;
  font-style: italic;
  padding: $spacing-md;
  background: rgba($primary-orange, 0.05);
  border-radius: $radius-md;
  border-left: 4rpx solid $primary-orange;
}

.dialog-footer {
  display: flex;
  gap: $spacing-md;
  padding: $spacing-lg;
  border-top: 1rpx solid $border-color;
  background: $white;
  
  .footer-btn {
    flex: 1;
    height: 88rpx;
    border-radius: $radius-xl;
    @include flex-center;
    font-size: $font-size-md;
    font-weight: 500;
    transition: all $transition-base;
    
    &.export-btn {
      background: $bg-light;
      color: $primary-orange;
      gap: $spacing-xs;
      
      &:active {
        background: rgba($primary-orange, 0.1);
      }
    }
    
    &.confirm-btn {
      background: linear-gradient(135deg, $primary-orange 0%, $primary-orange-alt 100%);
      color: $white;
      box-shadow: 0 4rpx 12rpx rgba($primary-orange, 0.3);
      
      &:active {
        transform: scale(0.98);
      }
    }
    
    .btn-text {
      font-size: $font-size-md;
    }
  }
}
</style>

