<template>
  <view class="login-container">
    <!-- 背景装饰 -->
    <view class="bg-decoration">
      <view class="circle circle-1"></view>
      <view class="circle circle-2"></view>
      <view class="circle circle-3"></view>
    </view>

    <!-- Logo 区域 -->
    <view class="logo-section">
      <view class="logo-wrapper">
        <image class="logo" src="/static/logo.png" mode="aspectFit" />
      </view>
      <text class="app-name">火源文案</text>
      <text class="app-slogan">AI 驱动的智能创作平台</text>
    </view>

    <!-- 登录按钮区域 -->
    <view class="login-section">
      <view class="login-card">
        <view class="card-header">
          <text class="card-title">欢迎使用</text>
          <text class="card-subtitle">使用微信手机号快速登录</text>
        </view>

        <!-- 手机号一键登录按钮 -->
        <button
          class="login-btn"
          :class="{ disabled: !isAgreed }"
          open-type="getPhoneNumber"
          @getphonenumber="handleGetPhoneNumber"
        >
          <view class="btn-content">
            <text class="btn-icon">📱</text>
            <text class="btn-text">手机号一键登录</text>
          </view>
        </button>

        <view class="divider">
          <view class="divider-line"></view>
          <text class="divider-text">安全快捷</text>
          <view class="divider-line"></view>
        </view>

        <view class="login-tips">
          <text class="tip-item">🔒 微信官方授权，安全可靠</text>
          <text class="tip-item">⚡ 一键登录，无需验证码</text>
        </view>
      </view>
    </view>

    <!-- 隐私协议区域 -->
    <view class="agreement-section">
      <view class="agreement-wrapper" @tap="toggleAgreement">
        <view class="checkbox" :class="{ checked: isAgreed }">
          <text v-if="isAgreed" class="check-icon">✓</text>
        </view>
        <view class="agreement-text">
          <text class="normal-text">我已阅读并同意</text>
          <text class="link-text" @tap.stop="openUserAgreement">《用户协议》</text>
          <text class="normal-text">与</text>
          <text class="link-text" @tap.stop="openPrivacyPolicy">《隐私政策》</text>
        </view>
      </view>
    </view>

    <!-- 底部版权 -->
    <view class="footer">
      <text class="copyright">© 2026 火源文案 版权所有</text>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { post } from '@/utils/request'

const authStore = useAuthStore()

// 是否同意协议
const isAgreed = ref(false)

// 是否正在登录
const isLogging = ref(false)

/**
 * 切换协议同意状态
 */
const toggleAgreement = () => {
  isAgreed.value = !isAgreed.value
}

/**
 * 处理获取手机号
 */
const handleGetPhoneNumber = async (e: any) => {
  console.log('getPhoneNumber event:', e)
  
  // 检查是否同意协议
  if (!isAgreed.value) {
    uni.showToast({
      title: '请先同意隐私协议',
      icon: 'none',
      duration: 2000
    })
    return
  }
  
  // 检查是否用户拒绝授权
  if (e.detail.errMsg && e.detail.errMsg.includes('deny')) {
    uni.showToast({
      title: '您已取消授权',
      icon: 'none',
      duration: 2000
    })
    return
  }
  
  // 检查是否获取到 code
  const phoneCode = e.detail.code
  if (!phoneCode) {
    uni.showToast({
      title: '获取手机号失败，请重试',
      icon: 'none',
      duration: 2000
    })
    return
  }
  
  // 防止重复点击
  if (isLogging.value) return
  isLogging.value = true
  
  try {
    uni.showLoading({
      title: '登录中...',
      mask: true
    })
    
    // 获取微信登录 code
    const loginResult = await wxLogin()
    
    if (!loginResult.code) {
      throw new Error('获取登录凭证失败')
    }
    
    // 调用后端登录接口
    const response = await post<{
      token: string
      is_new_user: boolean
      user_info?: {
        openid: string
        nickname: string
        avatarUrl: string
      }
    }>('/api/v1/client/auth/login', {
      code: loginResult.code,
      phone_code: phoneCode
    })
    
    uni.hideLoading()
    
    if (response.success && response.data) {
      // 保存 Token
      authStore.setToken(response.data.token)
      
      // 保存用户信息
      if (response.data.user_info) {
        authStore.setUserInfo({
          openid: response.data.user_info.openid,
          nickname: response.data.user_info.nickname || '',
          avatarUrl: response.data.user_info.avatarUrl || '/static/default-avatar.png'
        })
      }
      
      uni.showToast({
        title: '登录成功',
        icon: 'success',
        duration: 1500
      })
      
      // 根据是否新用户决定跳转
      setTimeout(() => {
        if (response.data?.is_new_user) {
          // 新用户，跳转到完善资料页
          uni.redirectTo({
            url: '/pages/login/profile'
          })
        } else {
          // 老用户，跳转到首页
          uni.switchTab({
            url: '/pages/index/index'
          })
        }
      }, 1500)
    } else {
      throw new Error(response.message || '登录失败')
    }
  } catch (error: any) {
    uni.hideLoading()
    console.error('Login error:', error)
    
    // 开发环境模拟登录成功
    // #ifdef H5
    mockLogin()
    return
    // #endif
    
    uni.showToast({
      title: error.message || '登录失败，请重试',
      icon: 'none',
      duration: 2000
    })
  } finally {
    isLogging.value = false
  }
}

/**
 * 微信登录获取 code
 */
function wxLogin(): Promise<{ code: string }> {
  return new Promise((resolve, reject) => {
    // #ifdef MP-WEIXIN
    uni.login({
      provider: 'weixin',
      success: (res) => {
        if (res.code) {
          resolve({ code: res.code })
        } else {
          reject(new Error('获取登录凭证失败'))
        }
      },
      fail: (err) => {
        console.error('uni.login failed:', err)
        reject(err)
      }
    })
    // #endif
    
    // #ifndef MP-WEIXIN
    // 非微信环境，使用 mock code
    console.log('[Dev] Using mock login code')
    resolve({ code: `mock_${Date.now()}` })
    // #endif
  })
}

/**
 * 开发环境模拟登录
 */
const mockLogin = () => {
  console.log('[Dev] Mock login')
  
  // 模拟 Token
  const mockToken = `mock_token_${Date.now()}`
  authStore.setToken(mockToken)
  
  // 模拟用户信息
  authStore.setUserInfo({
    openid: `mock_openid_${Date.now()}`,
    nickname: '',
    avatarUrl: '/static/default-avatar.png'
  })
  
  uni.showToast({
    title: '登录成功',
    icon: 'success',
    duration: 1500
  })
  
  // 跳转到完善资料页（模拟新用户）
  setTimeout(() => {
    uni.redirectTo({
      url: '/pages/login/profile'
    })
  }, 1500)
}

/**
 * 打开用户协议
 */
const openUserAgreement = () => {
  uni.navigateTo({
    url: '/pages/agreement/user'
  })
}

/**
 * 打开隐私政策
 */
const openPrivacyPolicy = () => {
  uni.navigateTo({
    url: '/pages/agreement/privacy'
  })
}
</script>

<style lang="scss" scoped>
.login-container {
  min-height: 100vh;
  background: linear-gradient(180deg, #667eea 0%, #764ba2 50%, #f5f7fa 100%);
  display: flex;
  flex-direction: column;
  position: relative;
  overflow: hidden;
}

/* 背景装饰 */
.bg-decoration {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  pointer-events: none;
  overflow: hidden;
  
  .circle {
    position: absolute;
    border-radius: 50%;
    background: rgba(255, 255, 255, 0.1);
  }
  
  .circle-1 {
    width: 400rpx;
    height: 400rpx;
    top: -100rpx;
    right: -100rpx;
  }
  
  .circle-2 {
    width: 300rpx;
    height: 300rpx;
    top: 200rpx;
    left: -150rpx;
  }
  
  .circle-3 {
    width: 200rpx;
    height: 200rpx;
    bottom: 400rpx;
    right: -50rpx;
  }
}

/* Logo 区域 */
.logo-section {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding-top: 180rpx;
  padding-bottom: 80rpx;
  z-index: 1;
  
  .logo-wrapper {
    width: 180rpx;
    height: 180rpx;
    background: rgba(255, 255, 255, 0.95);
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    box-shadow: 0 16rpx 48rpx rgba(0, 0, 0, 0.2);
    margin-bottom: 32rpx;
  }
  
  .logo {
    width: 120rpx;
    height: 120rpx;
  }
  
  .app-name {
    font-size: 56rpx;
    font-weight: 700;
    color: #ffffff;
    letter-spacing: 8rpx;
    text-shadow: 0 4rpx 16rpx rgba(0, 0, 0, 0.2);
    margin-bottom: 16rpx;
  }
  
  .app-slogan {
    font-size: 28rpx;
    color: rgba(255, 255, 255, 0.85);
    letter-spacing: 2rpx;
  }
}

/* 登录区域 */
.login-section {
  flex: 1;
  padding: 0 40rpx;
  z-index: 1;
  
  .login-card {
    background: #ffffff;
    border-radius: 32rpx;
    padding: 48rpx 40rpx;
    box-shadow: 0 16rpx 64rpx rgba(0, 0, 0, 0.15);
  }
  
  .card-header {
    text-align: center;
    margin-bottom: 48rpx;
    
    .card-title {
      display: block;
      font-size: 44rpx;
      font-weight: 700;
      color: #1a1a2e;
      margin-bottom: 12rpx;
    }
    
    .card-subtitle {
      font-size: 28rpx;
      color: #666666;
    }
  }
}

/* 登录按钮 */
.login-btn {
  width: 100%;
  height: 100rpx;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 50rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  border: none;
  padding: 0;
  margin: 0;
  box-shadow: 0 8rpx 32rpx rgba(102, 126, 234, 0.4);
  transition: all 0.3s ease;
  
  &::after {
    border: none;
  }
  
  &:active {
    transform: scale(0.98);
    opacity: 0.9;
  }
  
  &.disabled {
    opacity: 0.6;
  }
  
  .btn-content {
    display: flex;
    align-items: center;
    gap: 16rpx;
  }
  
  .btn-icon {
    font-size: 40rpx;
  }
  
  .btn-text {
    font-size: 32rpx;
    font-weight: 600;
    color: #ffffff;
    letter-spacing: 2rpx;
  }
}

/* 分隔线 */
.divider {
  display: flex;
  align-items: center;
  margin: 40rpx 0;
  
  .divider-line {
    flex: 1;
    height: 1rpx;
    background: linear-gradient(90deg, transparent, #e0e0e0, transparent);
  }
  
  .divider-text {
    padding: 0 24rpx;
    font-size: 24rpx;
    color: #999999;
  }
}

/* 登录提示 */
.login-tips {
  display: flex;
  flex-direction: column;
  gap: 16rpx;
  
  .tip-item {
    font-size: 26rpx;
    color: #666666;
    text-align: center;
  }
}

/* 协议区域 */
.agreement-section {
  padding: 40rpx;
  z-index: 1;
  
  .agreement-wrapper {
    display: flex;
    align-items: flex-start;
    justify-content: center;
    gap: 16rpx;
  }
  
  .checkbox {
    width: 40rpx;
    height: 40rpx;
    border: 3rpx solid #cccccc;
    border-radius: 8rpx;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
    transition: all 0.3s ease;
    margin-top: 4rpx;
    
    &.checked {
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      border-color: #667eea;
    }
    
    .check-icon {
      font-size: 24rpx;
      color: #ffffff;
      font-weight: 700;
    }
  }
  
  .agreement-text {
    flex: 1;
    font-size: 26rpx;
    line-height: 1.6;
    text-align: center;
  }
  
  .normal-text {
    color: #666666;
  }
  
  .link-text {
    color: #667eea;
    font-weight: 500;
  }
}

/* 底部版权 */
.footer {
  padding: 40rpx;
  text-align: center;
  z-index: 1;
  
  .copyright {
    font-size: 22rpx;
    color: #999999;
  }
}
</style>


