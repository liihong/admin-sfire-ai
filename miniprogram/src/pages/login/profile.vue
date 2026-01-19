<template>
  <view class="profile-container">
    <!-- 顶部背景 -->
    <view class="header-bg">
      <view class="bg-circle circle-1"></view>
      <view class="bg-circle circle-2"></view>
    </view>

    <!-- 页面标题 -->
    <view class="page-header">
      <text class="header-title">完善个人资料</text>
      <text class="header-subtitle">让我们更好地为您服务</text>
    </view>

    <!-- 表单卡片 -->
    <view class="form-card">
      <!-- 头像选择 -->
      <view class="form-item avatar-item">
        <text class="form-label">头像</text>
        <view class="avatar-picker">
          <button 
            class="avatar-btn" 
            open-type="chooseAvatar" 
            @chooseavatar="handleChooseAvatar"
          >
            <image 
              class="avatar-image" 
              :src="formData.avatarUrl || '/static/default-avatar.png'" 
              mode="aspectFill"
            />
            <view class="avatar-overlay">
              <text class="overlay-icon">📷</text>
            </view>
          </button>
          <text class="avatar-tip">点击更换头像</text>
        </view>
      </view>

      <!-- 昵称输入 -->
      <view class="form-item">
        <text class="form-label">昵称</text>
        <view class="input-wrapper">
          <input
            class="form-input"
            type="nickname"
            v-model="formData.nickname"
            placeholder="请输入昵称"
            placeholder-class="placeholder"
            @blur="handleNicknameBlur"
          />
          <text class="input-icon">✏️</text>
        </view>
      </view>

      <!-- 性别选择 -->
      <view class="form-item">
        <text class="form-label">性别</text>
        <view class="gender-picker">
          <view 
            class="gender-option"
            :class="{ active: formData.gender === 1 }"
            @tap="formData.gender = 1"
          >
            <text class="gender-icon">👨</text>
            <text class="gender-text">男</text>
          </view>
          <view 
            class="gender-option"
            :class="{ active: formData.gender === 2 }"
            @tap="formData.gender = 2"
          >
            <text class="gender-icon">👩</text>
            <text class="gender-text">女</text>
          </view>
          <view 
            class="gender-option"
            :class="{ active: formData.gender === 0 }"
            @tap="formData.gender = 0"
          >
            <text class="gender-icon">🙂</text>
            <text class="gender-text">保密</text>
          </view>
        </view>
      </view>
    </view>

    <!-- 提交按钮 -->
    <view class="submit-section">
      <button class="submit-btn" :disabled="isSubmitting" @tap="handleSubmit">
        <text class="btn-text">{{ isSubmitting ? '保存中...' : '保存并进入' }}</text>
      </button>
      <view class="skip-wrapper" @tap="handleSkip">
        <text class="skip-text">暂时跳过</text>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { request } from '@/utils/request'

const authStore = useAuthStore()

// 表单数据
const formData = reactive({
  avatarUrl: authStore.userInfo?.avatarUrl || '/static/default-avatar.png',
  nickname: authStore.userInfo?.nickname || '',
  gender: 0 // 0-保密 1-男 2-女
})

// 是否正在提交
const isSubmitting = ref(false)

// 临时头像文件路径（用于上传）
const tempAvatarPath = ref('')

/**
 * 选择头像
 */
const handleChooseAvatar = async (e: any) => {
  console.log('chooseAvatar event:', e)
  
  const avatarUrl = e.detail.avatarUrl
  if (!avatarUrl) {
    uni.showToast({
      title: '获取头像失败',
      icon: 'none'
    })
    return
  }
  
  // 保存临时路径
  tempAvatarPath.value = avatarUrl
  formData.avatarUrl = avatarUrl
}

/**
 * 昵称输入完成
 */
const handleNicknameBlur = (e: any) => {
  console.log('nickname blur:', e.detail.value)
}

/**
 * 提交表单
 */
const handleSubmit = async () => {
  // 验证昵称
  if (!formData.nickname.trim()) {
    uni.showToast({
      title: '请输入昵称',
      icon: 'none'
    })
    return
  }
  
  if (formData.nickname.length < 2 || formData.nickname.length > 20) {
    uni.showToast({
      title: '昵称需要2-20个字符',
      icon: 'none'
    })
    return
  }
  
  if (isSubmitting.value) return
  isSubmitting.value = true
  
  try {
    uni.showLoading({
      title: '保存中...',
      mask: true
    })
    
    // 处理头像
    let avatarData = formData.avatarUrl
    
    // 如果是临时文件路径，转换为 Base64
    if (tempAvatarPath.value && tempAvatarPath.value.startsWith('wxfile://')) {
      avatarData = await fileToBase64(tempAvatarPath.value)
    } else if (tempAvatarPath.value && tempAvatarPath.value.startsWith('http://tmp')) {
      // 临时文件路径（可能是 http://tmp 开头）
      avatarData = await fileToBase64(tempAvatarPath.value)
    }
    
    // 调用更新接口
    const response = await request<{
      success: boolean
      user_info: any
    }>({
      url: '/api/v1/client/auth/user',
      method: 'PUT',
      data: {
        nickname: formData.nickname.trim(),
        avatar: avatarData,
        gender: formData.gender
      }
    })
    
    uni.hideLoading()
    
    // 后端返回格式: {code: 200, data: {...}, msg: "..."}
    if (response.code === 200) {
      // 更新本地用户信息
      authStore.setUserInfo({
        ...authStore.userInfo!,
        nickname: formData.nickname.trim(),
        avatarUrl: formData.avatarUrl,
        gender: formData.gender
      })
      
      uni.showToast({
        title: '保存成功',
        icon: 'success',
        duration: 1500
      })
      
      // 跳转到IP工作台
      setTimeout(() => {
        uni.switchTab({
          url: '/pages/project/list'
        })
      }, 1500)
    } else {
      throw new Error(response.msg || '保存失败')
    }
  } catch (error: any) {
    uni.hideLoading()
    console.error('Update profile error:', error)
    
    // 开发环境模拟成功
    // #ifdef H5
    mockUpdateProfile()
    return
    // #endif
    
    uni.showToast({
      title: error.message || '保存失败，请重试',
      icon: 'none'
    })
  } finally {
    isSubmitting.value = false
  }
}

/**
 * 开发环境模拟更新
 */
const mockUpdateProfile = () => {
  // 更新本地用户信息
  authStore.setUserInfo({
    ...authStore.userInfo!,
    nickname: formData.nickname.trim(),
    avatarUrl: formData.avatarUrl,
    gender: formData.gender
  })
  
  uni.showToast({
    title: '保存成功',
    icon: 'success',
    duration: 1500
  })
  
  setTimeout(() => {
    uni.switchTab({
      url: '/pages/project/list'
    })
  }, 1500)
}

/**
 * 跳过完善资料
 */
const handleSkip = () => {
  uni.showModal({
    title: '提示',
    content: '跳过后可在"我的"页面完善资料',
    confirmText: '确定跳过',
    cancelText: '继续完善',
    success: (res) => {
      if (res.confirm) {
        uni.switchTab({
          url: '/pages/project/list'
        })
      }
    }
  })
}

/**
 * 将文件转换为 Base64
 */
function fileToBase64(filePath: string): Promise<string> {
  return new Promise((resolve, reject) => {
    // #ifdef MP-WEIXIN
    const fs = uni.getFileSystemManager()
    fs.readFile({
      filePath: filePath,
      encoding: 'base64',
      success: (res) => {
        // 返回带有数据类型前缀的 Base64
        resolve(`data:image/png;base64,${res.data}`)
      },
      fail: (err) => {
        console.error('Read file error:', err)
        reject(err)
      }
    })
    // #endif
    
    // #ifndef MP-WEIXIN
    // 非微信环境，直接返回路径
    resolve(filePath)
    // #endif
  })
}
</script>

<style lang="scss" scoped>
// CSS变量 - 品牌色（与 ProjectDashboard 保持一致）
$brand-orange: #FF8800;
$brand-orange-alt: #F37021;
$brand-orange-light: rgba(255, 136, 0, 0.1);
$bg-light: #F5F7FA;

.profile-container {
  min-height: 100vh;
  background: $bg-light;
  padding-bottom: 60rpx;
  position: relative;
  overflow: hidden;
}

/* 顶部背景 */
.header-bg {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 400rpx;
  background: linear-gradient(135deg, $brand-orange 0%, $brand-orange-alt 100%);
  overflow: hidden;
  
  .bg-circle {
    position: absolute;
    border-radius: 50%;
  }
  
  .circle-1 {
    width: 300rpx;
    height: 300rpx;
    background: radial-gradient(circle, rgba(255, 255, 255, 0.15) 0%, transparent 70%);
    top: -100rpx;
    right: -50rpx;
  }
  
  .circle-2 {
    width: 200rpx;
    height: 200rpx;
    background: radial-gradient(circle, rgba(255, 255, 255, 0.12) 0%, transparent 70%);
    top: 150rpx;
    left: -100rpx;
  }
}

/* 页面标题 */
.page-header {
  position: relative;
  z-index: 1;
  padding: 120rpx 40rpx 60rpx;
  
  .header-title {
    display: block;
    font-size: 48rpx;
    font-weight: 700;
    color: #ffffff;
    margin-bottom: 16rpx;
  }
  
  .header-subtitle {
    font-size: 28rpx;
    color: rgba(255, 255, 255, 0.85);
  }
}

/* 表单卡片 */
.form-card {
  position: relative;
  z-index: 1;
  margin: 0 32rpx;
  background: #ffffff;
  border-radius: 32rpx;
  padding: 48rpx 40rpx;
  box-shadow: 0 16rpx 48rpx rgba(0, 0, 0, 0.1);
}

/* 表单项 */
.form-item {
  margin-bottom: 48rpx;
  
  &:last-child {
    margin-bottom: 0;
  }
  
  .form-label {
    display: block;
    font-size: 30rpx;
    font-weight: 600;
    color: #333333;
    margin-bottom: 20rpx;
  }
}

/* 头像选择 */
.avatar-item {
  text-align: center;
  
  .form-label {
    text-align: left;
  }
}

.avatar-picker {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16rpx;
}

.avatar-btn {
  width: 180rpx;
  height: 180rpx;
  padding: 0;
  margin: 0;
  border: none;
  background: transparent;
  position: relative;
  border-radius: 50%;
  overflow: hidden;
  box-shadow: 0 8rpx 32rpx rgba(255, 136, 0, 0.25);
  
  &::after {
    border: none;
  }
  
  .avatar-image {
    width: 100%;
    height: 100%;
    border-radius: 50%;
  }
  
  .avatar-overlay {
    position: absolute;
    bottom: 0;
    left: 0;
    right: 0;
    height: 50rpx;
    background: rgba(0, 0, 0, 0.5);
    display: flex;
    align-items: center;
    justify-content: center;
    
    .overlay-icon {
      font-size: 28rpx;
    }
  }
}

.avatar-tip {
  font-size: 24rpx;
  color: #999999;
}

/* 输入框 */
.input-wrapper {
  display: flex;
  align-items: center;
  background: #f8f9fc;
  border-radius: 16rpx;
  padding: 0 24rpx;
  height: 96rpx;
  border: 2rpx solid #e8eaef;
  transition: all 0.3s ease;
  
  &:focus-within {
    border-color: $brand-orange;
    background: #ffffff;
  }
}

.form-input {
  flex: 1;
  height: 100%;
  font-size: 30rpx;
  color: #333333;
}

.placeholder {
  color: #cccccc;
}

.input-icon {
  font-size: 32rpx;
  margin-left: 16rpx;
}

/* 性别选择 */
.gender-picker {
  display: flex;
  gap: 24rpx;
}

.gender-option {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12rpx;
  padding: 28rpx 0;
  background: #f8f9fc;
  border-radius: 16rpx;
  border: 2rpx solid #e8eaef;
  transition: all 0.3s ease;
  
  &.active {
    background: linear-gradient(135deg, rgba(255, 136, 0, 0.1) 0%, rgba(255, 136, 0, 0.15) 100%);
    border-color: $brand-orange;
    
    .gender-text {
      color: $brand-orange;
      font-weight: 600;
    }
  }
  
  .gender-icon {
    font-size: 48rpx;
  }
  
  .gender-text {
    font-size: 26rpx;
    color: #666666;
  }
}

/* 提交区域 */
.submit-section {
  padding: 60rpx 40rpx 0;
}

.submit-btn {
  width: 100%;
  height: 100rpx;
  background: linear-gradient(135deg, $brand-orange 0%, $brand-orange-alt 100%);
  border-radius: 50rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  border: none;
  box-shadow: 0 8rpx 32rpx rgba(255, 136, 0, 0.4);
  
  &::after {
    border: none;
  }
  
  &:active {
    transform: scale(0.98);
    opacity: 0.9;
  }
  
  &[disabled] {
    opacity: 0.6;
  }
  
  .btn-text {
    font-size: 32rpx;
    font-weight: 600;
    color: #ffffff;
    letter-spacing: 2rpx;
  }
}

.skip-wrapper {
  text-align: center;
  padding: 32rpx;
  
  .skip-text {
    font-size: 28rpx;
    color: #999999;
    text-decoration: underline;
  }
}
</style>




