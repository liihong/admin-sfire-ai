<template>
  <view class="report-page">
    <!-- 顶部导航栏 -->
    <BaseHeader title="IP 数字化人格定位报告" @back="handleBack" />
    
    <!-- 报告内容 -->
    <scroll-view class="report-scroll" scroll-y>
      <view class="report-wrapper">
        <!-- Loading状态 -->
        <view v-if="isLoadingReport" class="loading-section">
          <u-loading-icon mode="spinner" color="#F37021" size="60"></u-loading-icon>
          <text class="loading-text">AI正在解析人格并且生成报告中，请耐心等待...</text>
          <view class="loading-dots">
            <text class="dot">.</text>
            <text class="dot">.</text>
            <text class="dot">.</text>
          </view>
        </view>
        
        <!-- 报告内容 -->
        <template v-else-if="reportData">
          <!-- IP名称 -->
          <view class="report-header">
            <text class="report-subtitle">{{ reportData.report.name || '未命名IP' }}</text>
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
        </template>
        
        <!-- 错误状态 -->
        <view v-else-if="reportError" class="error-section">
          <text class="error-icon">⚠️</text>
          <text class="error-text">{{ reportError }}</text>
          <view class="error-actions">
            <view class="error-btn" @tap="generateReport">
              <text>重新生成</text>
            </view>
            <view class="error-btn secondary" @tap="handleBack">
              <text>返回</text>
            </view>
          </view>
        </view>
      </view>
    </scroll-view>
    
    <!-- 底部操作栏 -->
    <view class="page-footer">
      <view class="footer-btn export-btn" @tap="handleExport">
        <u-icon name="download" color="#F37021" size="20"></u-icon>
        <text class="btn-text">导出报告</text>
      </view>
      <view class="footer-btn save-btn" @tap="handleSave" :class="{ disabled: isSaving || !reportData || isLoadingReport }">
        <u-loading-icon v-if="isSaving" mode="spinner" color="#FFFFFF" size="16"></u-loading-icon>
        <text class="btn-text">{{ isSaving ? '保存中...' : '将IP注入基因库' }}</text>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { useProjectStore } from '@/stores/project'
import BaseHeader from '@/components/base/BaseHeader.vue'
import { createProject, generateIPReport } from '@/api/project'
import { formDataToCreateRequest } from '@/utils/project'
import type { IPReportResponse } from '@/api/project'
import type { IPCollectFormData } from '@/api/project'

// Store
const projectStore = useProjectStore()

// 状态
const reportData = ref<IPReportResponse | null>(null)
const formData = ref<IPCollectFormData | null>(null)
const isSaving = ref(false)
const isLoadingReport = ref(false)
const reportError = ref<string | null>(null)

// 页面加载时生成报告
onMounted(() => {
  // 从store加载表单数据
  const hasData = loadFormData()
  // 如果数据加载成功，才生成报告
  if (hasData) {
    generateReport()
  }
})

/**
 * 从store加载表单数据
 */
function loadFormData() {
  try {
    const cachedData = projectStore.loadIPCollectFormData()
    if (cachedData) {
      formData.value = cachedData
      return true
    } else {
      reportError.value = '表单数据不存在，请返回重新填写'
      return false
    }
  } catch (error) {
    console.error('加载表单数据失败:', error)
    reportError.value = '表单数据格式错误，请返回重新填写'
    return false
  }
}

/**
 * 生成IP定位报告
 */
async function generateReport() {
  if (!formData.value) {
    reportError.value = '表单数据不存在，请返回重新填写'
    return
  }
  
  if (isLoadingReport.value) return
  
  isLoadingReport.value = true
  reportError.value = null
  
  // 确保页面不会自动跳转
  console.log('开始生成报告，当前页面状态正常')
  
  try {
    // 构建报告生成请求数据
    const reportRequest = {
      name: formData.value.name,
      industry: formData.value.industry,
      introduction: formData.value.introduction || '',
      tone: formData.value.tone || '',
      target_audience: formData.value.target_audience || '',
      target_pains: formData.value.target_pains || '',
      keywords: formData.value.keywords || [],
      industry_understanding: formData.value.industry_understanding || '',
      unique_views: formData.value.unique_views || '',
      catchphrase: formData.value.catchphrase || ''
    }
    
    console.log('开始生成报告，请求数据:', reportRequest)
    
    // 调用报告生成接口
    const response = await generateIPReport(reportRequest)
    
    console.log('报告生成成功:', response)
    reportData.value = response
    
  } catch (error: any) {
    console.error('生成IP定位报告失败:', error)
    const errorMsg = error.message || '报告生成失败，请重试'
    reportError.value = errorMsg
    uni.showToast({
      title: errorMsg,
      icon: 'none',
      duration: 2000
    })
  } finally {
    isLoadingReport.value = false
  }
}

function handleBack() {
  uni.navigateBack({
    fail: () => {
      uni.switchTab({ url: '/pages/project/index' })
    }
  })
}

async function handleSave() {
  if (isSaving.value) return
  
  // 检查表单数据是否存在
  if (!formData.value) {
    uni.showToast({
      title: '表单数据不存在，无法保存',
      icon: 'none'
    })
    return
  }
  
  isSaving.value = true
  
  try {
    uni.showLoading({
      title: '正在保存...',
      mask: true
    })
    
    // 将 IPCollectFormData 转换为 ProjectFormData（补充默认值）
    const projectFormData = {
      name: formData.value.name?.trim() || '未命名项目',
      industry: formData.value.industry?.trim() || '通用',
      tone: formData.value.tone || '',
      catchphrase: formData.value.catchphrase || '',
      target_audience: formData.value.target_audience || '',
      introduction: formData.value.introduction || '',
      keywords: formData.value.keywords || [],
      industry_understanding: formData.value.industry_understanding || '',
      unique_views: formData.value.unique_views || '',
      target_pains: formData.value.target_pains || '',
      benchmark_accounts: [],
      content_style: '',
      taboos: []
    }
    
    // 使用数据转换工具函数，将表单数据转换为创建请求
    const requestData = formDataToCreateRequest(projectFormData)
    
    // 创建项目（后端会自动生成Master Prompt）
    const project = await createProject(requestData)
    
    // 更新 store 状态
    projectStore.upsertProject(project)
    
    // 设置刷新标记
    projectStore.setNeedRefresh(true)
    
    uni.hideLoading()
    
    // 清理store中的IP收集表单缓存（注入基因库成功后清空）
    projectStore.clearIPCollectFormData()
    
    uni.showToast({
      title: '保存成功',
      icon: 'success'
    })
    
    // 跳转到项目列表页
    setTimeout(() => {
      uni.switchTab({
        url: '/pages/project/index'
      })
    }, 500)
  } catch (error: any) {
    uni.hideLoading()
    console.error('保存项目失败:', error)
    uni.showToast({
      title: error.message || '保存失败，请重试',
      icon: 'none',
      duration: 2000
    })
  } finally {
    isSaving.value = false
  }
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
          // 用户确认
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

.report-page {
  min-height: 100vh;
  background: $bg-light;
  display: flex;
  flex-direction: column;
}

.report-scroll {
  flex: 1;
}

.report-wrapper {
  padding: $spacing-xl;
  padding-bottom: 200rpx;
}

.report-header {
  text-align: center;
  margin-bottom: $spacing-xl;
  
  .report-subtitle {
    display: block;
    font-size: $font-size-xl;
    color: $primary-orange;
    font-weight: 600;
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

.loading-section {
  @include flex-center;
  @include flex-column;
  gap: $spacing-md;
  padding: $spacing-xl;
  
  .loading-text {
    font-size: $font-size-md;
    color: $text-second;
  }
}

.page-footer {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  display: flex;
  gap: $spacing-md;
  padding: $spacing-lg;
  @include safe-area-bottom-padding;
  border-top: 1rpx solid $border-color;
  background: $white;
  box-shadow: 0 -4rpx 12rpx rgba(0, 0, 0, 0.04);
  
  .footer-btn {
    flex: 1;
    height: 88rpx;
    border-radius: $radius-xl;
    @include flex-center;
    gap: $spacing-xs;
    font-size: $font-size-md;
    font-weight: 500;
    transition: all $transition-base;
    
    &.export-btn {
      background: $bg-light;
      color: $primary-orange;
      
      &:active {
        background: rgba($primary-orange, 0.1);
      }
    }
    
    &.save-btn {
      background: linear-gradient(135deg, $primary-orange 0%, $primary-orange-alt 100%);
      color: $white;
      box-shadow: 0 4rpx 12rpx rgba($primary-orange, 0.3);
      
      &:active:not(.disabled) {
        transform: scale(0.98);
      }
      
      &.disabled {
        opacity: 0.7;
        box-shadow: none;
      }
    }
    
    .btn-text {
      font-size: $font-size-md;
    }
  }
}
</style>

