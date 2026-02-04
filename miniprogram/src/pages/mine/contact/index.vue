<template>
  <view class="page-container">
    <!-- 提示信息卡片 -->
    <view class="info-card">
      <view class="info-icon">ℹ️</view>
      <text class="info-text">想体验全部功能需要开通Pro会员权限</text>
    </view>

    <!-- 二维码卡片 -->
    <view class="qrcode-card">
      <text class="qrcode-title">扫码联系客服</text>
      <view class="qrcode-wrapper">
       <image :show-menu-by-longpress="true"
          class="qrcode-image" 
          src="/static/qrcode-placeholder.png" 
          mode="aspectFit"
        />
      </view>
      <text class="qrcode-tip">请使用微信扫描上方二维码</text>
    </view>
  </view>
</template>

<script setup lang="ts">
// 客服页面 - 显示客服二维码
</script>

<style scoped>
.page-container {
  min-height: 100vh;
  background: linear-gradient(180deg, #f0f5ff 0%, #f5f7fa 100%);
  padding: 24rpx;
  box-sizing: border-box;
}

/* 提示信息卡片 */
.info-card {
  background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
  border-radius: 24rpx;
  padding: 32rpx;
  margin-bottom: 24rpx;
  display: flex;
  align-items: center;
  gap: 20rpx;
  box-shadow: 0 8rpx 24rpx rgba(59, 130, 246, 0.25);
}

.info-icon {
  font-size: 48rpx;
  flex-shrink: 0;
}

.info-text {
  font-size: 30rpx;
  color: #ffffff;
  font-weight: 600;
  line-height: 1.6;
  flex: 1;
}

/* 二维码卡片 */
.qrcode-card {
  background: #ffffff;
  border-radius: 24rpx;
  padding: 48rpx 32rpx;
  display: flex;
  flex-direction: column;
  align-items: center;
  box-shadow: 0 4rpx 24rpx rgba(99, 102, 241, 0.08);
}

.qrcode-title {
  font-size: 32rpx;
  font-weight: 600;
  color: #1f2937;
  margin-bottom: 40rpx;
}

.qrcode-wrapper {
  width: 480rpx;
  height: 480rpx;
  background: #f9fafb;
  border-radius: 16rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 2rpx dashed #d1d5db;
  margin-bottom: 32rpx;
  overflow: hidden;
}

.qrcode-image {
  width: 100%;
  height: 100%;
  border-radius: 12rpx;
}

.qrcode-tip {
  font-size: 26rpx;
  color: #6b7280;
  font-weight: 500;
}
</style>