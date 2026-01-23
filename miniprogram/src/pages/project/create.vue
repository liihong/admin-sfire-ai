<template>
  <view class="create-project-page">
    <!-- 顶部装饰背景 -->
    <view class="bg-decoration">
      <view class="decoration-circle circle-1"></view>
      <view class="decoration-circle circle-2"></view>
    </view>

    <!-- 页面头部 -->
    <view class="page-header">
      <view class="header-back" @tap="goBack">
        <text class="back-icon">←</text>
      </view>
      <view class="header-content">
        <text class="header-title">创建新IP</text>
        <text class="header-subtitle">打造专属 IP 人设</text>
      </view>
    </view>

    <!-- 主内容区域 -->
    <scroll-view class="main-content" scroll-y>
      <!-- 🔥 一键采集卡片 -->
      <!-- <view class="magic-import-card">
        <view class="card-header">
          <view class="card-icon">
            <text class="icon-text">🪄</text>
          </view>
          <view class="card-title-area">
            <text class="card-title">一键采集抖音 IP</text>
            <text class="card-desc">已有抖音账号？智能提取人设信息</text>
          </view>
        </view>

        <view class="import-form">
          <view class="input-wrapper">
            <input 
              class="douyin-input"
              v-model="douyinUrl"
              placeholder="粘贴抖音主页链接"
              placeholder-class="input-placeholder"
              :disabled="isCollecting"
            />
            <view 
              class="collect-btn"
              :class="{ disabled: !douyinUrl.trim() || isCollecting }"
              @tap="handleCollect"
            >
              <view class="btn-icon" v-if="!isCollecting">✨</view>
              <view class="loading-icon" v-else></view>
              <text class="btn-text">{{ isCollecting ? '采集中' : '采集' }}</text>
            </view>
          </view>
          
          <view class="collect-status" v-if="collectStatus">
            <view class="status-dot" :class="collectStatusClass"></view>
            <text class="status-text">{{ collectStatus }}</text>
          </view>
        </view>

        <view class="link-tips">
          <text class="tip-text">支持格式：抖音个人主页链接 / 分享链接</text>
        </view>
      </view> -->

      <!-- AI智能填写卡片 -->
      <!-- <view class="ai-fill-card" style="display: block;">
        <view class="card-header">
          <view class="card-icon">
            <text class="icon-text">🤖</text>
          </view>
          <view class="card-title-area">
            <text class="card-title">AI智能填写</text>
            <text class="card-desc">通过对话形式，智能收集IP信息</text>
          </view>
        </view>
        <view 
          class="ai-fill-btn"
          :class="{ disabled: isAICollecting }"
          @tap="handleAICollect">
          <view class="btn-icon" v-if="!isAICollecting">✨</view>
          <view class="loading-icon" v-else></view>
          <text class="btn-text">{{ isAICollecting ? '采集中' : '开始智能填写' }}</text>
        </view>
      </view> -->

      <!-- 分隔线 -->
      <!-- <view class="divider">
        <view class="divider-line"></view>
        <text class="divider-text">或手动填写</text>
        <view class="divider-line"></view>
      </view> -->

      <!-- IP表单 -->
      <view class="project-form">
        <!-- IP头像预览 -->
        <view class="avatar-section">
          <view class="avatar-preview" :style="{ background: avatarColor }">
            <image 
              v-if="avatarUrl" 
              :src="avatarUrl" 
              class="avatar-image"
              mode="aspectFill"
            />
            <text v-else class="avatar-letter">{{ avatarLetter }}</text>
          </view>
          <view class="avatar-info">
            <text class="avatar-hint">IP头像</text>
            <text class="avatar-auto" v-if="avatarUrl">已从抖音导入</text>
          </view>
        </view>

        <!-- IP名称 -->
        <view class="form-item">
          <view class="form-label-row">
            <text class="form-label">IP名称</text>
            <text class="form-required">*</text>
          </view>
          <input 
            class="form-input"
            v-model="formData.name"
            placeholder="如：李医生科普IP"
            :maxlength="30"
          />
        </view>

        <!-- 赛道选择 -->
        <view class="form-item">
          <view class="form-label-row">
            <text class="form-label">所属赛道</text>
          </view>
          <view class="industry-grid">
            <view 
              class="industry-option"
              v-for="industry in industryOptions"
              :key="industry"
              :class="{ selected: formData.industry === industry }"
              @tap="formData.industry = industry"
            >
              <text class="option-text">{{ industry }}</text>
            </view>
          </view>
        </view>

        <!-- IP 简介 -->
        <view class="form-item">
          <view class="form-label-row">
            <text class="form-label">IP 简介</text>
            <text class="form-hint">{{ formData.introduction.length }}/500</text>
          </view>
          <textarea 
            class="form-textarea"
            v-model="formData.introduction"
            placeholder="介绍一下你的 IP 定位和特色..."
            :maxlength="500"
          />
        </view>

        <!-- 语气风格 -->
        <view class="form-item">
          <view class="form-label-row">
            <text class="form-label">语气风格</text>
          </view>
          <view class="tone-grid">
            <view 
              class="tone-option"
              v-for="tone in toneOptions"
              :key="tone"
              :class="{ selected: formData.tone === tone }"
              @tap="formData.tone = tone"
            >
              <text class="option-text">{{ tone }}</text>
            </view>
          </view>
        </view>

        <!-- 口头禅/标签 -->
        <view class="form-item">
          <view class="form-label-row">
            <text class="form-label">人设标签 / 口头禅</text>
          </view>
          <input 
            class="form-input"
            v-model="formData.catchphrase"
            placeholder="如：家人们、听我说、这个很重要"
          />
        </view>

        <!-- 目标受众 -->
        <view class="form-item">
          <view class="form-label-row">
            <text class="form-label">目标受众</text>
          </view>
          <input 
            class="form-input"
            v-model="formData.targetAudience"
            placeholder="如：25-45岁关注健康的职场人群"
          />
        </view>

        <!-- 关键词标签 -->
        <view class="form-item">
          <view class="form-label-row">
            <text class="form-label">常用关键词</text>
            <text class="form-hint">用逗号分隔</text>
          </view>
          <input 
            class="form-input"
            v-model="keywordsInput"
            placeholder="如：健康,养生,科普,干货"
          />
          <view class="tags-preview" v-if="parsedKeywords.length > 0">
            <view class="tag-item" v-for="(kw, idx) in parsedKeywords" :key="idx">
              <text class="tag-text">{{ kw }}</text>
            </view>
          </view>
        </view>
      </view>

      <!-- 底部占位 -->
      <view class="form-footer-spacer"></view>
    </scroll-view>

    <!-- 底部按钮 -->
    <view class="footer-actions">
      <view 
        class="submit-btn"
        :class="{ disabled: !canSubmit || isSubmitting }"
        @tap="handleSubmit"
      >
        <view class="btn-glow"></view>
        <view class="btn-content">
          <text class="btn-icon" v-if="!isSubmitting">🚀</text>
          <view class="loading-spinner" v-else></view>
          <text class="btn-text">{{ isSubmitting ? '创建中...' : '创建IP' }}</text>
        </view>
      </view>
    </view>

    <!-- 采集进度弹窗 -->
    <view class="collect-modal" v-if="showCollectModal">
      <view class="modal-mask"></view>
      <view class="modal-content">
        <view class="modal-icon">
          <view class="magic-animation">
            <text class="magic-emoji">🪄</text>
          </view>
        </view>
        <text class="modal-title">{{ collectModalTitle }}</text>
        <text class="modal-desc">{{ collectModalDesc }}</text>
        <view class="progress-bar">
          <view class="progress-fill" :style="{ width: collectProgress + '%' }"></view>
        </view>
        <text class="progress-text">{{ collectProgress }}%</text>
      </view>
    </view>

    <!-- AI智能填写对话框 -->
    <IPCollectDialog
      :visible="showAIDialog"
      @close="showAIDialog = false"
      @complete="handleAIComplete"
    />
  </view>
</template>

<script setup lang="ts">
import { ref, computed, reactive } from 'vue'
import { useProjectStore, INDUSTRY_OPTIONS, TONE_OPTIONS } from '@/stores/project'
import { request } from '@/utils/request'
import { IPCollectDialog } from '@/components/business/dialog'
import { compressIPInfo, createProject } from '@/api/project'

// Store
const projectStore = useProjectStore()

// 采集状态
const douyinUrl = ref('')
const isCollecting = ref(false)
const collectStatus = ref('')
const showCollectModal = ref(false)
const collectModalTitle = ref('')
const collectModalDesc = ref('')
const collectProgress = ref(0)

// 表单数据
const formData = reactive({
  name: '',
  industry: '通用',
  introduction: '',
  tone: '专业亲和',
  catchphrase: '',
  targetAudience: ''
})

// 头像相关
const avatarUrl = ref('')
const avatarColor = ref('#FF8800')

// 关键词输入
const keywordsInput = ref('')

// 提交状态
const isSubmitting = ref(false)

// AI智能填写状态
const isAICollecting = ref(false)
const showAIDialog = ref(false)

// 选项数据
const industryOptions = INDUSTRY_OPTIONS.slice(0, 12)
const toneOptions = TONE_OPTIONS

// 计算属性
const avatarLetter = computed(() => {
  return formData.name ? formData.name[0].toUpperCase() : 'P'
})

const collectStatusClass = computed(() => {
  if (collectStatus.value.includes('成功')) return 'success'
  if (collectStatus.value.includes('失败')) return 'error'
  return 'loading'
})

const parsedKeywords = computed(() => {
  if (!keywordsInput.value.trim()) return []
  return keywordsInput.value
    .split(/[,，、]/)
    .map(k => k.trim())
    .filter(k => k.length > 0)
    .slice(0, 10)
})

const canSubmit = computed(() => {
  return formData.name.trim().length > 0
})

// 返回上一页
function goBack() {
  uni.navigateBack({
    fail: () => {
      uni.switchTab({ url: '/pages/project/list' })
    }
  })
}

// 处理采集
async function handleCollect() {
  if (!douyinUrl.value.trim() || isCollecting.value) return
  
  isCollecting.value = true
  showCollectModal.value = true
  collectProgress.value = 0
  collectModalTitle.value = '正在连接 Tikhub...'
  collectModalDesc.value = '准备获取抖音账号信息'
  
  try {
    // 模拟进度更新
    const progressInterval = setInterval(() => {
      if (collectProgress.value < 30) {
        collectProgress.value += 5
      }
    }, 200)
    
    // 阶段1: 连接 Tikhub
    await delay(1000)
    collectProgress.value = 30
    collectModalTitle.value = '正在获取账号信息...'
    collectModalDesc.value = '读取抖音主页数据'
    
    clearInterval(progressInterval)
    
    // 阶段2: 获取用户信息
    const progressInterval2 = setInterval(() => {
      if (collectProgress.value < 60) {
        collectProgress.value += 3
      }
    }, 200)
    
    // 调用后端 API
    const response = await request<{
      success: boolean
      data: {
        nickname: string
        signature: string
        avatar_url: string
        industry_guess: string
        keywords: string[]
        tone_guess: string
        target_audience_guess: string
      }
      message?: string
    }>({
      url: '/api/v1/client/tikhub/analyze-douyin',
      method: 'POST',
      data: {
        url: douyinUrl.value.trim()
      }
    })
    
    clearInterval(progressInterval2)
    
    if (response.success && response.data) {
      // 阶段3: 分析内容
      collectProgress.value = 70
      collectModalTitle.value = '正在分析视频内容...'
      collectModalDesc.value = '智能提取人设特征'
      
      await delay(1500)
      
      collectProgress.value = 90
      collectModalTitle.value = '整理人设信息...'
      collectModalDesc.value = '即将完成'
      
      await delay(500)
      
      collectProgress.value = 100
      
      // 自动填充表单
      const data = response.data
      formData.name = data.nickname || formData.name
      formData.introduction = data.signature || formData.introduction
      formData.industry = data.industry_guess || formData.industry
      formData.tone = data.tone_guess || formData.tone
      formData.targetAudience = data.target_audience_guess || formData.targetAudience
      
      if (data.keywords && data.keywords.length > 0) {
        keywordsInput.value = data.keywords.join('、')
      }
      
      if (data.avatar_url) {
        avatarUrl.value = data.avatar_url
      }
      
      await delay(300)
      showCollectModal.value = false
      collectStatus.value = '✓ 采集成功，请微调后保存'
      
      uni.showToast({
        title: 'IP 画像提取成功',
        icon: 'success'
      })
    } else {
      throw new Error(response.message || '采集失败')
    }
  } catch (error: any) {
    console.error('Collect failed:', error)
    showCollectModal.value = false
    collectStatus.value = '✗ 采集失败，请检查链接'
    
    uni.showToast({
      title: error.message || '采集失败',
      icon: 'none'
    })
  } finally {
    isCollecting.value = false
  }
}

// 提交创建
async function handleSubmit() {
  if (!canSubmit.value || isSubmitting.value) return
  
  isSubmitting.value = true
  
  try {
    // 构建请求数据（扁平化字段）
    const requestData: any = {
      name: formData.name.trim(),
      industry: formData.industry
    }

    // 添加可选的人设字段
    if (formData.introduction) {
      requestData.introduction = formData.introduction
    }
    if (formData.tone) {
      requestData.tone = formData.tone
    }
    if (formData.targetAudience) {
      requestData.target_audience = formData.targetAudience
    }
    if (formData.catchphrase) {
      requestData.catchphrase = formData.catchphrase
    }
    if (parsedKeywords.value.length > 0) {
      requestData.keywords = parsedKeywords.value
    }

    // 调用 API
    const response = await request<{
      project: any
    }>({
      url: '/api/v1/client/projects',
      method: 'POST',
      data: requestData
    })
    
    if (response.code === 200 && response.data?.project) {
      uni.showToast({
        title: '创建成功',
        icon: 'success'
      })

      // 跳转到项目列表页
      setTimeout(() => {
        uni.switchTab({
          url: '/pages/project/list'
        })
      }, 500)
    } else {
      throw new Error(response.msg || '创建失败')
    }
  } catch (error: any) {
    console.error('Submit failed:', error)
    uni.showToast({
      title: error.message || '创建失败，请重试',
      icon: 'none'
    })
  } finally {
    isSubmitting.value = false
  }
}

// 处理AI智能填写
function handleAICollect() {
  if (isAICollecting.value) return
  showAIDialog.value = true
}

// 处理AI采集完成
async function handleAIComplete(collectedInfo: any) {
  isAICollecting.value = true
  
  try {
    // 调用压缩接口
    const compressResponse = await compressIPInfo({
      raw_info: collectedInfo
    })
    
    const compressed = compressResponse.compressed_info
    
    // 填充表单
    if (compressed.name) {
      formData.name = compressed.name
    }
    if (compressed.industry) {
      formData.industry = compressed.industry
    }
    if (compressed.introduction) {
      formData.introduction = compressed.introduction
    }
    if (compressed.tone) {
      formData.tone = compressed.tone
    }
    if (compressed.target_audience) {
      formData.targetAudience = compressed.target_audience
    }
    if (compressed.catchphrase) {
      formData.catchphrase = compressed.catchphrase
    }
    if (compressed.keywords && compressed.keywords.length > 0) {
      keywordsInput.value = compressed.keywords.join('、')
    }
    
    uni.showToast({
      title: 'AI智能填写完成',
      icon: 'success'
    })
  } catch (error: any) {
    console.error('AI压缩失败:', error)
    uni.showToast({
      title: error.message || '处理失败',
      icon: 'none'
    })
  } finally {
    isAICollecting.value = false
  }
}

// 工具函数
function delay(ms: number) {
  return new Promise(resolve => setTimeout(resolve, ms))
}
</script>

<style lang="scss" scoped>
.create-project-page {
  min-height: 100vh;
  background: #F5F7FA;
  position: relative;
  overflow: hidden;
}

// 背景装饰
.bg-decoration {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 500rpx;
  pointer-events: none;
  overflow: hidden;
  
  .decoration-circle {
    position: absolute;
    border-radius: 50%;
    opacity: 0.6;
  }
  
  .circle-1 {
    width: 400rpx;
    height: 400rpx;
    background: linear-gradient(135deg, rgba(249, 115, 22, 0.12) 0%, rgba(249, 115, 22, 0.03) 100%);
    top: -150rpx;
    right: -100rpx;
  }
  
  .circle-2 {
    width: 250rpx;
    height: 250rpx;
    background: linear-gradient(135deg, rgba(59, 130, 246, 0.1) 0%, rgba(59, 130, 246, 0.02) 100%);
    top: 200rpx;
    left: -80rpx;
  }
}

// 页面头部
.page-header {
  position: relative;
  z-index: 10;
  padding: 60rpx 32rpx 32rpx;
  display: flex;
  align-items: flex-start;
  gap: 20rpx;
  
  .header-back {
    width: 72rpx;
    height: 72rpx;
    background: rgba(255, 255, 255, 0.9);
    backdrop-filter: blur(10px);
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    box-shadow: 0 4rpx 16rpx rgba(0, 0, 0, 0.06);
    
    .back-icon {
      font-size: 36rpx;
      color: #333;
    }
  }
  
  .header-content {
    flex: 1;
    padding-top: 8rpx;
  }
  
  .header-title {
    font-size: 40rpx;
    font-weight: 700;
    color: #1a1a2e;
    display: block;
    margin-bottom: 8rpx;
  }
  
  .header-subtitle {
    font-size: 26rpx;
    color: #666;
    display: block;
  }
}

// 主内容区域
.main-content {
  position: relative;
  z-index: 10;
  height: calc(100vh - 280rpx);
  padding: 0 32rpx;
}

// ========== 一键采集卡片 ==========
.magic-import-card {
  background: linear-gradient(135deg, #FFF7ED 0%, #FFEDD5 100%);
  border-radius: 28rpx;
  padding: 32rpx;
  margin-bottom: 32rpx;
  border: 2rpx solid rgba(249, 115, 22, 0.2);
  box-shadow: 0 8rpx 32rpx rgba(249, 115, 22, 0.1);
}

// ========== AI智能填写卡片 ==========
.ai-fill-card {
  background: linear-gradient(135deg, #EEF2FF 0%, #E0E7FF 100%);
  border-radius: 28rpx;
  padding: 32rpx;
  margin-bottom: 32rpx;
  border: 2rpx solid rgba(59, 130, 246, 0.2);
  box-shadow: 0 8rpx 32rpx rgba(59, 130, 246, 0.1);
  
  .card-header {
    display: flex;
    align-items: center;
    gap: 20rpx;
    margin-bottom: 24rpx;
  }
  
  .card-icon {
    width: 72rpx;
    height: 72rpx;
    background: linear-gradient(135deg, #3B82F6 0%, #60A5FA 100%);
    border-radius: 20rpx;
    display: flex;
    align-items: center;
    justify-content: center;
    box-shadow: 0 4rpx 16rpx rgba(59, 130, 246, 0.3);
    
    .icon-text {
      font-size: 36rpx;
    }
  }
  
  .card-title-area {
    flex: 1;
  }
  
  .card-title {
    font-size: 32rpx;
    font-weight: 600;
    color: #1E40AF;
    display: block;
    margin-bottom: 4rpx;
  }
  
  .card-desc {
    font-size: 24rpx;
    color: #3B82F6;
    opacity: 0.8;
  }
  
  .ai-fill-btn {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 12rpx;
    height: 88rpx;
    background: linear-gradient(135deg, #3B82F6 0%, #60A5FA 100%);
    border-radius: 20rpx;
    box-shadow: 0 4rpx 16rpx rgba(59, 130, 246, 0.25);
    
    &.disabled {
      background: #E5E7EB;
      box-shadow: none;
      
      .btn-text {
        color: #9CA3AF;
      }
    }
    
    &:active:not(.disabled) {
      transform: scale(0.98);
    }
    
    .btn-icon {
      font-size: 32rpx;
    }
    
    .btn-text {
      font-size: 30rpx;
      font-weight: 600;
      color: #fff;
    }
    
    .loading-icon {
      width: 32rpx;
      height: 32rpx;
      border: 3rpx solid rgba(255, 255, 255, 0.3);
      border-top-color: #fff;
      border-radius: 50%;
      animation: spin 0.8s linear infinite;
    }
  }
}

.import-form {
  .input-wrapper {
    display: flex;
    gap: 16rpx;
    background: #fff;
    border-radius: 16rpx;
    padding: 8rpx;
    box-shadow: 0 2rpx 8rpx rgba(0, 0, 0, 0.04);
  }
  
  .douyin-input {
    flex: 1;
    height: 72rpx;
    padding: 0 20rpx;
    font-size: 28rpx;
    color: #333;
    background: transparent;
  }
  
  .input-placeholder {
    color: #999;
  }
  
  .collect-btn {
    display: flex;
    align-items: center;
    gap: 8rpx;
    padding: 0 28rpx;
    height: 72rpx;
    background: linear-gradient(135deg, #F97316 0%, #FB923C 100%);
    border-radius: 12rpx;
    box-shadow: 0 4rpx 12rpx rgba(249, 115, 22, 0.25);
    
    &.disabled {
      background: #E5E7EB;
      box-shadow: none;
      
      .btn-text {
        color: #9CA3AF;
      }
    }
    
    &:active:not(.disabled) {
      transform: scale(0.98);
    }
    
    .btn-icon {
      font-size: 28rpx;
    }
    
    .btn-text {
      font-size: 28rpx;
      font-weight: 600;
      color: #fff;
    }
    
    .loading-icon {
      width: 28rpx;
      height: 28rpx;
      border: 3rpx solid rgba(255, 255, 255, 0.3);
      border-top-color: #fff;
      border-radius: 50%;
      animation: spin 0.8s linear infinite;
    }
  }
}

.collect-status {
  display: flex;
  align-items: center;
  gap: 12rpx;
  margin-top: 16rpx;
  padding: 0 8rpx;
  
  .status-dot {
    width: 12rpx;
    height: 12rpx;
    border-radius: 50%;
    
    &.success {
      background: #22C55E;
    }
    
    &.error {
      background: #EF4444;
    }
    
    &.loading {
      background: #F97316;
      animation: pulse 1s infinite;
    }
  }
  
  .status-text {
    font-size: 24rpx;
    color: #78716C;
  }
}

.link-tips {
  margin-top: 16rpx;
  
  .tip-text {
    font-size: 22rpx;
    color: #A8A29E;
  }
}

// ========== 分隔线 ==========
.divider {
  display: flex;
  align-items: center;
  gap: 20rpx;
  margin: 32rpx 0;
  
  .divider-line {
    flex: 1;
    height: 1rpx;
    background: linear-gradient(90deg, transparent, #E5E7EB, transparent);
  }
  
  .divider-text {
    font-size: 24rpx;
    color: #9CA3AF;
  }
}

// ========== IP表单 ==========
.project-form {
  background: rgba(255, 255, 255, 0.9);
  backdrop-filter: blur(20px);
  border-radius: 28rpx;
  padding: 32rpx;
  box-shadow: 0 4rpx 24rpx rgba(0, 0, 0, 0.04);
}

// 头像区域
.avatar-section {
  display: flex;
  align-items: center;
  gap: 24rpx;
  padding-bottom: 32rpx;
  margin-bottom: 32rpx;
  border-bottom: 1rpx solid #F3F4F6;
  
  .avatar-preview {
    width: 120rpx;
    height: 120rpx;
    border-radius: 28rpx;
    display: flex;
    align-items: center;
    justify-content: center;
    overflow: hidden;
    
    .avatar-image {
      width: 100%;
      height: 100%;
    }
    
    .avatar-letter {
      font-size: 48rpx;
      font-weight: 700;
      color: #fff;
    }
  }
  
  .avatar-info {
    .avatar-hint {
      font-size: 28rpx;
      color: #333;
      display: block;
      margin-bottom: 8rpx;
    }
    
    .avatar-auto {
      font-size: 24rpx;
      color: #22C55E;
    }
  }
}

// 表单项
.form-item {
  margin-bottom: 28rpx;
  
  .form-label-row {
    display: flex;
    align-items: center;
    gap: 8rpx;
    margin-bottom: 16rpx;
  }
  
  .form-label {
    font-size: 28rpx;
    font-weight: 500;
    color: #333;
  }
  
  .form-required {
    font-size: 28rpx;
    color: #EF4444;
  }
  
  .form-hint {
    font-size: 24rpx;
    color: #9CA3AF;
    margin-left: auto;
  }
  
  .form-input {
    width: 100%;
    height: 88rpx;
    background: #F5F7FA;
    border-radius: 16rpx;
    padding: 0 24rpx;
    font-size: 30rpx;
    color: #333;
    border: 2rpx solid transparent;
    
    &:focus {
      border-color: #3B82F6;
      background: #fff;
    }
  }
  
  .form-textarea {
    width: 100%;
    height: 180rpx;
    background: #F5F7FA;
    border-radius: 16rpx;
    padding: 20rpx 24rpx;
    font-size: 28rpx;
    color: #333;
    line-height: 1.6;
    border: 2rpx solid transparent;
    
    &:focus {
      border-color: #3B82F6;
      background: #fff;
    }
  }
}

// 行业选择网格
.industry-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12rpx;
  
  .industry-option {
    padding: 18rpx 8rpx;
    background: #F5F7FA;
    border-radius: 12rpx;
    text-align: center;
    border: 2rpx solid transparent;
    transition: all 0.2s ease;
    
    &.selected {
      background: linear-gradient(135deg, #EEF2FF 0%, #E0E7FF 100%);
      border-color: #3B82F6;
      
      .option-text {
        color: #3B82F6;
        font-weight: 500;
      }
    }
    
    .option-text {
      font-size: 24rpx;
      color: #666;
    }
  }
}

// 语气风格选择
.tone-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12rpx;
  
  .tone-option {
    padding: 18rpx 8rpx;
    background: #F5F7FA;
    border-radius: 12rpx;
    text-align: center;
    border: 2rpx solid transparent;
    transition: all 0.2s ease;
    
    &.selected {
      background: linear-gradient(135deg, #FEF3C7 0%, #FDE68A 100%);
      border-color: #F59E0B;
      
      .option-text {
        color: #B45309;
        font-weight: 500;
      }
    }
    
    .option-text {
      font-size: 24rpx;
      color: #666;
    }
  }
}

// 标签预览
.tags-preview {
  display: flex;
  flex-wrap: wrap;
  gap: 12rpx;
  margin-top: 16rpx;
  
  .tag-item {
    padding: 8rpx 20rpx;
    background: linear-gradient(135deg, #EEF2FF 0%, #E0E7FF 100%);
    border-radius: 20rpx;
    
    .tag-text {
      font-size: 24rpx;
      color: #4F46E5;
    }
  }
}

// 底部占位
.form-footer-spacer {
  height: 180rpx;
}

// ========== 底部按钮 ==========
.footer-actions {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  padding: 24rpx 32rpx;
  padding-bottom: calc(24rpx + env(safe-area-inset-bottom));
  background: linear-gradient(180deg, transparent 0%, #F5F7FA 30%);
  z-index: 100;
  
  .submit-btn {
    position: relative;
    height: 100rpx;
    background: linear-gradient(135deg, #3B82F6 0%, #60A5FA 100%);
    border-radius: 50rpx;
    display: flex;
    align-items: center;
    justify-content: center;
    box-shadow: 0 8rpx 32rpx rgba(59, 130, 246, 0.35);
    overflow: hidden;
    
    &.disabled {
      background: #E5E7EB;
      box-shadow: none;
      
      .btn-text {
        color: #9CA3AF;
      }
    }
    
    &:active:not(.disabled) {
      transform: scale(0.98);
    }
    
    .btn-glow {
      position: absolute;
      top: 0;
      left: -100%;
      width: 100%;
      height: 100%;
      background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.3), transparent);
      animation: btnGlow 3s infinite;
    }
    
    .btn-content {
      display: flex;
      align-items: center;
      gap: 12rpx;
      z-index: 1;
      
      .btn-icon {
        font-size: 36rpx;
      }
      
      .btn-text {
        font-size: 32rpx;
        font-weight: 600;
        color: #fff;
      }
      
      .loading-spinner {
        width: 36rpx;
        height: 36rpx;
        border: 4rpx solid rgba(255, 255, 255, 0.3);
        border-top-color: #fff;
        border-radius: 50%;
        animation: spin 0.8s linear infinite;
      }
    }
  }
}

// ========== 采集进度弹窗 ==========
.collect-modal {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 2000;
  display: flex;
  align-items: center;
  justify-content: center;
  
  .modal-mask {
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(0, 0, 0, 0.6);
    backdrop-filter: blur(4px);
  }
  
  .modal-content {
    position: relative;
    width: 560rpx;
    background: #fff;
    border-radius: 32rpx;
    padding: 48rpx;
    display: flex;
    flex-direction: column;
    align-items: center;
    animation: scaleIn 0.3s ease;
  }
  
  .modal-icon {
    margin-bottom: 24rpx;
    
    .magic-animation {
      width: 120rpx;
      height: 120rpx;
      background: linear-gradient(135deg, #FEF3C7 0%, #FDE68A 100%);
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
      animation: float 2s ease-in-out infinite;
      
      .magic-emoji {
        font-size: 56rpx;
        animation: wiggle 1s ease-in-out infinite;
      }
    }
  }
  
  .modal-title {
    font-size: 32rpx;
    font-weight: 600;
    color: #1a1a2e;
    margin-bottom: 12rpx;
  }
  
  .modal-desc {
    font-size: 26rpx;
    color: #666;
    margin-bottom: 32rpx;
  }
  
  .progress-bar {
    width: 100%;
    height: 12rpx;
    background: #F3F4F6;
    border-radius: 6rpx;
    overflow: hidden;
    
    .progress-fill {
      height: 100%;
      background: linear-gradient(90deg, #F97316, #FB923C);
      border-radius: 6rpx;
      transition: width 0.3s ease;
    }
  }
  
  .progress-text {
    font-size: 24rpx;
    color: #F97316;
    margin-top: 16rpx;
    font-weight: 500;
  }
}

// ========== 动画 ==========
@keyframes spin {
  to { transform: rotate(360deg); }
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

@keyframes btnGlow {
  0% { left: -100%; }
  50%, 100% { left: 100%; }
}

@keyframes scaleIn {
  from {
    opacity: 0;
    transform: scale(0.9);
  }
  to {
    opacity: 1;
    transform: scale(1);
  }
}

@keyframes float {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-10rpx); }
}

@keyframes wiggle {
  0%, 100% { transform: rotate(-5deg); }
  50% { transform: rotate(5deg); }
}
</style>

