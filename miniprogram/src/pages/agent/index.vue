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
        <text class="main-title">火源AI智能体</text>
        <text class="sub-title">HUOYUAN AI</text>
        <text class="desc">你的专属AI爆款引擎</text>
      </view>
    </view>
    
    <!-- 功能列表 -->
    <view class="feature-list">
      <!-- 加载中状态 -->
      <view v-if="loading" class="loading-wrapper">
        <text class="loading-text">加载中...</text>
      </view>

      <!-- 智能体列表 -->
      <view
        v-for="(item, index) in featureList"
        :key="item.id"
        class="feature-card"
        @click="handleFeatureClick(item)"
      >
        <AgentIcon :iconName="item.icon" />
        <view class="feature-content">
          <text class="feature-title">{{ item.name }}</text>
          <text class="feature-desc">{{ item.description }}</text>
        </view>
        <view class="feature-arrow">
          <text class="arrow-icon">›</text>
        </view>
      </view>

      <!-- 空状态 -->
      <view v-if="!loading && featureList.length === 0" class="empty-wrapper">
        <text class="empty-text">暂无智能体</text>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { getAgentList, type Agent } from '@/api/agent'
import AgentIcon from '@/components/AgentIcon.vue'

const authStore = useAuthStore()

// 智能体列表
const featureList = ref<Agent[]>([])
const loading = ref(false)

// 颜色配置（用于智能体卡片背景色）
const colorPalette = [
  '#3B82F6', // 蓝色
  '#22C55E', // 绿色
  '#F97316', // 橙色
  '#8B5CF6', // 紫色
  '#EC4899', // 粉色
  '#06B6D4', // 青色
  '#F59E0B', // 黄色
  '#EF4444'  // 红色
]

// 获取智能体列表
const loadAgentList = async () => {
  loading.value = true
  try {
    const response = await getAgentList()
    if (response.code === 200 && response.data?.agents) {
      featureList.value = response.data.agents
    } else {
      uni.showToast({
        title: response.msg || '获取智能体列表失败',
        icon: 'none',
        duration: 2000
      })
    }
  } catch (error) {
    console.error('加载智能体列表失败:', error)
    uni.showToast({
      title: '加载失败，请稍后重试',
      icon: 'none',
      duration: 2000
    })
  } finally {
    loading.value = false
  }
}

// 获取智能体卡片的背景色
const getAgentBgColor = (index: number): string => {
  return colorPalette[index % colorPalette.length]
}

// 点击智能体卡片
const handleFeatureClick = async (item: Agent) => {
  // 登录检查
  const loggedIn = await authStore.requireLogin()
  if (!loggedIn) return
  
  // 跳转到智能体对话页面，传递智能体ID
  uni.navigateTo({
    url: `/pages/copywriting/index?agentId=${item.id}`
  })
}

// 页面加载时获取智能体列表
onMounted(() => {
  loadAgentList()
})
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
/* 加载状态 */
.loading-wrapper {
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 80rpx 0;
}

.loading-text {
  font-size: 28rpx;
  color: #94a3b8;
}

/* 空状态 */
.empty-wrapper {
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 80rpx 0;
}

.empty-text {
  font-size: 28rpx;
  color: #94a3b8;
}
</style>

