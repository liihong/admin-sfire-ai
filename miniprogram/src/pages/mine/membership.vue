<template>
  <view class="page-wrapper">
    <!-- 页面头部 -->
    <view class="page-header">
      <SafeAreaTop />
      <view class="header-back" @tap="goBack">
        <text class="back-icon">←</text>
      </view>
      <view class="header-content">
        <text class="header-title">开通会员</text>
      </view>
    </view>

    <scroll-view scroll-y class="page-container">
      <!-- 科技感背景装饰 -->
      <view class="bg-decoration">
        <view class="grid-lines"></view>
        <view class="glow-circle glow-1"></view>
        <view class="glow-circle glow-2"></view>
        <view class="glow-circle glow-3"></view>
      </view>

    <!-- VIP会员特权横幅区 -->
    <view class="vip-hero-section">
      <view class="hero-bg-pattern"></view>
      <view class="hero-content">
        <view class="vip-badge">
          <text class="vip-text">VIP</text>
          <view class="vip-glow"></view>
        </view>
        <view class="hero-title">解锁全部高级功能</view>
        <view class="hero-features">
          <text class="feature-tag">赠送算力</text>
          <text class="feature-divider">|</text>
          <text class="feature-tag">无限数字人</text>
          <text class="feature-divider">|</text>
          <text class="feature-tag">爆款AI导师</text>
        </view>
        <view class="hero-cta">
          <text class="cta-text">立即加入 引领未来</text>
          <view class="cta-arrow">↓</view>
        </view>
      </view>
    </view>

    <!-- 选择会员套餐区 -->
    <view class="section-container">
      <view class="section-header">
        <view class="section-indicator"></view>
        <text class="section-title">选择会员套餐</text>
      </view>
      <view class="package-card" :class="{ selected: selectedPackage === 'annual' }" @tap="selectPackage('annual')">
        <view class="package-header">
          <text class="package-name">年度会员</text>
          <view class="recommend-badge">推荐</view>
        </view>
        <view class="package-price">
          <text class="price-symbol">¥</text>
          <text class="price-value">3980</text>
        </view>
        <text class="package-desc">包年VIP会员，享受全部特权功能，赠送10000算力</text>
        <view class="package-select-icon" v-if="selectedPackage === 'annual'">
          <text class="select-check">✓</text>
        </view>
        <view class="package-glow" v-if="selectedPackage === 'annual'"></view>
      </view>
    </view>

    <!-- 联系我开通会员区 -->
    <view class="section-container">
      <view class="section-header">
        <view class="section-indicator"></view>
        <text class="section-title">联系我开通会员</text>
      </view>
      <view class="qr-card">
        <view class="qr-wrapper">
          <image 
            class="qr-code" 
            src="/static/qrcode-placeholder.png" 
            mode="aspectFit"
          />
          <view class="qr-pattern"></view>
        </view>
        <text class="qr-hint">扫一扫上面的二维码图案，加我为朋友。</text>
        <text class="qr-action">长按二维码添加小猫导师微信</text>
      </view>
    </view>

    <!-- 会员专属权益区 -->
    <view class="section-container">
      <view class="section-header">
        <view class="section-indicator"></view>
        <text class="section-title">会员专属权益</text>
      </view>
      <view class="benefits-list">
        <view 
          v-for="(benefit, index) in benefitsList" 
          :key="index" 
          class="benefit-item"
        >
          <view class="benefit-icon-wrapper">
            <text class="benefit-number">{{ index + 1 }}</text>
            <view class="benefit-glow"></view>
          </view>
          <view class="benefit-content">
            <text class="benefit-title">{{ benefit.title }}</text>
            <text class="benefit-desc">{{ benefit.desc }}</text>
          </view>
        </view>
      </view>
    </view>

      <view class="bottom-gap"></view>
    </scroll-view>
  </view>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import SafeAreaTop from '@/components/common/SafeAreaTop.vue'

// 返回上一页
const goBack = () => {
  uni.navigateBack()
}

// 选中的套餐
const selectedPackage = ref<'annual' | null>('annual')

// 选择套餐
const selectPackage = (type: 'annual') => {
  selectedPackage.value = type
}

// 会员权益列表
const benefitsList = ref([
  {
    title: '赠送超值算力',
    desc: '算力可用于AI视频、AI创作等'
  },
  {
    title: '无限生成实景数字人',
    desc: '无限次克隆你的数字人分身'
  },
  {
    title: '爆款AI导师',
    desc: 'AI营销获客全流程一对一指导'
  },
  {
    title: 'AI文案智能体',
    desc: '爆款AI文案智能体矩阵,人人都可以是专业自媒体运营专家'
  }
])
</script>

<style scoped lang="scss">
.page-wrapper {
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: linear-gradient(180deg, #0a0e27 0%, #1a1f3a 50%, #0f1629 100%);
  overflow: hidden;
}

/* 页面头部 */
.page-header {
  position: relative;
  z-index: 100;
  background: rgba(10, 14, 39, 0.8);
  backdrop-filter: blur(10rpx);
  border-bottom: 1rpx solid rgba(59, 130, 246, 0.2);
}

.header-back {
  position: absolute;
  left: 32rpx;
  top: 50%;
  transform: translateY(-50%);
  width: 64rpx;
  height: 64rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2;
}

.back-icon {
  font-size: 48rpx;
  color: #ffffff;
  font-weight: 300;
}

.header-content {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24rpx 0;
  min-height: 88rpx;
}

.header-title {
  font-size: 36rpx;
  font-weight: 700;
  color: #ffffff;
  text-shadow: 0 0 10rpx rgba(59, 130, 246, 0.3);
}

.page-container {
  flex: 1;
  height: 0;
  background: linear-gradient(180deg, #0a0e27 0%, #1a1f3a 50%, #0f1629 100%);
  position: relative;
  padding-bottom: 40rpx;
  box-sizing: border-box;
}

/* 科技感背景装饰 */
.bg-decoration {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  pointer-events: none;
  z-index: 0;
  overflow: hidden;
}

.grid-lines {
  position: absolute;
  inset: 0;
  background-image: 
    linear-gradient(rgba(59, 130, 246, 0.1) 1px, transparent 1px),
    linear-gradient(90deg, rgba(59, 130, 246, 0.1) 1px, transparent 1px);
  background-size: 60rpx 60rpx;
  opacity: 0.3;
}

.glow-circle {
  position: absolute;
  border-radius: 50%;
  filter: blur(80rpx);
  opacity: 0.4;
  animation: float 8s ease-in-out infinite;
  
  &.glow-1 {
    width: 400rpx;
    height: 400rpx;
    top: -100rpx;
    left: -100rpx;
    background: radial-gradient(circle, rgba(59, 130, 246, 0.6) 0%, transparent 70%);
    animation-delay: 0s;
  }
  
  &.glow-2 {
    width: 500rpx;
    height: 500rpx;
    top: 30%;
    right: -150rpx;
    background: radial-gradient(circle, rgba(139, 92, 246, 0.5) 0%, transparent 70%);
    animation-delay: 2s;
  }
  
  &.glow-3 {
    width: 350rpx;
    height: 350rpx;
    bottom: 20%;
    left: 10%;
    background: radial-gradient(circle, rgba(236, 72, 153, 0.4) 0%, transparent 70%);
    animation-delay: 4s;
  }
}

@keyframes float {
  0%, 100% {
    transform: translate(0, 0) scale(1);
  }
  33% {
    transform: translate(30rpx, -30rpx) scale(1.1);
  }
  66% {
    transform: translate(-20rpx, 20rpx) scale(0.9);
  }
}

/* VIP会员特权横幅区 */
.vip-hero-section {
  position: relative;
  margin: 32rpx 24rpx 40rpx;
  padding: 60rpx 40rpx;
  border-radius: 32rpx;
  overflow: hidden;
  background: linear-gradient(135deg, rgba(59, 130, 246, 0.15) 0%, rgba(139, 92, 246, 0.2) 100%);
  border: 1rpx solid rgba(59, 130, 246, 0.3);
  box-shadow: 
    0 20rpx 60rpx rgba(59, 130, 246, 0.2),
    inset 0 0 80rpx rgba(59, 130, 246, 0.1);
  z-index: 1;
}

.hero-bg-pattern {
  position: absolute;
  inset: 0;
  background-image: 
    radial-gradient(circle at 20% 30%, rgba(59, 130, 246, 0.2) 0%, transparent 50%),
    radial-gradient(circle at 80% 70%, rgba(139, 92, 246, 0.2) 0%, transparent 50%);
  opacity: 0.6;
}

.hero-content {
  position: relative;
  z-index: 2;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 24rpx;
}

.vip-badge {
  position: relative;
  font-size: 120rpx;
  font-weight: 900;
  background: linear-gradient(135deg, #fbbf24 0%, #f59e0b 50%, #d97706 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  text-shadow: 0 0 40rpx rgba(251, 191, 36, 0.5);
  letter-spacing: 8rpx;
  animation: vipPulse 2s ease-in-out infinite;
}

.vip-glow {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 200rpx;
  height: 200rpx;
  background: radial-gradient(circle, rgba(251, 191, 36, 0.4) 0%, transparent 70%);
  filter: blur(40rpx);
  animation: vipGlow 2s ease-in-out infinite;
}

@keyframes vipPulse {
  0%, 100% {
    transform: scale(1);
  }
  50% {
    transform: scale(1.05);
  }
}

@keyframes vipGlow {
  0%, 100% {
    opacity: 0.6;
    transform: translate(-50%, -50%) scale(1);
  }
  50% {
    opacity: 1;
    transform: translate(-50%, -50%) scale(1.2);
  }
}

.hero-title {
  font-size: 44rpx;
  font-weight: 700;
  color: #ffffff;
  text-align: center;
  text-shadow: 0 0 20rpx rgba(59, 130, 246, 0.5);
}

.hero-features {
  display: flex;
  align-items: center;
  gap: 16rpx;
  padding: 16rpx 32rpx;
  background: linear-gradient(135deg, rgba(251, 191, 36, 0.2) 0%, rgba(251, 191, 36, 0.15) 100%);
  border-radius: 999rpx;
  border: 1rpx solid rgba(251, 191, 36, 0.4);
  backdrop-filter: blur(10rpx);
}

.feature-tag {
  font-size: 24rpx;
  color: #ffffff;
  font-weight: 600;
}

.feature-divider {
  font-size: 20rpx;
  color: rgba(255, 255, 255, 0.5);
}

.hero-cta {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8rpx;
  margin-top: 8rpx;
}

.cta-text {
  font-size: 28rpx;
  color: rgba(255, 255, 255, 0.9);
  font-weight: 500;
}

.cta-arrow {
  font-size: 24rpx;
  color: rgba(59, 130, 246, 0.8);
  animation: bounce 1.5s ease-in-out infinite;
}

@keyframes bounce {
  0%, 100% {
    transform: translateY(0);
  }
  50% {
    transform: translateY(10rpx);
  }
}

/* 区块容器 */
.section-container {
  margin: 0 24rpx 40rpx;
  z-index: 1;
  position: relative;
}

.section-header {
  display: flex;
  align-items: center;
  gap: 16rpx;
  margin-bottom: 24rpx;
}

.section-indicator {
  width: 6rpx;
  height: 32rpx;
  background: linear-gradient(180deg, #3b82f6 0%, #8b5cf6 100%);
  border-radius: 3rpx;
  box-shadow: 0 0 12rpx rgba(59, 130, 246, 0.6);
}

.section-title {
  font-size: 32rpx;
  font-weight: 700;
  color: #ffffff;
  text-shadow: 0 0 10rpx rgba(59, 130, 246, 0.3);
}

/* 套餐卡片 */
.package-card {
  position: relative;
  padding: 40rpx 32rpx;
  background: linear-gradient(135deg, rgba(30, 41, 59, 0.8) 0%, rgba(15, 23, 42, 0.9) 100%);
  border-radius: 24rpx;
  border: 2rpx solid rgba(59, 130, 246, 0.2);
  backdrop-filter: blur(10rpx);
  transition: all 0.3s ease;
  
  &.selected {
    border-color: rgba(59, 130, 246, 0.6);
    box-shadow: 
      0 0 40rpx rgba(59, 130, 246, 0.3),
      inset 0 0 40rpx rgba(59, 130, 246, 0.1);
  }
}

.package-glow {
  position: absolute;
  inset: -2rpx;
  border-radius: 24rpx;
  background: linear-gradient(135deg, rgba(59, 130, 246, 0.3), rgba(139, 92, 246, 0.3));
  filter: blur(20rpx);
  z-index: -1;
  animation: glowPulse 2s ease-in-out infinite;
}

@keyframes glowPulse {
  0%, 100% {
    opacity: 0.5;
  }
  50% {
    opacity: 1;
  }
}

.package-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24rpx;
}

.package-name {
  font-size: 32rpx;
  font-weight: 700;
  color: #ffffff;
}

.recommend-badge {
  padding: 8rpx 20rpx;
  background: linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%);
  border-radius: 999rpx;
  font-size: 22rpx;
  color: #ffffff;
  font-weight: 600;
  box-shadow: 0 0 20rpx rgba(59, 130, 246, 0.5);
}

.package-price {
  display: flex;
  align-items: baseline;
  gap: 8rpx;
  margin-bottom: 16rpx;
}

.price-symbol {
  font-size: 32rpx;
  color: #3b82f6;
  font-weight: 600;
}

.price-value {
  font-size: 64rpx;
  color: #3b82f6;
  font-weight: 900;
  text-shadow: 0 0 20rpx rgba(59, 130, 246, 0.5);
}

.package-desc {
  font-size: 26rpx;
  color: rgba(255, 255, 255, 0.7);
  line-height: 1.6;
}

.package-select-icon {
  position: absolute;
  bottom: 32rpx;
  right: 32rpx;
  width: 56rpx;
  height: 56rpx;
  background: linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 0 20rpx rgba(59, 130, 246, 0.6);
}

.select-check {
  font-size: 32rpx;
  color: #ffffff;
  font-weight: 700;
}

/* 二维码卡片 */
.qr-card {
  padding: 40rpx;
  background: linear-gradient(135deg, rgba(30, 41, 59, 0.8) 0%, rgba(15, 23, 42, 0.9) 100%);
  border-radius: 24rpx;
  border: 1rpx solid rgba(59, 130, 246, 0.2);
  backdrop-filter: blur(10rpx);
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 24rpx;
}

.qr-wrapper {
  position: relative;
  width: 400rpx;
  height: 400rpx;
  padding: 24rpx;
  background: #ffffff;
  border-radius: 16rpx;
  box-shadow: 
    0 0 40rpx rgba(59, 130, 246, 0.3),
    inset 0 0 20rpx rgba(59, 130, 246, 0.1);
}

.qr-code {
  width: 100%;
  height: 100%;
  border-radius: 8rpx;
}

.qr-pattern {
  position: absolute;
  inset: 0;
  background-image: 
    linear-gradient(45deg, rgba(59, 130, 246, 0.1) 25%, transparent 25%),
    linear-gradient(-45deg, rgba(59, 130, 246, 0.1) 25%, transparent 25%),
    linear-gradient(45deg, transparent 75%, rgba(59, 130, 246, 0.1) 75%),
    linear-gradient(-45deg, transparent 75%, rgba(59, 130, 246, 0.1) 75%);
  background-size: 20rpx 20rpx;
  background-position: 0 0, 0 10rpx, 10rpx -10rpx, -10rpx 0rpx;
  border-radius: 16rpx;
  pointer-events: none;
}

.qr-hint {
  font-size: 24rpx;
  color: rgba(255, 255, 255, 0.6);
  text-align: center;
}

.qr-action {
  font-size: 28rpx;
  color: rgba(255, 255, 255, 0.9);
  font-weight: 600;
  text-align: center;
}

/* 权益列表 */
.benefits-list {
  display: flex;
  flex-direction: column;
  gap: 24rpx;
}

.benefit-item {
  display: flex;
  gap: 24rpx;
  padding: 32rpx;
  background: linear-gradient(135deg, rgba(30, 41, 59, 0.8) 0%, rgba(15, 23, 42, 0.9) 100%);
  border-radius: 20rpx;
  border: 1rpx solid rgba(59, 130, 246, 0.2);
  backdrop-filter: blur(10rpx);
  transition: all 0.3s ease;
  
  &:active {
    transform: scale(0.98);
    border-color: rgba(59, 130, 246, 0.4);
  }
}

.benefit-icon-wrapper {
  position: relative;
  width: 80rpx;
  height: 80rpx;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, rgba(59, 130, 246, 0.3) 0%, rgba(139, 92, 246, 0.3) 100%);
  border-radius: 50%;
  border: 2rpx solid rgba(59, 130, 246, 0.5);
}

.benefit-glow {
  position: absolute;
  inset: -4rpx;
  border-radius: 50%;
  background: radial-gradient(circle, rgba(59, 130, 246, 0.4) 0%, transparent 70%);
  filter: blur(12rpx);
  animation: benefitGlow 2s ease-in-out infinite;
}

@keyframes benefitGlow {
  0%, 100% {
    opacity: 0.5;
  }
  50% {
    opacity: 1;
  }
}

.benefit-number {
  font-size: 36rpx;
  font-weight: 700;
  color: #ffffff;
  position: relative;
  z-index: 1;
}

.benefit-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 12rpx;
}

.benefit-title {
  font-size: 30rpx;
  font-weight: 700;
  color: #ffffff;
}

.benefit-desc {
  font-size: 26rpx;
  color: rgba(255, 255, 255, 0.7);
  line-height: 1.5;
}

.bottom-gap {
  height: 40rpx;
}
</style>
