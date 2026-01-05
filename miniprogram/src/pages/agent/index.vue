<template>
  <view class="agent-page">
    <!-- 头部区域 -->
    <view class="header-section">
      <!-- 背景装饰 -->
      <view class="header-bg"></view>
      
      <!-- 头像 -->
      <view class="avatar-wrapper">
        <view class="avatar">
          <text class="avatar-text">火</text>
        </view>
      </view>
      
      <!-- 标题信息 -->
      <view class="title-section">
        <text class="main-title">火源文案智能体</text>
        <text class="sub-title">HUOYUAN AI</text>
        <text class="desc">你的专属AI爆款引擎</text>
      </view>
    </view>
    
    <!-- 功能列表 -->
    <view class="feature-list">
      <view 
        v-for="(item, index) in featureList" 
        :key="index" 
        class="feature-card"
        @click="handleFeatureClick(item)"
      >
        <view class="feature-icon" :style="{ backgroundColor: item.bgColor }">
          <text class="icon-text">{{ item.icon }}</text>
        </view>
        <view class="feature-content">
          <text class="feature-title">{{ item.title }}</text>
          <text class="feature-desc">{{ item.description }}</text>
        </view>
        <view class="feature-arrow">
          <text class="arrow-icon">›</text>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useAuthStore } from '@/stores/auth'

const authStore = useAuthStore()

// 功能类型定义
interface FeatureItem {
  id: number
  icon: string
  title: string
  description: string
  bgColor: string
  path: string
}

// Mock 数据
const featureList = ref<FeatureItem[]>([
  {
    id: 1,
    icon: '❓',
    title: 'IP问答型文案',
    description: '适合拍摄提问和IP问答场景文案',
    bgColor: '#3B82F6',
    path: '/pages/feature/qa/index'
  },
  {
    id: 2,
    icon: '🎙️',
    title: '高效口播文案',
    description: '基于「流量密码库」随机组合文案',
    bgColor: '#22C55E',
    path: '/pages/feature/broadcast/index'
  },
  {
    id: 3,
    icon: '📝',
    title: '爆款选题创作',
    description: '基于「流量密码库」创作爆款选题',
    bgColor: '#F97316',
    path: '/pages/feature/topic/index'
  },
  {
    id: 4,
    icon: '🎯',
    title: '定向口播文案',
    description: '基于「流量密码库」定向结构文案',
    bgColor: '#3B82F6',
    path: '/pages/feature/target/index'
  },
  {
    id: 5,
    icon: '🔥',
    title: '抖音热点文案',
    description: '结合IP行业和热点事件创作文案',
    bgColor: '#22C55E',
    path: '/pages/feature/trending/index'
  }
])

// 点击功能卡片
const handleFeatureClick = async (item: FeatureItem) => {
  // 登录检查
  const loggedIn = await authStore.requireLogin()
  if (!loggedIn) return
  
  uni.showToast({
    title: `即将开放：${item.title}`,
    icon: 'none',
    duration: 1500
  })
  // 后续可以跳转到对应页面
  // uni.navigateTo({ url: item.path })
}
</script>

<style scoped>
.agent-page {
  min-height: 100vh;
  background: linear-gradient(180deg, #f8fafc 0%, #f1f5f9 100%);
  padding-bottom: 120rpx;
}

/* 头部区域 */
.header-section {
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 60rpx 40rpx 50rpx;
  overflow: hidden;
}

.header-bg {
  position: absolute;
  top: -200rpx;
  left: 50%;
  transform: translateX(-50%);
  width: 800rpx;
  height: 800rpx;
  background: radial-gradient(circle, rgba(59, 130, 246, 0.08) 0%, transparent 70%);
  border-radius: 50%;
  pointer-events: none;
}

/* 头像 */
.avatar-wrapper {
  position: relative;
  z-index: 1;
  margin-bottom: 30rpx;
}

.avatar {
  width: 180rpx;
  height: 180rpx;
  background: linear-gradient(135deg, #3B82F6 0%, #60A5FA 100%);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 16rpx 48rpx rgba(59, 130, 246, 0.35);
}

.avatar-text {
  font-size: 80rpx;
  font-weight: 700;
  color: #ffffff;
  text-shadow: 0 2rpx 8rpx rgba(0, 0, 0, 0.1);
}

/* 标题信息 */
.title-section {
  display: flex;
  flex-direction: column;
  align-items: center;
  position: relative;
  z-index: 1;
}

.main-title {
  font-size: 44rpx;
  font-weight: 700;
  color: #1e293b;
  margin-bottom: 12rpx;
  letter-spacing: 2rpx;
}

.sub-title {
  font-size: 26rpx;
  font-weight: 600;
  color: #94a3b8;
  letter-spacing: 4rpx;
  margin-bottom: 16rpx;
}

.desc {
  font-size: 28rpx;
  color: #64748b;
}

/* 功能列表 */
.feature-list {
  padding: 20rpx 32rpx;
}

.feature-card {
  display: flex;
  align-items: center;
  background: #ffffff;
  border-radius: 24rpx;
  padding: 36rpx 32rpx;
  margin-bottom: 24rpx;
  box-shadow: 0 4rpx 24rpx rgba(0, 0, 0, 0.04);
  transition: all 0.2s ease;
}

.feature-card:active {
  transform: scale(0.98);
  box-shadow: 0 2rpx 12rpx rgba(0, 0, 0, 0.06);
}

.feature-icon {
  width: 96rpx;
  height: 96rpx;
  border-radius: 20rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.icon-text {
  font-size: 44rpx;
}

.feature-content {
  flex: 1;
  margin-left: 28rpx;
  display: flex;
  flex-direction: column;
}

.feature-title {
  font-size: 32rpx;
  font-weight: 600;
  color: #1e293b;
  margin-bottom: 8rpx;
}

.feature-desc {
  font-size: 26rpx;
  color: #94a3b8;
  line-height: 1.4;
}

.feature-arrow {
  flex-shrink: 0;
  margin-left: 16rpx;
}

.arrow-icon {
  font-size: 40rpx;
  color: #cbd5e1;
  font-weight: 300;
}
</style>

