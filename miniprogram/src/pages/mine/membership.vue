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
     <!-- 会员特权介绍卡片 - 重新设计 -->
      <view class="hero-section">
        <view class="hero-card">
          <view class="hero-bg-pattern"></view>
          <view class="hero-content">
           <view class="hero-left">
              <view class="hero-badge-wrapper">
                <text class="hero-badge-text">VIP</text>
                <view class="badge-glow"></view>
              </view>
             <text class="hero-title">解锁全部高级功能</text>
              <text class="hero-subtitle">享受专业服务，提升工作效率</text>
            </view>
           <view class="hero-right">
              <view class="hero-icon">✨</view>
            </view>
          </view>
        </view>
      </view>

    <!-- 会员专属权益区 - 纵向排列 -->
      <view class="section-container">
       <view class="section-header">
          <text class="section-title">会员专属权益</text>
        </view>
        <view class="benefits-list">
          <view v-for="(benefit, index) in benefitsList" :key="index" class="benefit-item">
            <view class="benefit-icon-wrapper">
             <text class="benefit-number">{{ index + 1 }}</text>
            </view>
            <view class="benefit-content">
              <text class="benefit-title">{{ benefit.title }}</text>
              <text class="benefit-desc">{{ benefit.desc }}</text>
            </view>
          </view>
        </view>
      </view>

    <!-- 选择会员套餐区 - 横向滚动 -->
      <view class="section-container">
        <view class="section-header">
         <text class="section-title">选择会员套餐</text>
        </view>
       <scroll-view scroll-x class="package-scroll" show-scrollbar="false">
          <view class="package-list">
            <!-- 月卡会员 -->
            <view class="package-card selected">
              <view class="package-header">
               <view class="package-name-wrapper">
                  <text class="package-name">月卡会员</text>
                </view>
               <view class="limit-badge">限时优惠</view>
              </view>
              <view class="package-price-row">
                <view class="package-price">
                  <text class="price-symbol">¥</text>
                  <text class="price-value">199</text>
                </view>
                <text class="price-original">原价¥299</text>
              </view>
              <text class="package-desc">限时优惠，每个用户仅限一次</text>
            </view>

            <!-- VIP年卡会员 -->
            <view class="package-card selected popular" @tap="selectPackage('vip')">
              <view class="popular-tag">推荐</view>
              <view class="package-header">
                <view class="package-name-wrapper">
                  <text class="package-name">VIP年卡会员</text>
                </view>
              </view>
              <view class="package-price-row">
                <view class="package-price">
                  <text class="price-symbol">¥</text>
                  <text class="price-value">1980</text>
                </view>
              </view>
              <text class="package-desc">可解锁1个IP席位，享受全部VIP特权</text>

            </view>

            <!-- SVIP超级会员 -->
            <view class="package-card selected premium" @tap="selectPackage('svip')">
              <view class="premium-tag">超值</view>
              <view class="package-header">
                <view class="package-name-wrapper">
                  <text class="package-name">SVIP超级会员</text>
                </view>
              </view>
              <view class="package-price-row">
               <view class="package-price">
                  <text class="price-symbol">¥</text>
                  <text class="price-value">3980</text>
                </view>
             </view>
             <text class="package-desc">可解锁5个IP席位，享受全部SVIP特权</text>

            </view>
          </view>
       </scroll-view>

      <!-- 更多席位提示 -->
        <view class="more-seats-tip">
          <text class="tip-text">如需更多席位，请联系管理员</text>
        </view>
      </view>

      <!-- 联系开通会员区 -->
      <view class="section-container">
        <view class="section-header">
         <text class="section-title">联系开通会员</text>
        </view>
        <view class="qr-card">
          <view class="qr-wrapper">
           <image :show-menu-by-longpress="true" class="qr-code" src="/static/qrcode-placeholder.png"
              mode="aspectFit" />
          </view>
         <text class="qr-hint">扫一扫上面的二维码图案，加我为朋友</text>
          <text class="qr-action">长按二维码添加隔壁老陈导师微信</text>
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

// 选中的套餐类型
type PackageType = 'monthly' | 'vip' | 'svip' | null

// 选中的套餐
const selectedPackage = ref<PackageType>('vip')

// 选择套餐
const selectPackage = (type: PackageType) => {
  selectedPackage.value = type
}

// 会员权益列表
const benefitsList = ref([
  {
    title: '赠送超值算力',
    desc: '算力可用于IP定位、AI创作等'
  },
  {
    title: '爆款AI导师',
    desc: 'AI营销获客全流程一对一指导'
  },
  {
    title: 'AI文案智能体',
    desc: '爆款AI文案智能体矩阵，人人都可以是专业自媒体运营专家'
  }
])
</script>

<style scoped lang="scss">
@import '@/styles/_variables.scss';
.page-wrapper {
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: $bg-light;
  overflow: hidden;
}

.page-header {
  position: relative;
  z-index: 100;
  background: $white;
    border-bottom: 1rpx solid $border-color;
    box-shadow: $shadow-sm;
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
  border-radius: 50%;
    background: rgba(0, 0, 0, 0.05);
}

.back-icon {
  font-size: 36rpx;
    color: $text-main;
    font-weight: 600;
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
  font-weight: 600;
    color: $text-main;
}

.page-container {
  flex: 1;
  height: 0;
  background: $bg-light;
  padding-bottom: 40rpx;
}

.hero-section {
  margin: 32rpx 24rpx 40rpx;
}

.hero-card {
  background: linear-gradient(135deg, #1A1A2E 0%, #16213E 100%);
  border-radius: $radius-lg;
  padding: 48rpx 40rpx;
  overflow: hidden;
}

.hero-bg-pattern {
  display: none;
}

.hero-content {
  display: flex;
    align-items: center;
    justify-content: space-between;
      gap: 32rpx;
    }
    .hero-left {
      flex: 1;
      display: flex;
      flex-direction: column;
      gap: 16rpx;
    }
  
    .hero-badge-wrapper {
      width: 96rpx;
      height: 96rpx;
      display: flex;
      align-items: center;
      justify-content: center;
    }
  
    .hero-badge-text {
      font-size: 40rpx;
  font-weight: 900;
  color: $primary-orange;
}

.badge-glow {
  display: none;
}

.hero-title {
  font-size: 40rpx;
  font-weight: 700;
  color: $white;
  line-height: 1.3;
}
.hero-subtitle {
  font-size: 26rpx;
  color: rgba(255, 255, 255, 0.8);
}
.hero-right {
  flex-shrink: 0;
}

.hero-icon {
  font-size: 80rpx;
  opacity: 0.2;
}

.section-container {
  margin: 0 24rpx 40rpx;
}

.section-header {
  margin-bottom: 24rpx;
}

.section-title {
  font-size: 32rpx;
  font-weight: 600;
  color: $text-main;
}

.benefits-list {
  display: flex;
  flex-direction: column;
  gap: 20rpx;
}

.benefit-item {
  display: flex;
  flex-direction: row;
  align-items: center;
  gap: 24rpx;
    padding: 32rpx 24rpx;
    width: 100%;
    background: $white;
    border-radius: $radius-md;
    box-shadow: $shadow-sm;
}

.benefit-icon-wrapper {
  width: 80rpx;
  height: 80rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(243, 112, 33, 0.1);
  border-radius: 50%;
}

.benefit-number {
  font-size: 32rpx;
  font-weight: 700;
  color: $primary-orange;
}

.benefit-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 8rpx;
  text-align: left;
}

.benefit-title {
  font-size: 28rpx;
  font-weight: 600;
  color: $text-main;
}

.benefit-desc {
  font-size: 22rpx;
  color: $text-second;
  line-height: 1.4;
  word-wrap: break-word;
  word-break: break-all;
  overflow-wrap: break-word;
}

.package-scroll {
  white-space: nowrap;
  width: 100%;
}

.package-list {
  display: inline-flex;
  gap: 20rpx;
  padding: 4rpx 0;
}

.package-card {
  position: relative;
  display: inline-block;
    width: 320rpx;
  padding: 40rpx 32rpx;
  background: $white;
    border-radius: $radius-md;
    border: 2rpx solid $border-color;
    box-shadow: $shadow-sm;
    vertical-align: top;
  &.selected {
    border-color: $primary-orange;
    }

                &.popular {
                  border-color: rgba(243, 112, 33, 0.3);
                }

                &.premium {
                  border-color: rgba(139, 92, 246, 0.3);
  }
}

.package-header {
  display: flex;
  flex-direction: column;
    gap: 12rpx;
  margin-bottom: 24rpx;
}

.package-name-wrapper {
  display: flex;
  align-items: center;
  gap: 12rpx;
}

.package-name {
  font-size: 32rpx;
  font-weight: 700;
  color: $text-main;
  }
  
  .popular-tag {
    position: absolute;
    top: -12rpx;
    right: 24rpx;
    padding: 6rpx 20rpx;
    background: $primary-orange;
    border-radius: 999rpx;
    font-size: 20rpx;
    color: $white;
    font-weight: 600;
  }
  
  .premium-tag {
    position: absolute;
    top: -12rpx;
    right: 24rpx;
    padding: 6rpx 20rpx;
    background: #8B5CF6;
    border-radius: 999rpx;
    font-size: 20rpx;
    color: $white;
    font-weight: 600;
}

.limit-badge {
  position: absolute;
  top: -12rpx;
  right: 24rpx;
  padding: 6rpx 16rpx;
  background: #EF4444;
  border-radius: 999rpx;
  font-size: 20rpx;
    color: $white;
  font-weight: 600;
}

.package-price-row {
  display: flex;
  align-items: baseline;
  gap: 16rpx;
  margin-bottom: 16rpx;
}

.package-price {
  display: flex;
  align-items: baseline;
  gap: 4rpx;
}

.price-symbol {
  font-size: 28rpx;
    color: $primary-orange;
  font-weight: 600;
}

.price-value {
  font-size: 56rpx;
    color: $primary-orange;
    font-weight: 700;
  }
  
  .price-original {
    font-size: 24rpx;
    color: $text-second;
    text-decoration: line-through;
}

.package-desc {
  font-size: 24rpx;
    color: $text-second;
  line-height: 1.6;
  word-wrap: break-word;
    word-break: break-all;
    overflow-wrap: break-word;
    white-space: normal
}

.package-select-icon {
  position: absolute;
  top: 24rpx;
    right: 24rpx;
    width: 44rpx;
    height: 44rpx;
    background: $primary-orange;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.select-check {
  font-size: 26rpx;
    color: $white;
  font-weight: 700;
}

.more-seats-tip {
  margin-top: 24rpx;
  padding: 20rpx;
  background: rgba(243, 112, 33, 0.05);
  border-radius: $radius-sm;
  border-left: 4rpx solid $primary-orange;
}

.tip-text {
  font-size: 24rpx;
  color: $text-second;
}
.qr-card {
  padding: 40rpx;
  background: $white;
    border-radius: $radius-md;
    box-shadow: $shadow-sm;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 24rpx;
}

.qr-wrapper {
  width: 400rpx;
  height: 400rpx;
  padding: 24rpx;
  background: #F9FAFB;
    border-radius: $radius-sm;
    border: 2rpx dashed $border-color;
    display: flex;
    align-items: center;
    justify-content: center;
}

.qr-code {
  width: 100%;
  height: 100%;
  border-radius: $radius-sm;
}

.qr-hint {
  font-size: 24rpx;
  color: $text-second;
  text-align: center;
}

.qr-action {
  font-size: 28rpx;
  color: $text-main;
  font-weight: 600;
  text-align: center;
}

.bottom-gap {
  height: 40rpx;
}
</style>
