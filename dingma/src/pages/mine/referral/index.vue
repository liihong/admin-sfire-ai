<template>
  <view class="page-wrapper">
    <!-- 页面头部 -->
    <BaseHeader title="我要推荐" @back="goBack" />

    <scroll-view scroll-y class="page-container">
      <!-- 邀请码卡片 -->
      <view class="invite-card">
        <view class="invite-header">
          <text class="invite-title">我的邀请码</text>
          <text class="invite-subtitle">邀请好友一起体验</text>
        </view>
        <view class="invite-code-wrapper">
          <text class="invite-code">{{ inviteCode || '未登录' }}</text>
          <view class="copy-btn" @tap="copyInviteCode">
            <text class="copy-btn-text">复制</text>
          </view>
        </view>
        <view class="invite-tip">
          <text class="tip-text">好友注册时输入此邀请码，您将获得奖励</text>
        </view>
      </view>

      <!-- 邀请奖励说明卡片 -->
      <view class="reward-card">
        <view class="reward-header">
          <text class="reward-header-icon">🎁</text>
          <text class="reward-title">邀请奖励</text>
        </view>
        <view class="reward-content">
          <view class="reward-item">
            <view class="reward-icon-wrapper">
              <text class="reward-icon">🎁</text>
            </view>
            <view class="reward-info">
              <text class="reward-label">成功邀请奖励</text>
              <text class="reward-value">100 算力点</text>
            </view>
          </view>
          <view class="reward-desc">
            <text class="desc-text">每成功邀请一名好友注册并完成首次登录，系统将自动奖励您 100 算力点</text>
          </view>
        </view>
      </view>

      <!-- 分享按钮：plain + 图标定宽，避免 button 内 image 被撑满 -->
      <view class="share-section">
        <button class="share-btn" plain @tap="handleShare" open-type="share">
          <view class="share-btn-content">
            <view class="share-icon-wrap">
              <SvgIcon name="send" :size="36" color="#FFFFFF" />
            </view>
            <text class="share-btn-text">立即分享</text>
          </view>
        </button>
        <text class="share-tip">分享给好友或朋友圈，邀请他们一起体验</text>
      </view>

      <!-- 邀请规则说明 -->
      <view class="rules-card">
        <view class="rules-header">
          <text class="rules-title">邀请规则</text>
        </view>
        <view class="rules-list">
          <view class="rule-item" v-for="(rule, index) in rules" :key="index">
            <view class="rule-number">{{ index + 1 }}</view>
            <text class="rule-text">{{ rule }}</text>
          </view>
        </view>
      </view>

      <view class="bottom-gap"></view>
    </scroll-view>
  </view>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { onShareAppMessage, onShareTimeline } from '@dcloudio/uni-app'
import BaseHeader from '@/components/base/BaseHeader.vue'
import SvgIcon from '@/components/base/SvgIcon.vue'
import { useAuthStore } from '@/stores/auth'

// 获取 store 实例
const authStore = useAuthStore()

// 邀请码（用户手机号）
const inviteCode = computed(() => {
  const phone = authStore.userInfo?.phone
  return phone || ''
})

// 邀请规则
const rules = ref([
  '好友通过您的邀请码注册并完成首次登录',
  '系统自动识别邀请关系并发放奖励',
  '每成功邀请一人，您将获得 100 算力点奖励',
  '奖励将在好友完成注册后立即到账',
  '邀请码为您的手机号，请妥善保管'
])

/**
 * 返回上一页
 */
const goBack = () => {
  uni.navigateBack()
}

/**
 * 复制邀请码
 */
const copyInviteCode = () => {
  if (!inviteCode.value) {
    uni.showToast({
      title: '请先登录',
      icon: 'none'
    })
    return
  }

  uni.setClipboardData({
    data: inviteCode.value,
    success: () => {
      uni.showToast({
        title: '邀请码已复制',
        icon: 'success'
      })
    },
    fail: () => {
      uni.showToast({
        title: '复制失败',
        icon: 'none'
      })
    }
  })
}

/**
 * 处理分享
 */
const handleShare = () => {
  if (!inviteCode.value) {
    uni.showToast({
      title: '请先登录',
      icon: 'none'
    })
    return
  }
  // 分享功能由 onShareAppMessage 和 onShareTimeline 处理
}

/**
 * 分享给好友
 */
onShareAppMessage(() => {
  return {
    title: `邀请您一起体验火源灵感火花，使用我的邀请码：${inviteCode.value || '****'}`,
    path: `/pages/login/index?inviteCode=${inviteCode.value || ''}`,
    imageUrl: '/static/logo.png'
  }
})

/**
 * 分享到朋友圈
 */
onShareTimeline(() => {
  return {
    title: `邀请您一起体验火源灵感火花，使用我的邀请码：${inviteCode.value || '****'}`,
    query: `inviteCode=${inviteCode.value || ''}`,
    imageUrl: '/static/logo.png'
  }
})
</script>

<style scoped lang="scss">
@import '@/styles/_variables.scss';

.page-wrapper {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
  background: $bg-color;
}

.page-container {
  flex: 1;
  height: 0;
  min-height: 0;
  padding: 24rpx;
  box-sizing: border-box;
}

/* 邀请码卡片 */
.invite-card {
  background: linear-gradient(135deg, #F37021 0%, #FF8800 100%);
  border-radius: 24rpx;
  padding: 48rpx 32rpx;
  margin-bottom: 24rpx;
  box-shadow: 0 8rpx 24rpx rgba(243, 112, 33, 0.25);
}

.invite-header {
  display: flex;
  flex-direction: column;
  align-items: center;
  margin-bottom: 32rpx;
}

.invite-title {
  font-size: 40rpx;
  font-weight: 700;
  color: $white;
  margin-bottom: 8rpx;
}

.invite-subtitle {
  font-size: 26rpx;
  color: rgba(255, 255, 255, 0.9);
}

.invite-code-wrapper {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: rgba(255, 255, 255, 0.2);
  border-radius: 16rpx;
  padding: 24rpx 32rpx;
  margin-bottom: 24rpx;
  backdrop-filter: blur(10rpx);
}

.invite-code {
  font-size: 48rpx;
  font-weight: 700;
  color: $white;
  letter-spacing: 4rpx;
  font-family: 'DIN Alternate', 'Helvetica Neue', sans-serif;
}

.copy-btn {
  padding: 12rpx 24rpx;
  background: $white;
  border-radius: 12rpx;
  flex-shrink: 0;
}

.copy-btn-text {
  font-size: 26rpx;
  color: $primary-orange;
  font-weight: 600;
}

.copy-btn:active {
  opacity: 0.9;
  transform: scale(0.98);
}

.invite-tip {
  display: flex;
  justify-content: center;
}

.tip-text {
  font-size: 24rpx;
  color: rgba(255, 255, 255, 0.85);
  line-height: 1.5;
}

/* 邀请奖励说明卡片 */
.reward-card {
  background: $white;
  border-radius: 24rpx;
  padding: 32rpx;
  margin-bottom: 24rpx;
  box-shadow: $card-shadow;
}

.reward-header {
  display: flex;
  align-items: center;
  gap: 16rpx;
  margin-bottom: 24rpx;
}

.reward-header-icon {
  font-size: 40rpx;
  line-height: 1;
}

.reward-title {
  font-size: 32rpx;
  font-weight: 600;
  color: $text-main;
}

.reward-content {
  display: flex;
  flex-direction: column;
  gap: 24rpx;
}

.reward-item {
  display: flex;
  align-items: center;
  gap: 20rpx;
  padding: 24rpx;
  background: linear-gradient(135deg, rgba(243, 112, 33, 0.1) 0%, rgba(255, 136, 0, 0.1) 100%);
  border-radius: 16rpx;
}

.reward-icon-wrapper {
  width: 64rpx;
  height: 64rpx;
  background: linear-gradient(135deg, #F37021 0%, #FF8800 100%);
  border-radius: 16rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.reward-icon {
  font-size: 36rpx;
}

.reward-info {
  display: flex;
  flex-direction: column;
  gap: 4rpx;
  flex: 1;
}

.reward-label {
  font-size: 26rpx;
  color: $text-second;
}

.reward-value {
  font-size: 36rpx;
  font-weight: 700;
  color: $primary-orange;
}

.reward-desc {
  padding: 20rpx;
  background: #F7F8FA;
  border-radius: 12rpx;
}

.desc-text {
  font-size: 26rpx;
  color: $text-second;
  line-height: 1.6;
}

/* 分享按钮区域 */
.share-section {
  display: flex;
  flex-direction: column;
  align-items: center;
  margin-bottom: 24rpx;
}

.share-btn {
  width: 100%;
  height: 96rpx;
  padding: 0;
  margin: 0 0 16rpx;
  line-height: 1;
  overflow: hidden;
  box-sizing: border-box;
  background: linear-gradient(135deg, #F37021 0%, #FF8800 100%) !important;
  border-radius: 48rpx;
  border: none !important;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 8rpx 24rpx rgba(243, 112, 33, 0.3);
}

.share-btn::after {
  border: none;
}

.share-btn-content {
  display: flex;
  flex-direction: row;
  align-items: center;
  justify-content: center;
  gap: 12rpx;
  width: 100%;
  height: 100%;
}

/** 微信 button 内 image 会默认撑满，必须外层定宽高 */
.share-icon-wrap {
  width: 36rpx;
  height: 36rpx;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;

  :deep(.svg-icon--lucide),
  :deep(image) {
    width: 36rpx !important;
    height: 36rpx !important;
    max-width: 36rpx;
    max-height: 36rpx;
  }
}

.share-btn-text {
  font-size: 32rpx;
  color: $white;
  font-weight: 600;
}

.share-btn:active {
  opacity: 0.9;
  transform: scale(0.98);
}

.share-tip {
  font-size: 24rpx;
  color: $text-second;
  text-align: center;
}

/* 邀请规则说明卡片 */
.rules-card {
  background: $white;
  border-radius: 24rpx;
  padding: 32rpx;
  margin-bottom: 24rpx;
  box-shadow: $card-shadow;
}

.rules-header {
  margin-bottom: 24rpx;
}

.rules-title {
  font-size: 32rpx;
  font-weight: 600;
  color: $text-main;
}

.rules-list {
  display: flex;
  flex-direction: column;
  gap: 20rpx;
}

.rule-item {
  display: flex;
  align-items: flex-start;
  gap: 16rpx;
}

.rule-number {
  width: 40rpx;
  height: 40rpx;
  background: linear-gradient(135deg, #F37021 0%, #FF8800 100%);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  font-size: 24rpx;
  color: $white;
  font-weight: 600;
}

.rule-text {
  font-size: 26rpx;
  color: $text-second;
  line-height: 1.6;
  flex: 1;
}

.bottom-gap {
  height: calc(48rpx + env(safe-area-inset-bottom));
}
</style>

