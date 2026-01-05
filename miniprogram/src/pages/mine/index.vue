<template>
  <view class="page-container">
    <!-- 用户信息卡片 -->
    <view class="user-card">
      <view class="user-info">
        <view class="avatar-wrapper">
          <image 
            class="avatar" 
            :src="userInfo.avatar || '/static/default-avatar.png'" 
            mode="aspectFill"
          />
        </view>
        <view class="user-details">
          <text class="phone-number">{{ userInfo.phone }}</text>
          <view class="tags-row">
            <view class="vip-tag">
              <text class="vip-text">VIP会员</text>
            </view>
            <view class="expire-tag">
              <text class="expire-text">{{ userInfo.expireDate }}过期</text>
            </view>
          </view>
        </view>
      </view>
    </view>

    <!-- 我的算力卡片 -->
    <view class="stat-card">
      <view class="stat-header">
        <text class="stat-title">我的算力</text>
        <text class="stat-link" @tap="goToDetail('power')">算力明细 ›</text>
      </view>
      <view class="stat-value-row">
        <text class="stat-number">{{ userInfo.power }}</text>
        <text class="stat-unit">算力</text>
      </view>
    </view>

    <!-- 合伙人卡片 -->
    <view class="partner-card">
      <view class="stat-header">
        <text class="stat-title">合伙人 - {{ userInfo.partnerStatus }}</text>
        <text class="stat-link" @tap="goToDetail('asset')">资产明细 ›</text>
      </view>
      <view class="stat-value-row">
        <text class="stat-number">{{ userInfo.balance }}</text>
        <text class="stat-unit">元</text>
      </view>
      <view class="action-buttons">
        <view class="btn-primary" @tap="handleWithdraw">
          <text class="btn-text-primary">申请提现</text>
        </view>
        <view class="btn-outline" @tap="handleInvite">
          <text class="btn-text-outline">邀请好友</text>
        </view>
      </view>
    </view>

    <!-- 功能列表 -->
    <view class="menu-card">
      <view 
        v-for="(item, index) in menuList" 
        :key="index" 
        class="menu-item"
        :class="{ 'menu-item-border': index < menuList.length - 1 }"
        @tap="handleMenuClick(item)"
      >
        <view class="menu-left">
          <view class="menu-icon-wrapper" :style="{ background: item.iconBg }">
            <text class="menu-icon">{{ item.icon }}</text>
          </view>
          <text class="menu-name">{{ item.name }}</text>
        </view>
        <text class="menu-arrow">›</text>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'

// 用户信息 Mock 数据
const userInfo = reactive({
  avatar: '',
  phone: '132****6633',
  expireDate: '2026-01-24',
  power: '3678',
  balance: '0.00',
  partnerStatus: '待成为合伙人'
})

// 功能菜单 Mock 数据
const menuList = ref([
  {
    id: 'digital-human',
    name: '我的数字人',
    icon: '👤',
    iconBg: 'linear-gradient(135deg, #e0e7ff 0%, #c7d2fe 100%)',
    path: '/pages/digital-human/index'
  },
  {
    id: 'works',
    name: '我的作品',
    icon: '📊',
    iconBg: 'linear-gradient(135deg, #fef3c7 0%, #fde68a 100%)',
    path: '/pages/works/index'
  },
  {
    id: 'help',
    name: '帮助与反馈',
    icon: '❓',
    iconBg: 'linear-gradient(135deg, #dbeafe 0%, #bfdbfe 100%)',
    path: '/pages/help/index'
  }
])

// 跳转到明细页面
const goToDetail = (type: string) => {
  uni.showToast({
    title: type === 'power' ? '查看算力明细' : '查看资产明细',
    icon: 'none'
  })
}

// 申请提现
const handleWithdraw = () => {
  uni.showToast({
    title: '申请提现功能开发中',
    icon: 'none'
  })
}

// 邀请好友
const handleInvite = () => {
  uni.showToast({
    title: '邀请好友功能开发中',
    icon: 'none'
  })
}

// 菜单点击
const handleMenuClick = (item: any) => {
  uni.showToast({
    title: `进入${item.name}`,
    icon: 'none'
  })
}
</script>

<style scoped>
.page-container {
  min-height: 100vh;
  background: linear-gradient(180deg, #f0f5ff 0%, #f5f7fa 100%);
  padding: 24rpx;
  padding-bottom: 180rpx;
  box-sizing: border-box;
}

/* 用户信息卡片 */
.user-card {
  background: #ffffff;
  border-radius: 24rpx;
  padding: 32rpx;
  margin-bottom: 24rpx;
  box-shadow: 0 4rpx 24rpx rgba(99, 102, 241, 0.08);
}

.user-info {
  display: flex;
  align-items: center;
  gap: 24rpx;
}

.avatar-wrapper {
  width: 120rpx;
  height: 120rpx;
  border-radius: 50%;
  background: linear-gradient(135deg, #e0e7ff 0%, #c7d2fe 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  flex-shrink: 0;
}

.avatar {
  width: 100%;
  height: 100%;
}

.user-details {
  display: flex;
  flex-direction: column;
  gap: 16rpx;
}

.phone-number {
  font-size: 40rpx;
  font-weight: 700;
  color: #1f2937;
}

.tags-row {
  display: flex;
  align-items: center;
  gap: 16rpx;
}

.vip-tag {
  background: linear-gradient(135deg, #fbbf24 0%, #f59e0b 100%);
  padding: 6rpx 16rpx;
  border-radius: 8rpx;
}

.vip-text {
  font-size: 24rpx;
  color: #ffffff;
  font-weight: 600;
}

.expire-tag {
  border: 2rpx solid #3b82f6;
  padding: 6rpx 16rpx;
  border-radius: 8rpx;
  background: rgba(59, 130, 246, 0.05);
}

.expire-text {
  font-size: 24rpx;
  color: #3b82f6;
  font-weight: 500;
}

/* 统计卡片通用样式 */
.stat-card,
.partner-card {
  background: #ffffff;
  border-radius: 24rpx;
  padding: 32rpx;
  margin-bottom: 24rpx;
  box-shadow: 0 4rpx 24rpx rgba(99, 102, 241, 0.08);
}

.stat-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16rpx;
}

.stat-title {
  font-size: 30rpx;
  font-weight: 600;
  color: #1f2937;
}

.stat-link {
  font-size: 26rpx;
  color: #3b82f6;
  font-weight: 500;
}

.stat-value-row {
  display: flex;
  align-items: baseline;
  gap: 8rpx;
}

.stat-number {
  font-size: 64rpx;
  font-weight: 700;
  color: #f59e0b;
  font-family: 'DIN Alternate', 'Helvetica Neue', sans-serif;
}

.stat-unit {
  font-size: 28rpx;
  color: #6b7280;
  font-weight: 500;
}

/* 操作按钮 */
.action-buttons {
  display: flex;
  gap: 24rpx;
  margin-top: 32rpx;
}

.btn-primary {
  flex: 1;
  height: 88rpx;
  background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
  border-radius: 44rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 8rpx 24rpx rgba(59, 130, 246, 0.35);
}

.btn-text-primary {
  font-size: 30rpx;
  color: #ffffff;
  font-weight: 600;
}

.btn-outline {
  flex: 1;
  height: 88rpx;
  background: #ffffff;
  border: 2rpx solid #3b82f6;
  border-radius: 44rpx;
  display: flex;
  align-items: center;
  justify-content: center;
}

.btn-text-outline {
  font-size: 30rpx;
  color: #3b82f6;
  font-weight: 600;
}

/* 功能菜单卡片 */
.menu-card {
  background: #ffffff;
  border-radius: 24rpx;
  overflow: hidden;
  box-shadow: 0 4rpx 24rpx rgba(99, 102, 241, 0.08);
}

.menu-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 32rpx;
}

.menu-item-border {
  border-bottom: 1rpx solid #f3f4f6;
}

.menu-left {
  display: flex;
  align-items: center;
  gap: 20rpx;
}

.menu-icon-wrapper {
  width: 72rpx;
  height: 72rpx;
  border-radius: 18rpx;
  display: flex;
  align-items: center;
  justify-content: center;
}

.menu-icon {
  font-size: 36rpx;
}

.menu-name {
  font-size: 30rpx;
  font-weight: 500;
  color: #1f2937;
}

.menu-arrow {
  font-size: 36rpx;
  color: #9ca3af;
  font-weight: 300;
}

/* 按钮点击效果 */
.btn-primary:active {
  opacity: 0.9;
  transform: scale(0.98);
}

.btn-outline:active {
  background: rgba(59, 130, 246, 0.05);
}

.menu-item:active {
  background: #f9fafb;
}
</style>

