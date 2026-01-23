<template>
  <view class="project-index-page">
    <!-- 项目列表视图 - 没有激活项目时显示 -->
    <ProjectList 
      v-if="!hasActiveProject && !isLoading && !loadError"
    />
    
    <!-- 操作台视图 - 有激活项目时显示 -->
    <ProjectDashboard 
      v-if="hasActiveProject && !isLoading" 
      :isInTabBar="true"
      @switch-to-list="handleSwitchToList"
    />
    
    <!-- 加载状态 -->
    <view v-if="isLoading" class="loading-container">
      <view class="loading-spinner"></view>
      <text class="loading-text">加载中...</text>
    </view>
    
    <!-- 错误状态 - 如果加载失败且不在加载中，显示错误提示 -->
    <view v-if="!isLoading && loadError" class="error-container">
      <text class="error-text">加载失败，请重试</text>
      <view class="retry-btn" @tap="loadProjects(true)">
        <text class="retry-text">重试</text>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import { useProjectStore } from '@/stores/project'
import { fetchProjects } from '@/api/project'
// import { ProjectList, ProjectDashboard } from '@/components/business/project'
// 临时测试：绕过 index.js
import ProjectList from '@/components/business/project/ProjectList.vue'
import ProjectDashboard from '@/components/business/project/ProjectDashboard.vue'

const projectStore = useProjectStore()
const isLoading = ref(true)
const isFirstLoad = ref(true) // 标记是否是首次加载
const isLoadinging = ref(false) // 标记是否正在请求中，用于防止重复请求
const loadError = ref(false) // 标记是否加载失败

const hasActiveProject = computed(() => projectStore.hasActiveProject)

// 加载项目列表（带超时保护）
async function loadProjects(forceRefresh = false) {
  // 如果正在请求中且不是强制刷新，则跳过（防止重复请求）
  if (isLoadinging.value && !forceRefresh) {
    console.log('[ProjectIndex] 跳过重复请求')
    return
  }
  
  console.log('[ProjectIndex] 开始加载项目列表', { forceRefresh, isFirstLoad: isFirstLoad.value })
  isLoading.value = true
  isLoadinging.value = true
  loadError.value = false
  
  // 设置超时保护（10秒）
  const timeoutId = setTimeout(() => {
    if (isLoadinging.value) {
      console.warn('[ProjectIndex] 请求超时，强制结束加载')
      isLoading.value = false
      isLoadinging.value = false
      loadError.value = true
      uni.showToast({ title: '请求超时，请重试', icon: 'none' })
      // 设置空列表以便显示组件
      projectStore.setProjectList([], undefined)
    }
  }, 10000)
  
  try {
    const response = await fetchProjects()
    clearTimeout(timeoutId)
    console.log('[ProjectIndex] 项目列表加载成功', response)
    
    // 确保 response 有 projects 属性
    if (response && Array.isArray(response.projects)) {
      projectStore.setProjectList(response.projects, response.active_project_id)
      console.log('[ProjectIndex] Store 更新完成', { 
        hasActiveProject: projectStore.hasActiveProject,
        projectCount: projectStore.projectCount 
      })
    } else {
      console.warn('[ProjectIndex] 响应数据格式异常', response)
      projectStore.setProjectList([], undefined)
    }
  } catch (error) {
    clearTimeout(timeoutId)
    console.error('[ProjectIndex] 加载项目列表失败:', error)
    loadError.value = true
    uni.showToast({ title: '加载失败', icon: 'none' })
    // 即使加载失败，也设置空列表，以便显示组件（显示空状态）
    projectStore.setProjectList([], undefined)
  } finally {
    isLoading.value = false
    isLoadinging.value = false
    isFirstLoad.value = false
    console.log('[ProjectIndex] 加载完成', { 
      isLoading: isLoading.value, 
      hasActiveProject: projectStore.hasActiveProject,
      projectCount: projectStore.projectCount,
      loadError: loadError.value
    })
  }
}

// 处理项目选择
function handleProjectSelected() {
  // 项目选择后，hasActiveProject 会自动变为 true，视图会自动切换
  // 这里可以添加额外的逻辑，比如提示等
}

// 处理切换到列表
async function handleSwitchToList() {
  // 清除激活项目，视图会自动切换回列表
  projectStore.clearActiveProject()
  // 重新加载项目列表
  await loadProjects()
}

// 页面首次加载时执行
onMounted(async () => {
  console.log('[ProjectIndex] onMounted 执行')
  try {
    await loadProjects()
  } catch (error) {
    console.error('[ProjectIndex] onMounted 加载失败:', error)
    // 确保即使出错也能显示组件
    isLoading.value = false
    loadError.value = true
  }
})

// Tabbar 页面切换回来时也会触发，确保数据刷新
onShow(async () => {
  console.log('[ProjectIndex] onShow 执行', { isFirstLoad: isFirstLoad.value })
  // 如果不是首次加载，则刷新数据（避免与 onMounted 重复加载）
  if (!isFirstLoad.value) {
    try {
      await loadProjects(true)
    } catch (error) {
      console.error('[ProjectIndex] onShow 加载失败:', error)
      // 确保即使出错也能显示组件
      isLoading.value = false
      loadError.value = true
    }
  }
})

// 监听激活项目变化，自动切换视图
watch(() => projectStore.hasActiveProject, (newVal) => {
  console.log('[ProjectIndex] 激活项目状态变化', { hasActiveProject: newVal, isLoading: isLoading.value })
  // 视图会自动通过 v-if 切换，不需要额外操作
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
