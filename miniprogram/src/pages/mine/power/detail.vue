<template>
  <view class="power-detail-page">
    <!-- 顶部装饰背景 -->
    <view class="bg-decoration">
      <view class="decoration-circle circle-1"></view>
      <view class="decoration-circle circle-2"></view>
    </view>

    <!-- 页面头部 -->
    <view class="page-header">
      <!-- iPhone 灵动岛安全区适配 -->
      <SafeAreaTop />
      <view class="header-back" @tap="goBack">
        <text class="back-icon">←</text>
      </view>
      <view class="header-content">
        <text class="header-title">算力明细</text>
        <text class="header-subtitle">查看算力消耗记录</text>
      </view>
    </view>

    <!-- 列表区域 -->
    <scroll-view 
      class="list-wrapper" 
      scroll-y 
      :refresher-enabled="true" 
      @refresherrefresh="onRefresh"
      :refresher-triggered="isRefreshing"
      @scrolltolower="onLoadMore"
      :lower-threshold="100"
    >
      <!-- 空状态 -->
      <view class="empty-state" v-if="!isLoading && transactionList.length === 0">
        <view class="empty-icon">📊</view>
        <text class="empty-title">暂无算力消耗记录</text>
        <text class="empty-desc">您的算力消耗记录将显示在这里</text>
      </view>

      <!-- 明细列表 -->
      <view class="transaction-list" v-else>
        <view 
          class="transaction-item" 
          v-for="(item, index) in transactionList" 
          :key="item.id || index"
        >
        <view class="item-content">
          <view class="item-left">
            <view class="item-icon-wrapper" :class="getTypeClass(item.type)">
              <text class="item-icon">{{ getTypeIcon(item.type) }}</text>
            </view>
            <view class="item-info">
              <text class="item-title">{{  item.typeName || '算力消耗' }}</text>
              <text class="item-time">{{ formatTime(item.create_time || item.created_at) }}</text>
            </view>
          </view>
          <view class="item-right">
            <text class="item-amount" :class="getAmountClass(item.amount)">
              {{ item.amount }}
            </text>
          </view>
        </view>
          <view class="item-remark">
            {{ item.remark }}
            </view>
        </view>
      </view>

      <!-- 加载更多提示 -->
      <view class="load-more" v-if="transactionList.length > 0">
        <text class="load-more-text" v-if="isLoadingMore">加载中...</text>
        <text class="load-more-text" v-else-if="hasMore">上拉加载更多</text>
        <text class="load-more-text" v-else>没有更多数据了</text>
      </view>

      <!-- 底部占位 -->
      <view class="list-footer-spacer"></view>
    </scroll-view>

    <!-- Loading 状态 -->
    <view class="loading-overlay" v-if="isLoading && transactionList.length === 0">
      <view class="loading-spinner"></view>
      <text class="loading-text">加载中...</text>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { getCoinTransactions } from '@/api/coin'
import SafeAreaTop from '@/components/common/SafeAreaTop.vue'

// 交易记录类型
interface Transaction {
  id?: number | string
  type?: string
  typeName?: string
  amount?: number | string
  remark?: string
  create_time?: string
  created_at?: string
}

// 状态
const transactionList = ref<Transaction[]>([])
const isLoading = ref(false)
const isRefreshing = ref(false)
const isLoadingMore = ref(false)
const hasMore = ref(true)
const currentPage = ref(1)
const pageSize = ref(20)

// 初始化
onMounted(() => {
  loadTransactions(1, true)
})

// 加载交易记录
async function loadTransactions(pageNum: number, isRefresh: boolean = false) {
  // 防止重复加载
  if (isLoading.value || isLoadingMore.value) return
  
  if (isRefresh) {
    isLoading.value = true
    currentPage.value = 1
  } else {
    isLoadingMore.value = true
  }

  try {
    const response = await getCoinTransactions({
      pageNum,
      pageSize: pageSize.value
    })

    // 后端返回格式: {code: 200, data: {list: [...], total: ...}, msg: "..."}
    if (response.code === 200 && response.data) {
      const data = response.data
      // 处理不同的响应结构
      const list = data.list || data.records || []
      const total = data.total || data.totalCount || 0

      if (isRefresh) {
        transactionList.value = list
      } else {
        transactionList.value = [...transactionList.value, ...list]
      }

      // 判断是否还有更多数据
      const currentTotal = transactionList.value.length
      hasMore.value = currentTotal < total && list.length === pageSize.value

      if (!isRefresh) {
        currentPage.value = pageNum
      }
    } else {
      uni.showToast({
        title: (response as any).msg || '加载失败',
        icon: 'none'
      })
    }
  } catch (error: any) {
    console.error('加载算力明细失败:', error)
    uni.showToast({
      title: error.message || '加载失败，请稍后重试',
      icon: 'none'
    })
  } finally {
    isLoading.value = false
    isLoadingMore.value = false
    isRefreshing.value = false
  }
}

// 下拉刷新
async function onRefresh() {
  isRefreshing.value = true
  await loadTransactions(1, true)
}

// 加载更多
function onLoadMore() {
  if (!hasMore.value || isLoadingMore.value || isLoading.value) return
  loadTransactions(currentPage.value + 1, false)
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

    // 超过7天显示具体日期
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
.power-detail-page {
  min-height: 100vh;
  background: #F5F7FA;
  position: relative;
  overflow: hidden;
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

// 列表区域
.list-wrapper {
  position: relative;
  z-index: 5;
  height: calc(100vh - 200rpx);
  padding: 0 32rpx;
}

// 空状态
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 120rpx 40rpx;
  text-align: center;
}

.empty-icon {
  font-size: 120rpx;
  margin-bottom: 32rpx;
  opacity: 0.6;
}

.empty-title {
  font-size: 32rpx;
  font-weight: 600;
  color: #1f2937;
  margin-bottom: 16rpx;
}

.empty-desc {
  font-size: 28rpx;
  color: #6b7280;
}

// 交易列表
.transaction-list {
  padding-bottom: 40rpx;
}

.transaction-item {
  background: #ffffff;
  border-radius: 24rpx;
  padding: 32rpx;
  margin-bottom: 24rpx;
  box-shadow: 0 2rpx 12rpx rgba(0, 0, 0, 0.04);
}
.item-content {
  padding: 12rpx;
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.item-left {
  display: flex;
  align-items: center;
  gap: 24rpx;
  flex: 1;
}

.item-icon-wrapper {
  width: 88rpx;
  height: 88rpx;
  border-radius: 20rpx;
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
  font-size: 40rpx;
}

.item-info {
  display: flex;
  flex-direction: column;
  gap: 8rpx;
  flex: 1;
  min-width: 0;
}

.item-title {
  font-size: 30rpx;
  font-weight: 600;
  color: #1f2937;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.item-time {
  font-size: 24rpx;
  color: #9ca3af;
}

.item-right {
  display: flex;
  align-items: center;
  flex-shrink: 0;
}
.item-remark{
    font-size: 24rpx;
    color: #9ca3af;
    margin-top: 16rpx;
}

.item-amount {
  font-size: 32rpx;
  font-weight: 700;
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

// 加载更多
.load-more {
  padding: 40rpx 0;
  text-align: center;
}

.load-more-text {
  font-size: 26rpx;
  color: #9ca3af;
}

// 底部占位
.list-footer-spacer {
  height: 40rpx;
}

// Loading 状态
.loading-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(255, 255, 255, 0.9);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  z-index: 100;
}

.loading-spinner {
  width: 60rpx;
  height: 60rpx;
  border: 4rpx solid #e5e7eb;
  border-top-color: #3b82f6;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 24rpx;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.loading-text {
  font-size: 28rpx;
  color: #6b7280;
}
</style>

