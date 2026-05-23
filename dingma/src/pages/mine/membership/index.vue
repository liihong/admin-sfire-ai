<template>
  <view class="page-wrapper">
    <scroll-view scroll-y class="page-container">
      <view class="page-content">
        <SafeAreaTop />
        <view class="top-nav">
          <view class="back-btn" @tap="goBack">
            <text class="back-icon">‹</text>
          </view>
        </view>

        <!-- 顶妈会员年卡 -->
        <view class="price-card">
          <view class="price-tag">限时特惠</view>
          <text class="price-name">顶妈会员年卡</text>
          <text class="price-desc">全年畅享会员所有特权，让创业更简单一点</text>
          <view class="price-divider" />
          <view class="price-row">
            <view class="price-main">
              <text class="price-symbol">¥</text>
              <text class="price-value">365</text>
              <text class="price-unit">/年</text>
              <text class="price-original">原价 ¥599</text>
            </view>
          </view>
          <view class="price-tip">
            <text class="price-tip-text">🔥 每天仅需 1 元钱，智囊随身带</text>
          </view>
        </view>
        <!-- 尊享会员特权卡片 -->
        <view class="benefits-card">
          <view class="section-heading">
            <view class="heading-bar" />
            <text class="heading-title">专属四大核心权益</text>
          </view>
          <view class="benefits-list">
            <view
              v-for="(benefit, index) in benefitsList"
              :key="index"
              class="benefit-item"
            >
              <view class="benefit-icon-wrap" :class="benefit.iconBg">
                <SvgIcon :name="benefit.icon" :size="40" :color="benefit.iconColor" />
              </view>
              <view class="benefit-text">
                <text class="benefit-title">{{ benefit.title }}</text>
                <text class="benefit-desc">{{ benefit.desc }}</text>
              </view>
            </view>
          </view>
        </view>

        <!-- 底部署名说明与开通按钮 -->
        <view class="cta-section">
          <view class="cta-btn" @tap="goOpenContact">
            <text class="cta-check">✓</text>
            <text class="cta-text">联系开通会员</text>
          </view>
          <view class="agreement-row">
            <text class="agreement-text">开通即代表您同意</text>
            <text class="agreement-link" @tap.stop="openUserAgreement">《会员服务协议》</text>
            <text class="agreement-text">与</text>
            <text class="agreement-link" @tap.stop="openPrivacyPolicy">《隐私政策》</text>
          </view>
        </view>

        <view class="bottom-gap" />
      </view>
    </scroll-view>
  </view>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import SafeAreaTop from '@/components/common/SafeAreaTop.vue'
import SvgIcon from '@/components/base/SvgIcon.vue'

const goBack = () => {
  uni.navigateBack({
    fail: () => {
      uni.switchTab({ url: '/pages/mine/index' })
    }
  })
}

const goOpenContact = () => {
  uni.navigateTo({ url: '/pages/mine/contact/index' })
}

const openUserAgreement = () => {
  uni.navigateTo({ url: '/pages/agreement/user' })
}

const openPrivacyPolicy = () => {
  uni.navigateTo({ url: '/pages/agreement/privacy' })
}

const benefitsList = ref([
  {
    icon: 'linggan',
    iconColor: '#D97706',
    iconBg: 'icon-bg-amber',
    title: '顶妈数字大脑 · 帮你思考',
    desc: '告别没思路、群冷场！帮你分析客群心理、规划群发售方向，像创业军师一样给你出谋划策。'
  },
  {
    icon: 'book',
    iconColor: '#F43F5E',
    iconBg: 'icon-bg-rose',
    title: '爆款创作专家 · 帮你写文案',
    desc: '秒出极富真实烟火气的朋友圈文案、高转化接龙话术、吸睛短视频脚本，零门槛轻松掌握网感。'
  },
  {
    icon: 'suanli',
    iconColor: '#3B82F6',
    iconBg: 'icon-bg-blue',
    title: '超值算力狂送 · 灵感不设限',
    desc: '赠送大额高优先级 VIP 专属算力，AI 创作秒速响应。多场景一键无阻生文，彻底告别额度焦虑。'
  },
  {
    icon: 'hotspot',
    iconColor: '#10B981',
    iconBg: 'icon-bg-emerald',
    title: '专属私域护航 · 帮你做营销',
    desc: '顶妈全套私域成交心法加持。手把手教你群暖群破冰、如何高情商对答嫌贵、促成快速成交。'
  }
])
</script>

<style scoped lang="scss">
@import '@/styles/_variables.scss';

.page-wrapper {
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: $bg-base;
  overflow: hidden;
}

.page-container {
  flex: 1;
  height: 0;
  background: $bg-base;
}

.page-content {
  padding: 0 40rpx 0;
}

.top-nav {
  padding: 16rpx 0 24rpx;
}

.back-btn {
  width: 64rpx;
  height: 64rpx;
  border-radius: 50%;
  background: $white;
  box-shadow: 0 4rpx 16rpx rgba(0, 0, 0, 0.06);
  display: flex;
  align-items: center;
  justify-content: center;
}

.back-icon {
  font-size: 40rpx;
  color: #1f2937;
  font-weight: 600;
  line-height: 1;
  margin-top: -4rpx;
}

.benefits-card {
  background: $white;
  border-radius: 48rpx;
  padding: 48rpx;
  border: 1rpx solid #f1f5f9;
  box-shadow: 0 20rpx 60rpx -10rpx rgba(0, 0, 0, 0.04);
  margin-bottom: 48rpx;
}

.section-heading {
  display: flex;
  align-items: center;
  gap: 16rpx;
  margin-bottom: 40rpx;
}

.heading-bar {
  width: 8rpx;
  height: 32rpx;
  background: $primary-orange;
  border-radius: 999rpx;
  flex-shrink: 0;
}

.heading-title {
  font-size: 28rpx;
  font-weight: 900;
  color: #1e293b;
}

.benefits-list {
  display: flex;
  flex-direction: column;
  gap: 16rpx;
}

.benefit-item {
  display: flex;
  gap: 32rpx;
  padding: 24rpx;
  border-radius: 32rpx;
}

.benefit-icon-wrap {
  width: 88rpx;
  height: 88rpx;
  border-radius: 24rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  box-shadow: $shadow-sm;
}

.icon-bg-amber {
  background: #fef3c7;
}

.icon-bg-rose {
  background: #fff1f2;
}

.icon-bg-blue {
  background: #eff6ff;
}

.icon-bg-emerald {
  background: #ecfdf5;
}

.benefit-text {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 8rpx;
  min-width: 0;
}

.benefit-title {
  font-size: 28rpx;
  font-weight: 700;
  color: #1e293b;
  line-height: 1.4;
}

.benefit-desc {
  font-size: 22rpx;
  font-weight: 500;
  color: #64748b;
  line-height: 1.6;
}

/* ========== 价格卡片 ========== */
.price-card {
  position: relative;
  overflow: hidden;
  background: linear-gradient(135deg, #fffbeb 0%, #fff7ed 50%, #fff1f2 100%);
  border: 1rpx solid rgba(252, 211, 77, 0.5);
  border-radius: 48rpx;
  padding: 48rpx;
  box-shadow: $shadow-sm;
  margin-bottom: 32rpx;
}

.price-tag {
  position: absolute;
  top: 0;
  right: 0;
  padding: 12rpx 32rpx;
  background: linear-gradient(90deg, $accent-gold 0%, $terracotta-red 100%);
  border-radius: 0 0 0 32rpx;
  font-size: 20rpx;
  font-weight: 900;
  color: $white;
}

.price-name {
  display: block;
  font-size: 30rpx;
  font-weight: 900;
  color: #1e293b;
  margin-bottom: 12rpx;
  padding-right: 120rpx;
}

.price-desc {
  display: block;
  font-size: 22rpx;
  color: #64748b;
  line-height: 1.6;
}

.price-divider {
  margin: 40rpx 0 32rpx;
  height: 1rpx;
  background: rgba(252, 211, 77, 0.3);
}

.price-row {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
}

.price-main {
  display: flex;
  align-items: baseline;
  flex-wrap: wrap;
  gap: 4rpx;
}

.price-symbol {
  font-size: 36rpx;
  font-weight: 900;
  color: $accent-gold;
}

.price-value {
  font-size: 60rpx;
  font-weight: 900;
  color: $accent-gold;
  line-height: 1;
}

.price-unit {
  font-size: 24rpx;
  font-weight: 700;
  color: rgba(164, 112, 54, 0.9);
}

.price-original {
  font-size: 24rpx;
  color: #94a3b8;
  text-decoration: line-through;
  margin-left: 16rpx;
  font-weight: 500;
}

.price-tip {
  margin-top: 24rpx;
}

.price-tip-text {
  display: inline-block;
  font-size: 20rpx;
  font-weight: 700;
  color: rgba(146, 64, 14, 0.85);
  background: rgba(252, 211, 77, 0.3);
  padding: 8rpx 16rpx;
  border-radius: 12rpx;
}

/* ========== 底部 CTA ========== */
.cta-section {
  padding-top: 8rpx;
}

.cta-btn {
  width: 100%;
  height: 96rpx;
  background: linear-gradient(135deg, $accent-gold 0%, $accent-gold-deep 100%);
  border-radius: 32rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 16rpx;
  box-shadow: 0 12rpx 32rpx rgba(197, 139, 73, 0.28);
}

.cta-check {
  font-size: 32rpx;
  color: $white;
  font-weight: 700;
}

.cta-text {
  font-size: 32rpx;
  font-weight: 700;
  color: $white;
  letter-spacing: 2rpx;
}

.agreement-row {
  margin-top: 24rpx;
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  align-items: center;
  gap: 4rpx;
}

.agreement-text {
  font-size: 20rpx;
  color: #94a3b8;
  font-weight: 500;
}

.agreement-link {
  font-size: 20rpx;
  color: #64748b;
  font-weight: 500;
}

.bottom-gap {
  height: calc(40rpx + env(safe-area-inset-bottom));
}
</style>
