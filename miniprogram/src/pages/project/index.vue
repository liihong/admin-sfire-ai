<template>
  <view class="project-index-page">
    <!-- 项目列表视图 - 没有激活项目时显示 -->
    <ProjectList 
      v-if="!hasActiveProject && !isLoading" 
      :isInTabBar="true"
      @project-selected="handleProjectSelected"
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
  </view>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useProjectStore } from '@/stores/project'
import { fetchProjects } from '@/api/project'
import ProjectList from '@/components/ProjectList.vue'
import ProjectDashboard from '@/components/ProjectDashboard.vue'

const projectStore = useProjectStore()
const isLoading = ref(true)

const hasActiveProject = computed(() => projectStore.hasActiveProject)

// 加载项目列表
async function loadProjects() {
  isLoading.value = true
  try {
    const response = await fetchProjects()
    projectStore.setProjectList(response.projects, response.active_project_id)
  } catch (error) {
    console.error('Failed to fetch projects:', error)
    uni.showToast({ title: '加载失败', icon: 'none' })
  } finally {
    isLoading.value = false
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

onMounted(async () => {
  await loadProjects()
})

// 监听激活项目变化，自动切换视图
watch(() => projectStore.hasActiveProject, () => {
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
</style>
