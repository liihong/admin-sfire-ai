<template>
  <view class="qrcode-login-container">
    <!-- 流体弥散背景 -->
    <view class="bg-fluid">
      <view class="fluid-blob fluid-blob-1"></view>
      <view class="fluid-blob fluid-blob-2"></view>
    </view>

    <!-- 火花点缀 -->
    <view class="sparkles">
      <view class="sparkle sparkle-1"></view>
      <view class="sparkle sparkle-2"></view>
      <view class="sparkle sparkle-3"></view>
      <view class="sparkle sparkle-4"></view>
      <view class="sparkle sparkle-5"></view>
      <view class="sparkle sparkle-6"></view>
    </view>

    <!-- Logo 区域 -->
    <view class="logo-section">
      <view class="logo-glass-wrapper">
        <view class="logo-gradient-ball">
          <image class="logo" src="/static/logo.png" mode="aspectFit" />
        </view>
      </view>
      <text class="app-name">火源灵感火花</text>
      <view class="ai-tip-capsule">
        <view class="breathing-dot"></view>
        <text class="ai-tip-text">PC端扫码登录授权</text>
      </view>
    </view>

    <!-- 授权状态区域 -->
    <view class="auth-section">
      <!-- 加载状态 -->
      <view v-if="authStatus === 'loading'" class="status-container">
        <view class="loading-spinner"></view>
        <text class="status-text">正在授权登录...</text>
      </view>

      <!-- 成功状态 -->
      <view v-else-if="authStatus === 'success'" class="status-container">
        <view class="success-icon">✓</view>
        <text class="status-text success-text">授权成功</text>
        <text class="status-tip">请返回PC端继续操作</text>
        <button class="close-btn" @tap="handleCloseMiniProgram">关闭小程序</button>
      </view>

      <!-- 错误状态 -->
      <view v-else-if="authStatus === 'error'" class="status-container">
        <view class="error-icon">✕</view>
        <text class="status-text error-text">{{ errorMessage }}</text>
        <button class="retry-btn" @tap="handleRetry">重试</button>
      </view>
    </view>

    <!-- 底部版权 -->
    <view class="footer">
      <text class="copyright">© 2026 火源AI 版权所有</text>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { onLoad } from '@dcloudio/uni-app'
import { qrcodeLogin } from '@/api/user'
import { wxLogin, exitMiniProgram, getSceneFromOptions } from '@/utils/wechat'

// 页面加载参数类型定义
interface PageLoadOptions {
  scene?: string
  query?: {
    scene?: string
  }
  [key: string]: any
}

// 授权状态：loading-加载中, success-成功, error-失败
const authStatus = ref<'loading' | 'success' | 'error'>('loading')
const errorMessage = ref('')
const scene = ref('')
// 防重复提交标志
const isProcessing = ref(false)

/**
 * 错误码常量定义
 */
const ERROR_CODES = {
  EXPIRED: ['EXPIRED', 'expired', '过期', '已过期'],
  NETWORK_ERROR: ['NETWORK_ERROR', 'timeout', '网络', 'fail', '连接失败'],
  INVALID_SCENE: ['INVALID_SCENE', '无效', 'invalid'],
} as const

/**
 * 解析错误消息，返回用户友好的提示
 */
const parseErrorMessage = (error: any): string => {
  const errorMsg = error.message || error.msg || '授权失败，请重试'
  const errorCode = error.code || error.errcode || ''

  // 使用错误码匹配（优先）
  if (errorCode === 'EXPIRED' || ERROR_CODES.EXPIRED.some(code => errorMsg.includes(code))) {
    return '二维码已过期，请重新扫描'
  }
  
  if (errorCode === 'NETWORK_ERROR' || ERROR_CODES.NETWORK_ERROR.some(code => errorMsg.includes(code))) {
    return '网络连接失败，请检查网络'
  }
  
  if (errorCode === 'INVALID_SCENE' || ERROR_CODES.INVALID_SCENE.some(code => errorMsg.includes(code))) {
    return '二维码无效，请重新扫描'
  }

  // 默认返回原始错误消息
  return errorMsg
}

/**
 * 执行扫码登录授权
 */
const performQrcodeLogin = async () => {
  // 防止重复提交
  if (isProcessing.value) {
    return
  }

  // 检查场景值
  if (!scene.value) {
    authStatus.value = 'error'
    errorMessage.value = '二维码无效，请重新扫描'
    return
  }

  isProcessing.value = true
  authStatus.value = 'loading'
  errorMessage.value = ''

  try {
    // 1. 获取微信登录 code
    const loginResult = await wxLogin()
    if (!loginResult.code) {
      throw new Error('获取登录凭证失败')
    }

    // 2. 调用扫码登录接口
    const response = await qrcodeLogin({
      code: loginResult.code,
      scene: scene.value
    })

    // 3. 检查响应结果
    if (response.code === 200 && response.data?.success) {
      // 授权成功
      authStatus.value = 'success'
    } else {
      // 授权失败
      throw new Error(response.msg || '授权失败，请重试')
    }
  } catch (error: any) {
    console.error('Qrcode login error:', error)
    authStatus.value = 'error'
    errorMessage.value = parseErrorMessage(error)
  } finally {
    isProcessing.value = false
  }
}

/**
 * 重试授权
 */
const handleRetry = () => {
  if (!isProcessing.value) {
    performQrcodeLogin()
  }
}

/**
 * 关闭小程序
 */
const handleCloseMiniProgram = () => {
  exitMiniProgram('/pages/index/index')
}

/**
 * 页面加载时获取场景值并开始授权
 */
onLoad((options: PageLoadOptions) => {
  // 使用工具函数获取场景值，支持多种获取方式
  const sceneValue = getSceneFromOptions(options)
  
  if (sceneValue) {
    scene.value = sceneValue
    // 自动开始授权流程
    performQrcodeLogin()
  } else {
    // 场景值缺失，显示错误
    authStatus.value = 'error'
    errorMessage.value = '二维码无效，请重新扫描'
  }
})
</script>

<style lang="scss" scoped>
@import '@/styles/_variables.scss';
@import '@/styles/_mixins.scss';
@import '@/styles/_animations.scss';

// 页面特定变量
$brand-purple: #9D50FF;
$bg-ultra-light: #FDFEFE;

.qrcode-login-container {
  min-height: 100vh;
  background: $bg-ultra-light;
  @include flex-column;
  position: relative;
  overflow: hidden;
}

.bg-fluid {
  @include fixed-fullscreen;
  pointer-events: none;
  overflow: hidden;
}

.fluid-blob {
  position: absolute;
  border-radius: $radius-circle;
  filter: blur(120rpx);
  opacity: 0.4;
  animation: float-slow 25s ease-in-out infinite;
}

.fluid-blob-1 {
  width: 600rpx;
  height: 600rpx;
  background: radial-gradient(circle, rgba(255, 136, 0, 0.6) 0%, rgba(255, 136, 0, 0.2) 50%, transparent 100%);
  top: -200rpx;
  left: -200rpx;
  animation-delay: 0s;
}

.fluid-blob-2 {
  width: 500rpx;
  height: 500rpx;
  background: radial-gradient(circle, rgba(157, 80, 255, 0.5) 0%, rgba(157, 80, 255, 0.2) 50%, transparent 100%);
  bottom: -150rpx;
  right: -150rpx;
  animation-delay: 5s;
}

.sparkles {
  @include fixed-fullscreen;
  pointer-events: none;
}

.sparkle {
  position: absolute;
  width: 8rpx;
  height: 8rpx;
  background: $brand-orange;
  border-radius: $radius-circle;
  box-shadow: 0 0 12rpx $brand-orange;
  animation: sparkle 3s ease-in-out infinite;
}

.sparkle-1 {
  top: 20%;
  left: 15%;
  animation-delay: 0s;
}

.sparkle-2 {
  top: 35%;
  right: 20%;
  animation-delay: 0.5s;
}

.sparkle-3 {
  top: 50%;
  left: 10%;
  animation-delay: 1s;
}

.sparkle-4 {
  top: 65%;
  right: 15%;
  animation-delay: 1.5s;
}

.sparkle-5 {
  top: 80%;
  left: 25%;
  animation-delay: 2s;
}

.sparkle-6 {
  top: 25%;
  right: 30%;
  animation-delay: 2.5s;
}

.logo-section {
  @include flex-column;
  align-items: center;
  padding-top: 200rpx;
  padding-bottom: 100rpx;
  z-index: $z-index-base;
}

.logo-glass-wrapper {
  width: 200rpx;
  height: 200rpx;
  background: rgba(255, 255, 255, 0.6);
  backdrop-filter: blur(20rpx);
  -webkit-backdrop-filter: blur(20rpx);
  border-radius: $radius-circle;
  border: 2rpx solid rgba(255, 255, 255, 0.8);
  @include flex-center;
  box-shadow: $shadow-lg;
  margin-bottom: $spacing-xl;
  position: relative;
  overflow: hidden;
}

.logo-gradient-ball {
  width: 140rpx;
  height: 140rpx;
  background: linear-gradient(135deg, $brand-orange 0%, $brand-orange-alt 50%, $brand-purple 100%);
  border-radius: $radius-circle;
  box-shadow: inset 0 0 40rpx rgba(255, 255, 255, 0.3);
}

.logo {
  width: 100%;
  height: 100%;
}

.app-name {
  font-size: 56rpx;
  font-weight: 700;
  color: #595968;
  letter-spacing: 12rpx;
  text-shadow: 0 2rpx 8rpx rgba(0, 0, 0, 0.08);
  margin-bottom: $spacing-lg;
}

.ai-tip-capsule {
  @include flex-center-vertical;
  gap: $spacing-sm;
  padding: 12rpx $spacing-md;
  background: rgba(255, 255, 255, 0.7);
  backdrop-filter: blur(10rpx);
  -webkit-backdrop-filter: blur(10rpx);
  border-radius: 50rpx;
  border: 1rpx solid rgba(255, 136, 0, 0.2);
}

.breathing-dot {
  width: 16rpx;
  height: 16rpx;
  background: $brand-orange;
  border-radius: $radius-circle;
  box-shadow: 0 0 12rpx $brand-orange;
  animation: breathing-dot 2s ease-in-out infinite;
}

.ai-tip-text {
  font-size: $font-size-sm;
  color: $text-secondary;
}

.auth-section {
  flex: 1;
  padding: 0 60rpx;
  z-index: $z-index-base;
  @include flex-column;
  align-items: center;
  justify-content: center;
  gap: $spacing-lg;
}

.status-container {
  @include flex-column;
  align-items: center;
  gap: $spacing-md;
  width: 100%;
}

.loading-spinner {
  width: 80rpx;
  height: 80rpx;
  border: 6rpx solid rgba(255, 136, 0, 0.2);
  border-top-color: $brand-orange;
  border-radius: $radius-circle;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.success-icon {
  width: 120rpx;
  height: 120rpx;
  background: linear-gradient(135deg, $brand-orange 0%, $brand-orange-alt 100%);
  border-radius: $radius-circle;
  @include flex-center;
  font-size: 80rpx;
  color: $white;
  font-weight: 700;
  box-shadow: 0 8rpx 24rpx rgba(255, 136, 0, 0.3);
}

.error-icon {
  width: 120rpx;
  height: 120rpx;
  background: rgba(255, 59, 48, 0.1);
  border-radius: $radius-circle;
  @include flex-center;
  font-size: 80rpx;
  color: #ff3b30;
  font-weight: 700;
}

.status-text {
  font-size: $font-size-lg;
  font-weight: 600;
  color: $text-primary;
  text-align: center;
}

.success-text {
  color: $brand-orange;
}

.error-text {
  color: #ff3b30;
}

.status-tip {
  font-size: $font-size-sm;
  color: $text-secondary;
  text-align: center;
  margin-top: $spacing-xs;
}

.close-btn,
.retry-btn {
  width: 100%;
  height: 88rpx;
  background: linear-gradient(135deg, $brand-orange 0%, $brand-orange-alt 100%);
  border-radius: 50rpx;
  @include flex-center;
  color: $white;
  font-size: $font-size-lg;
  font-weight: 600;
  border: none;
  margin-top: $spacing-lg;
  box-shadow: 0 4rpx 16rpx rgba(255, 136, 0, 0.3);
  transition: all $transition-slow ease;
}

.close-btn::after,
.retry-btn::after {
  border: none;
}

.close-btn:active,
.retry-btn:active {
  transform: scale(0.98);
  opacity: 0.9;
}

.retry-btn {
  background: rgba(255, 136, 0, 0.1);
  color: $brand-orange;
  box-shadow: 0 2rpx 8rpx rgba(255, 136, 0, 0.2);
}

.footer {
  padding: 40rpx;
  text-align: center;
  z-index: $z-index-base;
}

.copyright {
  font-size: $font-size-xs;
  color: $text-muted;
}
</style>

