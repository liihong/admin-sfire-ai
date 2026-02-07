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

    <!-- 推荐人手机号 -->
      <view class="form-item">
       <text class="form-label">推荐人手机号（选填）</text>
        <view class="input-wrapper">
          <input class="form-input" type="number" v-model="formData.inviterPhone" placeholder="请输入推荐人手机号"
            placeholder-class="placeholder" maxlength="11" @blur="handleInviterPhoneBlur" />
          <text class="input-icon">📱</text>
        </view>
       <text class="form-tip">填写推荐人手机号可获得额外奖励</text>
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
import { updateUserInfo, uploadAvatar } from '@/api/user'

const authStore = useAuthStore()

// 表单数据
const formData = reactive({
  avatarUrl: authStore.userInfo?.avatarUrl || '/static/default-avatar.png',
  nickname: authStore.userInfo?.nickname || '',
  inviterPhone: '' // 推荐人手机号
})

// 是否正在提交
const isSubmitting = ref(false)

// 临时头像文件路径（用于上传）
const tempAvatarPath = ref('')

/**
 * 选择头像
 */
const handleChooseAvatar = async (e: any) => {
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
  // 昵称输入完成处理
}

/**
 * 推荐人手机号输入完成
 */
const handleInviterPhoneBlur = (e: any) => {
  const phone = e.detail.value?.trim() || ''
  if (phone && !/^1[3-9]\d{9}$/.test(phone)) {
    uni.showToast({
      title: '请输入正确的手机号',
      icon: 'none'
    })
  }
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
    
    // 准备更新数据
    const updateData: {
      nickname: string
      avatar?: string
      inviter_phone?: string
    } = {
      nickname: formData.nickname.trim()
    }
    
    // 如果填写了推荐人手机号，进行验证并添加
    const inviterPhone = formData.inviterPhone?.trim() || ''
    if (inviterPhone) {
      // 验证手机号格式
      if (!/^1[3-9]\d{9}$/.test(inviterPhone)) {
        uni.showToast({
          title: '请输入正确的手机号',
          icon: 'none'
        })
        isSubmitting.value = false
        return
      }
      updateData.inviter_phone = inviterPhone
    }

    // 如果选择了新头像，先上传头像
    if (tempAvatarPath.value) {
      try {
        const uploadResponse = await uploadAvatar(tempAvatarPath.value)

        // 检查上传是否成功
        if (uploadResponse.code === 200 && uploadResponse.data?.url) {
          // 上传成功，使用返回的 URL
          updateData.avatar = uploadResponse.data.url
          formData.avatarUrl = uploadResponse.data.url
        } else {
          throw new Error(uploadResponse.msg || '头像上传失败')
        }
      } catch (uploadError: any) {
        uni.hideLoading()
        console.error('上传头像失败:', uploadError)
        uni.showToast({
          title: uploadError?.message || '头像上传失败，请重试',
          icon: 'none'
        })
        isSubmitting.value = false
        return
      }
    }

    // 调用更新用户信息接口
    const response = await updateUserInfo(updateData)
    
    uni.hideLoading()
    
    // 后端返回格式: {code: 200, data: {...}, msg: "..."}
    if (response.code === 200) {
      // 刷新用户信息（从服务器获取最新信息）
      await authStore.refreshUserInfo()
      
      uni.showToast({
        title: '保存成功',
        icon: 'success',
        duration: 1500
      })
      
      // 跳转到IP工作台
      setTimeout(() => {
        uni.switchTab({
          url: '/pages/project/index'
        })
      }, 1500)
    } else {
      throw new Error((response as any).msg || '保存失败')
    }
  } catch (error: any) {
    uni.hideLoading()
    console.error('Update profile error:', error)
    
    uni.showToast({
      title: error.message || '保存失败，请重试',
      icon: 'none'
    })
  } finally {
    isSubmitting.value = false
  }
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
          url: '/pages/project/index'
        })
      }
    }
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

.form-tip {
  display: block;
  font-size: 24rpx;
  color: #999999;
  margin-top: 12rpx;
  line-height: 1.5;
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




