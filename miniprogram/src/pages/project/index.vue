<template>
  <view class="project-index-page">
    <!-- 项目列表视图 - 没有激活项目时显示 -->
   <ProjectList v-if="!hasActiveProject && !isLoading" />
    <!-- 操作台视图 - 有激活项目时显示 -->
   <ProjectDashboard v-if="hasActiveProject && !isLoading" :isInTabBar="true" />
    <!-- 加载状态 -->
    <view v-if="isLoading" class="loading-container">
      <view class="loading-spinner"></view>
      <text class="loading-text">加载中...</text>
    </view>

    <!-- 错误状态 - 如果加载失败且不在加载中，显示错误提示 -->
    <view v-if="!isLoading && loadError" class="error-container">
      <text class="error-text">加载失败，请重试</text>
     <view class="retry-btn" @tap="refreshPage(true)">
        <text class="retry-text">重试</text>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useProjectStore } from '@/stores/project'

import ProjectList from './components/List.vue'
import ProjectDashboard from './components/Dashboard.vue'
import { onShow } from '@dcloudio/uni-app'

const projectStore = useProjectStore()
const isLoading = ref(true)
const loadError = ref(false) // 标记是否加载失败

const hasActiveProject = computed(() => projectStore.hasActiveProject)

/**
 * 重新加载页面
 */
function refreshPage(_?: boolean) {
  const pages = getCurrentPages()
  const currentPage = pages[pages.length - 1]
  const url = '/' + currentPage.route
  uni.reLaunch({
    url: url
  })
}


// 页面显示时获取用户信息
onShow(() => {
  isLoading.value = false
  loadError.value = false
})

</script>

<style lang="scss" scoped>
.project-index-page {
  width: 100%;
  min-height: 100vh;
  background-color: #F5F7FA;
}

.loading-container {
  width: 100%;
  height: 100vh;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 16rpx;
}

.loading-spinner {
  width: 60rpx;
  height: 60rpx;
  border: 4rpx solid #E5E7EB;
  border-top-color: #3B82F6;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.loading-text {
  font-size: 28rpx;
  color: #6B7280;
}

.error-container {
  width: 100%;
  height: 100vh;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 32rpx;
  padding: 40rpx;
}

.error-text {
  font-size: 28rpx;
  color: #EF4444;
}

.retry-btn {
  padding: 20rpx 40rpx;
  background-color: #3B82F6;
  border-radius: 8rpx;
}

.retry-text {
  font-size: 28rpx;
  color: #FFFFFF;
}
</style>
