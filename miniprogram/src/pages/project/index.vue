<template>
  <view class="project-index-page">
    <SafeAreaTop />
    <!-- 操作台视图 - 有激活项目时显示 -->
    <ProjectDashboard v-if="hasActiveProject && !isLoading" :isInTabBar="true" @switch-project="openProjectDrawer" />

    <!-- 空状态视图 - 没有项目时显示 -->
    <view v-if="!hasActiveProject && !isLoading && projectList.length === 0" class="empty-state-container">
      <EmptyState @action="navigateToCreate" />
    </view>

    <!-- 项目列表抽屉 -->
    <BaseDrawer :visible="drawerVisible" title="选择你的操盘项目" @update:visible="drawerVisible = $event"
      @close="drawerVisible = false">
      <ProjectList :key="refreshKey" @project-selected="handleProjectSelected" />
    </BaseDrawer>

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
import { ref, computed, watch } from 'vue'
import { useProjectStore } from '@/stores/project'
import { fetchProjects } from '@/api/project'

import ProjectList from './components/List.vue'
import ProjectDashboard from './components/Dashboard.vue'
import SafeAreaTop from '@/components/common/SafeAreaTop.vue'
import BaseDrawer from '@/components/common/BaseDrawer.vue'
import EmptyState from './components/list/EmptyState.vue'

import { onShow } from '@dcloudio/uni-app'

const projectStore = useProjectStore()
const isLoading = ref(true)
const loadError = ref(false) // 标记是否加载失败
const refreshKey = ref(0) // 用于强制刷新 List 组件
const drawerVisible = ref(false) // 控制抽屉显示/隐藏

const hasActiveProject = computed(() => projectStore.hasActiveProject)
const projectList = computed(() => projectStore.projectList)

// 监听 hasActiveProject 变化，当切换列表时确保 isLoading 为 false
watch(hasActiveProject, (newVal, oldVal) => {
  // 当从有激活项目切换到无激活项目时，确保 isLoading 为 false
  if (oldVal === true && newVal === false) {
    isLoading.value = false
    loadError.value = false
    // 强制刷新 List 组件
    refreshKey.value++
  }
})

// 监听项目列表变化，如果没有项目且没有激活项目，显示空状态
watch([hasActiveProject, projectList], ([hasActive, list]) => {
  // 如果没有激活项目且项目列表为空，确保 isLoading 为 false 以显示空状态
  if (!hasActive && list.length === 0) {
    isLoading.value = false
    loadError.value = false
  }
})

/**
 * 打开项目列表抽屉
 */
function openProjectDrawer() {
  drawerVisible.value = true
  // 强制刷新 List 组件
  refreshKey.value++
}

/**
 * 处理项目选择后的回调
 */
function handleProjectSelected() {
  drawerVisible.value = false
}

/**
 * 跳转到创建项目页面
 */
function navigateToCreate() {
  uni.navigateTo({
    url: '/pages/project/create'
  })
}

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

// 刷新项目列表
async function refreshProjectList() {
  try {
    isLoading.value = true
    loadError.value = false
    const response = await fetchProjects()
    projectStore.setProjectList(response.projects, response.active_project_id)
    // 更新 key 强制重新渲染组件（确保显示最新数据）
    refreshKey.value++
  } catch (error) {
    console.error('刷新项目列表失败:', error)
    loadError.value = true
  } finally {
    isLoading.value = false
  }
}

// 页面显示时检查是否需要刷新
onShow(async () => {
  // 检查 store 中的刷新标记，如果有则触发刷新
  const needRefresh = projectStore.checkAndClearRefresh()
  
  // 如果 store 中没有项目数据，也需要主动加载
  const hasNoData = projectStore.projectList.length === 0

  if (needRefresh || hasNoData) {
    // 加载项目列表数据
    await refreshProjectList()
  } else {
    // 如果不需要刷新且有数据，直接设置为非加载状态
    isLoading.value = false
    loadError.value = false
  }
})

</script>

<style lang="scss" scoped>
.project-index-page {
  width: 100%;
  min-height: 100vh;
  background-color: #F5F7FA;
}

.empty-state-container {
  width: 100%;
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
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
