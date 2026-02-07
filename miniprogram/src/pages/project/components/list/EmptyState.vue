<template>
  <view class="empty-state">
   <BaseHeader title="创建你操盘的IP" />
    <!-- 中心图形：浅橙色圆形 + 火焰图标 -->
    <view class="empty-icon-wrapper">
      <view class="empty-icon-circle">
        <text class="empty-icon-text">火</text>
      </view>
    </view>

    <!-- 主提示语 -->
    <text class="empty-title">万事俱备，只欠一把火</text>

    <!-- 详细说明 -->
    <view class="empty-desc-wrapper">
      <text class="empty-desc">创建一个 IP 项目，火源灵感火花会帮你</text>
      <text class="empty-desc">打理那些繁琐的创作流程</text>
    </view>

    <!-- 长按钮（使用公共样式） -->
    <view class="pill-button" @tap="handleAction">
      <SvgIcon name="add" size="40" color="#FFFFFF" />
      <text class="pill-button-text">开启第一个项目</text>
    </view>
  </view>
</template>

<script setup lang="ts">
import SvgIcon from '@/components/base/SvgIcon.vue'

// Emits
const emit = defineEmits<{
  action: [] // 点击按钮时触发
}>()

// 处理按钮点击
function handleAction() {
  emit('action')
}
</script>

<style lang="scss" scoped>
@import '@/styles/_variables.scss';
@import '@/styles/_components.scss';

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 120rpx 40rpx;
  min-height: 60vh;
}

// 中心图形容器
.empty-icon-wrapper {
  margin-bottom: 48rpx;
}

.empty-icon-circle {
  width: 200rpx;
  height: 200rpx;
  border-radius: 50%;
  background: #FFF2E6; // 浅橙色背景
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 4rpx 20rpx rgba(255, 136, 0, 0.1);
  position: relative;

  // 添加轻微的光晕效果
  &::after {
    content: '';
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    width: 180rpx;
    height: 180rpx;
    border-radius: 50%;
    background: radial-gradient(circle, rgba(255, 136, 0, 0.15) 0%, transparent 70%);
  }
}

.empty-icon-text {
  font-size: 100rpx;
  font-weight: 700;
  color: #FF8800; // 鲜艳的橙色
  position: relative;
  z-index: 1;
  line-height: 1;
}

// 主提示语
.empty-title {
  font-size: 44rpx;
  font-weight: 700;
  color: #898989; // 深黑色
  margin-bottom: 32rpx;
  text-align: center;
  letter-spacing: 1rpx;
}

// 详细说明容器
.empty-desc-wrapper {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8rpx;
  margin-bottom: 64rpx;
}

.empty-desc {
  font-size: 28rpx;
  color: #999999; // 浅灰色
  text-align: center;
  line-height: 1.6;
}
</style>
