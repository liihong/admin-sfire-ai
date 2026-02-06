<template>
  <view class="base-header" :class="customClass">
    <!-- 顶部装饰背景（可选） -->
    <view v-if="showDecoration" class="bg-decoration">
      <view class="decoration-circle circle-1"></view>
      <view class="decoration-circle circle-2"></view>
    </view>
<!-- iPhone 灵动岛安全区适配 -->
<view 
    class="safe-area-top" 
    :style="{ height: safeAreaHeight + 'rpx' }"
  ></view>
    <!-- 页面头部 -->
    <view class="header-container">
        <view class="header-back" @tap="handleBack">
          <text class="back-icon">‹</text>
        </view>
      <view class="header-content-wrapper">
        
        <view class="header-content">
          <text class="header-title">{{ title }}</text>
          <text v-if="subtitle" class="header-subtitle">{{ subtitle }}</text>
        </view>
        <!-- 右侧插槽 -->
        <view v-if="$slots.right" class="header-right">
          <slot name="right"></slot>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
interface Props {
  // 标题
  title: string
  // 副标题（可选）
  subtitle?: string
  // 是否显示装饰背景
  showDecoration?: boolean
  // 自定义样式类
  customClass?: string
}

const props = withDefaults(defineProps<Props>(), {
  subtitle: '',
  showDecoration: false,
  customClass: ''
})

// 返回事件
const emit = defineEmits<{
  back: []
}>()

// 处理返回
function handleBack() {
  emit('back')
  // 默认行为：返回上一页
  uni.navigateBack({
    fail: () => {
      uni.switchTab({ url: '/pages/mine/index' })
    }
  })
}

// 安全区高度（rpx）
const safeAreaHeight = ref(0)

onMounted(() => {
  try {
    // 使用微信官方 API 获取安全区域信息（推荐方案）
    const systemInfo = uni.getSystemInfoSync()
    const safeAreaInsets = (systemInfo.safeAreaInsets as { top?: number; bottom?: number; left?: number; right?: number }) || {}
    const statusBarHeight = systemInfo.statusBarHeight || 0
    
    // 优先使用 safeAreaInsets.top，否则使用 statusBarHeight
    // 注意：uni.getSystemInfoSync() 返回的是 px，需要转换为 rpx（乘以 2）
    const topHeight = safeAreaInsets.top || statusBarHeight || 0
    safeAreaHeight.value = topHeight * 2 // px 转 rpx

  } catch (error) {
    console.warn('[SafeAreaTop] 获取安全区域信息失败:', error)
    safeAreaHeight.value = 0
  }
})

</script>

<style lang="scss" scoped>
.base-header {
  z-index: 100;
  background: transparent;
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

// 头部容器
.header-container {
  position: relative;
  z-index: 10;
  display: flex;
    align-items: center;
    justify-content: center;
    padding-bottom: 10rpx;
}

// 头部内容包装器
.header-content-wrapper {
  display: flex;
  align-items: center;
  text-align: center;
  gap: 24rpx;
}

// 返回按钮
.header-back {
  width: 64rpx;
  height: 64rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.9);
  box-shadow: 0 2rpx 12rpx rgba(0, 0, 0, 0.08);
  flex-shrink: 0;
  position: absolute;
left: 15px;
}

.back-icon {
  font-size: 36rpx;
  color: #1f2937;
  font-weight: 600;
}

// 头部内容
.header-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 8rpx;
  min-width: 0;
}

.header-title {
  font-size: 32rpx;
  font-weight: 700;
  color: #1f2937;
}

.header-subtitle {
  font-size: 26rpx;
  color: #6b7280;
}

// 右侧插槽
.header-right {
  flex-shrink: 0;
}
</style>

