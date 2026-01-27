<template>
  <view class="recharge-page">
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
        <text class="header-title">充值算力</text>
        <text class="header-subtitle">选择套餐充值</text>
      </view>
    </view>

    <!-- 当前算力余额 -->
    <view class="balance-section">
      <view class="balance-label">当前算力</view>
      <view class="balance-value-row">
        <text class="balance-value">{{ balance }}</text>
        <text class="balance-unit">算力</text>
      </view>
    </view>

    <!-- 套餐列表 -->
    <scroll-view class="package-list-wrapper" scroll-y>
      <view class="package-list" v-if="packages.length > 0">
        <PackageCard
          v-for="pkg in packages"
          :key="pkg.id"
          :package="pkg"
          @click="handlePackageClick"
        />
      </view>

      <!-- 加载状态 -->
      <view class="loading-state" v-if="isLoading">
        <view class="loading-spinner"></view>
        <text class="loading-text">加载中...</text>
      </view>

      <!-- 空状态 -->
      <view class="empty-state" v-if="!isLoading && packages.length === 0">
        <view class="empty-icon">📦</view>
        <text class="empty-title">暂无套餐</text>
        <text class="empty-desc">套餐正在准备中，请稍后再试</text>
      </view>

      <!-- 底部占位 -->
      <view class="list-footer-spacer"></view>
    </scroll-view>
  </view>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { getPackages, createRechargeOrder, queryOrderStatus } from '@/api/recharge'
import { getBalance } from '@/api/coin'
import type { Package } from '@/api/recharge'
import PackageCard from './components/PackageCard.vue'
import SafeAreaTop from '@/components/common/SafeAreaTop.vue'

// 余额
const balance = ref<string>('0')

// 套餐列表
const packages = ref<Package[]>([])
const isLoading = ref(false)

// 初始化
onMounted(() => {
  loadBalance()
  loadPackages()
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

// 加载套餐列表
async function loadPackages() {
  if (isLoading.value) return
  isLoading.value = true

  try {
    const response = await getPackages()
    if (response.code === 200 && response.data) {
      packages.value = response.data
    } else {
      uni.showToast({
        title: response.msg || '加载套餐失败',
        icon: 'none'
      })
    }
  } catch (error: any) {
    console.error('加载套餐失败:', error)
    uni.showToast({
      title: error.message || '加载失败，请稍后重试',
      icon: 'none'
    })
  } finally {
    isLoading.value = false
  }
}

// 处理套餐点击
async function handlePackageClick(pkg: Package) {
  try {
    // 创建订单
    uni.showLoading({
      title: '创建订单中...',
      mask: true
    })

    const orderResponse = await createRechargeOrder({
      package_id: pkg.id
    })

    if (orderResponse.code !== 200 || !orderResponse.data) {
      uni.hideLoading()
      uni.showToast({
        title: orderResponse.msg || '创建订单失败',
        icon: 'none'
      })
      return
    }

    const orderData = orderResponse.data
    const paymentParams = orderData.payment_params

    uni.hideLoading()

    // 调用微信支付
    uni.requestPayment({
      provider: 'wxpay',
      timeStamp: paymentParams.timeStamp,
      nonceStr: paymentParams.nonceStr,
      package: paymentParams.package,
      signType: paymentParams.signType,
      paySign: paymentParams.paySign,
      success: async (res) => {
        console.log('支付成功:', res)
        
        // 支付成功，查询订单状态
        await checkOrderStatus(orderData.order_id)
        
        uni.showToast({
          title: '充值成功',
          icon: 'success'
        })
        
        // 刷新余额
        await loadBalance()
        
        // 延迟返回上一页
        setTimeout(() => {
          uni.navigateBack()
        }, 1500)
      },
      fail: (err) => {
        console.error('支付失败:', err)
        
        if (err.errMsg && err.errMsg.includes('cancel')) {
          uni.showToast({
            title: '支付已取消',
            icon: 'none'
          })
        } else {
          uni.showToast({
            title: '支付失败，请重试',
            icon: 'none'
          })
        }
      }
    })
  } catch (error: any) {
    uni.hideLoading()
    console.error('创建订单失败:', error)
    uni.showToast({
      title: error.message || '创建订单失败，请重试',
      icon: 'none'
    })
  }
}

// 查询订单状态
async function checkOrderStatus(orderId: string) {
  try {
    const response = await queryOrderStatus(orderId)
    if (response.code === 200 && response.data) {
      console.log('订单状态:', response.data)
    }
  } catch (error: any) {
    console.error('查询订单状态失败:', error)
  }
}

// 返回上一页
function goBack() {
  uni.navigateBack({
    fail: () => {
      uni.switchTab({ url: '/pages/mine/index' })
    }
  })
}
</script>

<style lang="scss" scoped>
.recharge-page {
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

// 余额区域
.balance-section {
  position: relative;
  z-index: 5;
  background: #ffffff;
  border-radius: 24rpx;
  padding: 32rpx;
  margin: 0 32rpx 24rpx;
  box-shadow: 0 4rpx 24rpx rgba(99, 102, 241, 0.08);
}

.balance-label {
  font-size: 26rpx;
  color: #6b7280;
  margin-bottom: 12rpx;
}

.balance-value-row {
  display: flex;
  align-items: baseline;
  gap: 8rpx;
}

.balance-value {
  font-size: 56rpx;
  font-weight: 700;
  color: #f59e0b;
  font-family: 'DIN Alternate', 'Helvetica Neue', sans-serif;
}

.balance-unit {
  font-size: 28rpx;
  color: #6b7280;
  font-weight: 500;
}

// 套餐列表
.package-list-wrapper {
  position: relative;
  z-index: 5;
  height: calc(100vh - 400rpx);
  padding: 0 32rpx;
}

.package-list {
  padding-bottom: 40rpx;
}

// 加载状态
.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 120rpx 40rpx;
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

// 底部占位
.list-footer-spacer {
  height: 40rpx;
}
</style>


