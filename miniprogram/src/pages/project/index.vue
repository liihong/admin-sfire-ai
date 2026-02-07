<template>
  <view class="project-index-page">
    <SafeAreaTop />
    <!-- 操作台视图 - 有激活项目时显示 -->
    <ProjectDashboard v-if="hasActiveProject && !isLoading" :isInTabBar="true" @switch-project="openProjectDrawer" />

    <!-- 空状态视图 - 没有项目时显示 -->
    <view v-if="!hasActiveProject && !isLoading && projectList.length === 0" class="empty-state-container">
      <EmptyState @action="navigateToCreate" />
    </view>

    <!-- 有项目但未激活时，直接显示项目列表和创建按钮 -->
    <view v-if="!hasActiveProject && !isLoading && projectList.length > 0" class="project-list-page">
      <!-- 引导文字 -->
      <view class="project-list-header">
        <text class="header-title">选择你的操盘项目</text>
        <text class="header-subtitle">每个项目拥有独立的IP人设和内容风格</text>
      </view>
      <!-- 项目列表 -->
      <ProjectList :key="refreshKey" @project-selected="handleProjectSelected" />
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

import { onShow, onLoad } from '@dcloudio/uni-app'

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
  // 如果是从抽屉中选择的，关闭抽屉
  if (drawerVisible.value) {
    drawerVisible.value = false
  }
  // 强制刷新 List 组件（如果当前显示的是列表页面）
  refreshKey.value++
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
    console.log('[ProjectIndex] 开始加载项目列表...')
    const response = await fetchProjects()
    console.log('[ProjectIndex] 项目列表加载成功:', {
      projectsCount: response.projects?.length || 0,
      activeProjectId: response.active_project_id
    })
    projectStore.setProjectList(response.projects, response.active_project_id)
    // 更新 key 强制重新渲染组件（确保显示最新数据）
    refreshKey.value++
    console.log('[ProjectIndex] Store 状态:', {
      hasActiveProject: projectStore.hasActiveProject,
      projectListLength: projectStore.projectList.length
    })
  } catch (error) {
    console.error('[ProjectIndex] 刷新项目列表失败:', error)
    loadError.value = true
    // 确保即使出错也显示错误状态，而不是一直加载
    isLoading.value = false
  } finally {
    isLoading.value = false
    console.log('[ProjectIndex] 加载完成，isLoading:', isLoading.value)
  }
}

// 初始化加载数据
async function initLoad() {
  try {
    console.log('[ProjectIndex] 开始初始化加载...')
    // 检查 store 中的刷新标记，如果有则触发刷新
    const needRefresh = projectStore.checkAndClearRefresh()

    // 如果 store 中没有项目数据，也需要主动加载
    const hasNoData = projectStore.projectList.length === 0

    console.log('[ProjectIndex] 初始化状态:', {
      needRefresh,
      hasNoData,
      projectListLength: projectStore.projectList.length
    })

    if (needRefresh || hasNoData) {
      // 加载项目列表数据
      await refreshProjectList()
    } else {
      // 如果不需要刷新且有数据，直接设置为非加载状态
      console.log('[ProjectIndex] 使用缓存数据，跳过加载')
      isLoading.value = false
      loadError.value = false
    }
  } catch (error) {
    console.error('[ProjectIndex] 初始化加载失败:', error)
    // 确保即使出错也显示内容
    isLoading.value = false
    loadError.value = true
  }
}

// 页面加载时初始化加载
onLoad(() => {
  // 注意：onLoad 不支持 async，需要手动处理
  initLoad().catch(error => {
    console.error('onLoad 执行失败:', error)
    isLoading.value = false
    loadError.value = true
  })
})

// 页面显示时检查是否需要刷新
onShow(() => {
  // 检查 store 中的刷新标记，如果有则触发刷新
  const needRefresh = projectStore.checkAndClearRefresh()
  
  // 如果 store 中没有项目数据，也需要主动加载
  const hasNoData = projectStore.projectList.length === 0

  if (needRefresh || hasNoData) {
    // 加载项目列表数据
    refreshProjectList().catch(error => {
      console.error('onShow 刷新失败:', error)
    })
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
.project-list-page {
  width: 100%;
  min-height: 100vh;
  background-color: #F5F7FA;
}

.project-list-header {
  padding: 48rpx 32rpx 32rpx;
  display: flex;
  flex-direction: column;
  gap: 16rpx;
}

.header-title {
  font-size: 44rpx;
  font-weight: 600;
  color: #1D2129;
  line-height: 1.4;
}

.header-subtitle {
  font-size: 28rpx;
  color: #86909C;
  line-height: 1.5;
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
