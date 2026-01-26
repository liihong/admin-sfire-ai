<template>
  <view class="power-index-page">
    <!-- 顶部装饰背景 -->
    <view class="bg-decoration">
      <view class="decoration-circle circle-1"></view>
      <view class="decoration-circle circle-2"></view>
    </view>

    <!-- 页面头部 -->
    <view class="page-header">
      <SafeAreaTop />
      <view class="header-back" @tap="goBack">
        <text class="back-icon">←</text>
      </view>
      <view class="header-content">
        <text class="header-title">我的算力</text>
        <text class="header-subtitle">查看算力余额和明细</text>
      </view>
    </view>

    <!-- 算力余额卡片 -->
    <view class="balance-card">
      <view class="balance-label">当前算力</view>
      <view class="balance-value-row">
        <text class="balance-value">{{ balance }}</text>
        <text class="balance-unit">算力</text>
      </view>
    </view>

    <!-- 快捷入口 -->
    <view class="quick-actions">
      <view class="action-item" @tap="goToRecharge">
        <view class="action-icon-wrapper recharge-icon">
          <text class="action-icon">💰</text>
        </view>
        <text class="action-text">充值算力</text>
      </view>
      <view class="action-item" @tap="goToDetail">
        <view class="action-icon-wrapper detail-icon">
          <text class="action-icon">📊</text>
        </view>
        <text class="action-text">算力明细</text>
      </view>
    </view>

    <!-- 最近交易记录 -->
    <view class="recent-transactions" v-if="recentTransactions.length > 0">
      <view class="section-title">最近交易</view>
      <view class="transaction-list">
        <view 
          class="transaction-item" 
          v-for="(item, index) in recentTransactions" 
          :key="item.id || index"
          @tap="goToDetail"
        >
          <view class="item-left">
            <view class="item-icon-wrapper" :class="getTypeClass(item.type)">
              <text class="item-icon">{{ getTypeIcon(item.type) }}</text>
            </view>
            <view class="item-info">
              <text class="item-title">{{ item.typeName || '算力变动' }}</text>
              <text class="item-time">{{ formatTime(item.create_time || item.created_at) }}</text>
            </view>
          </view>
          <view class="item-right">
            <text class="item-amount" :class="getAmountClass(item.amount)">
              {{ formatAmount(item.amount) }}
            </text>
          </view>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { getBalance, getCoinTransactions } from '@/api/coin'
import SafeAreaTop from '@/components/common/SafeAreaTop.vue'

// 余额
const balance = ref<string>('0')

// 最近交易记录
interface Transaction {
  id?: number | string
  type?: string
  typeName?: string
  amount?: number | string
  create_time?: string
  created_at?: string
}

const recentTransactions = ref<Transaction[]>([])
const isLoading = ref(false)

// 初始化
onMounted(() => {
  loadBalance()
  loadRecentTransactions()
})

// 加载余额
async function loadBalance() {
  try {
    const response = await getBalance()
    if (response.code === 200 && response.data) {
      balance.value = String(response.data.available_balance || 0)
    }
  } catch (error: any) {
    console.error('加载余额失败:', error)
  }
}

// 加载最近交易记录
async function loadRecentTransactions() {
  if (isLoading.value) return
  isLoading.value = true

  try {
    const response = await getCoinTransactions({
      pageNum: 1,
      pageSize: 5
    })

    if (response.code === 200 && response.data) {
      const data = response.data
      const list = data.list || data.records || []
      recentTransactions.value = list
    }
  } catch (error: any) {
    console.error('加载交易记录失败:', error)
  } finally {
    isLoading.value = false
  }
}

// 跳转到充值页面
function goToRecharge() {
  uni.navigateTo({
    url: '/pages/mine/power/recharge'
  })
}

// 跳转到明细页面
function goToDetail() {
  uni.navigateTo({
    url: '/pages/mine/power/detail'
  })
}

// 返回上一页
function goBack() {
  uni.navigateBack({
    fail: () => {
      uni.switchTab({ url: '/pages/mine/index' })
    }
  })
}

// 获取类型样式类
function getTypeClass(type?: string): string {
  if (!type) return 'type-default'
  const typeLower = type.toLowerCase()
  if (typeLower.includes('consume') || typeLower.includes('消耗') || typeLower.includes('deduct')) {
    return 'type-consume'
  }
  if (typeLower.includes('recharge') || typeLower.includes('充值') || typeLower.includes('add')) {
    return 'type-recharge'
  }
  return 'type-default'
}

// 获取类型图标
function getTypeIcon(type?: string): string {
  if (!type) return '💎'
  const typeLower = type.toLowerCase()
  if (typeLower.includes('consume') || typeLower.includes('消耗') || typeLower.includes('deduct')) {
    return '📉'
  }
  if (typeLower.includes('recharge') || typeLower.includes('充值') || typeLower.includes('add')) {
    return '📈'
  }
  return '💎'
}

// 获取金额样式类
function getAmountClass(amount?: number | string): string {
  if (!amount) return 'amount-default'
  const numAmount = typeof amount === 'string' ? parseFloat(amount) : amount
  if (numAmount < 0) return 'amount-negative'
  if (numAmount > 0) return 'amount-positive'
  return 'amount-default'
}

// 格式化金额
function formatAmount(amount?: number | string): string {
  if (amount === undefined || amount === null) return '0'
  const numAmount = typeof amount === 'string' ? parseFloat(amount) : amount
  if (numAmount > 0) return `+${numAmount}`
  return String(numAmount)
}

// 格式化时间
function formatTime(timeStr?: string): string {
  if (!timeStr) return ''
  
  try {
    const date = new Date(timeStr)
    const now = new Date()
    const diff = now.getTime() - date.getTime()

    const minutes = Math.floor(diff / 60000)
    const hours = Math.floor(diff / 3600000)
    const days = Math.floor(diff / 86400000)

    if (minutes < 1) return '刚刚'
    if (minutes < 60) return `${minutes}分钟前`
    if (hours < 24) return `${hours}小时前`
    if (days < 7) return `${days}天前`

    const month = date.getMonth() + 1
    const day = date.getDate()
    const year = date.getFullYear()
    const currentYear = now.getFullYear()
    
    if (year === currentYear) {
      return `${month}/${day}`
    }
    return `${year}/${month}/${day}`
  } catch (error) {
    return timeStr
  }
}
</script>

<style lang="scss" scoped>
.power-index-page {
  min-height: 100vh;
  background: #F5F7FA;
  position: relative;
  overflow: hidden;
  padding-bottom: 40rpx;
}

// 背景装饰
.bg-decoration {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 400rpx;
  pointer-events: none;
  overflow: hidden;

  .decoration-circle {
    position: absolute;
    border-radius: 50%;
    opacity: 0.6;
  }

  .circle-1 {
    width: 300rpx;
    height: 300rpx;
    background: linear-gradient(135deg, rgba(59, 130, 246, 0.15) 0%, rgba(59, 130, 246, 0.05) 100%);
    top: -100rpx;
    right: -50rpx;
  }

  .circle-2 {
    width: 200rpx;
    height: 200rpx;
    background: linear-gradient(135deg, rgba(249, 115, 22, 0.1) 0%, rgba(249, 115, 22, 0.03) 100%);
    top: 100rpx;
    left: -60rpx;
  }
}

// 页面头部
.page-header {
  position: relative;
  z-index: 10;
  padding: 60rpx 32rpx 40rpx;
  display: flex;
  align-items: center;
  gap: 24rpx;
}

.header-back {
  width: 64rpx;
  height: 64rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.9);
  box-shadow: 0 2rpx 12rpx rgba(0, 0, 0, 0.08);
}

.back-icon {
  font-size: 36rpx;
  color: #1f2937;
  font-weight: 600;
}

.header-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 8rpx;
}

.header-title {
  font-size: 44rpx;
  font-weight: 700;
  color: #1f2937;
}

.header-subtitle {
  font-size: 26rpx;
  color: #6b7280;
}

// 余额卡片
.balance-card {
  position: relative;
  z-index: 5;
  background: #ffffff;
  border-radius: 24rpx;
  padding: 48rpx 32rpx;
  margin: 0 32rpx 32rpx;
  box-shadow: 0 4rpx 24rpx rgba(99, 102, 241, 0.08);
}

.balance-label {
  font-size: 28rpx;
  color: #6b7280;
  margin-bottom: 16rpx;
}

.balance-value-row {
  display: flex;
  align-items: baseline;
  gap: 8rpx;
}

.balance-value {
  font-size: 72rpx;
  font-weight: 700;
  color: #f59e0b;
  font-family: 'DIN Alternate', 'Helvetica Neue', sans-serif;
}

.balance-unit {
  font-size: 32rpx;
  color: #6b7280;
  font-weight: 500;
}

// 快捷入口
.quick-actions {
  position: relative;
  z-index: 5;
  display: flex;
  gap: 24rpx;
  padding: 0 32rpx;
  margin-bottom: 32rpx;
}

.action-item {
  flex: 1;
  background: #ffffff;
  border-radius: 24rpx;
  padding: 32rpx;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16rpx;
  box-shadow: 0 2rpx 12rpx rgba(0, 0, 0, 0.04);
}

.action-icon-wrapper {
  width: 96rpx;
  height: 96rpx;
  border-radius: 24rpx;
  display: flex;
  align-items: center;
  justify-content: center;

  &.recharge-icon {
    background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%);
  }

  &.detail-icon {
    background: linear-gradient(135deg, #dbeafe 0%, #bfdbfe 100%);
  }
}

.action-icon {
  font-size: 48rpx;
}

.action-text {
  font-size: 28rpx;
  font-weight: 500;
  color: #1f2937;
}

// 最近交易
.recent-transactions {
  position: relative;
  z-index: 5;
  padding: 0 32rpx;
}

.section-title {
  font-size: 32rpx;
  font-weight: 600;
  color: #1f2937;
  margin-bottom: 24rpx;
}

.transaction-list {
  display: flex;
  flex-direction: column;
  gap: 16rpx;
}

.transaction-item {
  background: #ffffff;
  border-radius: 20rpx;
  padding: 24rpx;
  display: flex;
  align-items: center;
  justify-content: space-between;
  box-shadow: 0 2rpx 8rpx rgba(0, 0, 0, 0.04);
}

.item-left {
  display: flex;
  align-items: center;
  gap: 20rpx;
  flex: 1;
}

.item-icon-wrapper {
  width: 72rpx;
  height: 72rpx;
  border-radius: 16rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;

  &.type-consume {
    background: linear-gradient(135deg, #fee2e2 0%, #fecaca 100%);
  }

  &.type-recharge {
    background: linear-gradient(135deg, #dbeafe 0%, #bfdbfe 100%);
  }

  &.type-default {
    background: linear-gradient(135deg, #e0e7ff 0%, #c7d2fe 100%);
  }
}

.item-icon {
  font-size: 32rpx;
}

.item-info {
  display: flex;
  flex-direction: column;
  gap: 6rpx;
  flex: 1;
  min-width: 0;
}

.item-title {
  font-size: 28rpx;
  font-weight: 500;
  color: #1f2937;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.item-time {
  font-size: 22rpx;
  color: #9ca3af;
}

.item-right {
  display: flex;
  align-items: center;
  flex-shrink: 0;
}

.item-amount {
  font-size: 28rpx;
  font-weight: 600;
  font-family: 'DIN Alternate', 'Helvetica Neue', sans-serif;

  &.amount-positive {
    color: #ef4444;
  }

  &.amount-negative {
    color: #10b981;
  }

  &.amount-default {
    color: #6b7280;
  }
}
</style>

