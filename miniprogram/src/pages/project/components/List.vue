<template>
  <view class="project-list-container">
    <!-- 项目列表区域 -->
    <scroll-view class="project-list-wrapper" scroll-y :refresher-enabled="true" @refresherrefresh="onRefresh"
      :refresher-triggered="isRefreshing">
      <!-- 项目卡片列表 -->
      <view class="project-cards" v-if="projectList.length > 0">
        <view class="project-card" v-for="(project, index) in projectList" :key="project.id" :class="{
          active: activeProject?.id === project.id,
          'enter-animation': true
}" :style="{ animationDelay: `${index * 0.08}s` }" @tap="handleSelectProject(project)">
          <!-- 选中指示器 -->
          <view class="active-indicator" v-if="activeProject?.id === project.id">
            <text class="indicator-icon">✓</text>
          </view>

          <!-- 项目头像 -->
          <view class="project-avatar">
            <text class="avatar-letter">{{ project.avatar_letter || project.name[0] }}</text>
          </view>

          <!-- 项目信息 -->
          <view class="project-info">
            <view class="project-name-row">
              <text class="project-name">{{ project.name }}</text>
            </view>
            <view class="project-meta">
              <view class="industry-tag-wrapper" v-if="project.industry && project.industry !== '通用'">
                <text class="tag-label">行业标签：</text>
                <view class="industry-tag">
                  <text class="tag-text">{{ project.industry }}</text>
                </view>
              </view>
            </view>
            <view class="persona-preview" v-if="project.persona_settings?.tone">
              <text class="preview-label">语气：</text>
              <text class="preview-value">{{ project.persona_settings.tone }}</text>
            </view>
          </view>

          <!-- 操作按钮 -->
          <view class="project-actions" @tap.stop>
            <view class="action-btn edit-btn" @tap="handleEditProject(project)">
              <SvgIcon name="edit" size="30" color="#FFFFFF" />
            </view>
            <view class="action-btn delete-btn" @tap="handleDeleteProject(project)">
              <SvgIcon name="delete" size="30" color="#FFFFFF" />
            </view>
          </view>
        </view>
      </view>

      <!-- 底部占位 -->
      <view class="list-footer-spacer"></view>
    </scroll-view>

    <!-- Loading 状态 -->
    <BaseLoading :visible="isLoading" text="加载中..." />

    <!-- 创建项目按钮（固定在底部，不随页面滚动） -->
    <view class="create-project-btn-wrapper" v-if="canCreateProject && projectList.length !== 0">
      <view class="create-project-btn" @tap="navigateToCreate">
        <SvgIcon name="add" size="36" color="#FFFFFF" />
        <text class="create-btn-text">创建新IP</text>
      </view>
      <text class="create-btn-hint" v-if="maxIpCount !== null">
        当前 {{ projectList.length }}/{{ maxIpCount }} 个IP
      </text>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import { useProjectStore, type Project } from '@/stores/project'
import { useAuthStore } from '@/stores/auth'
import { fetchProjects, deleteProject } from '@/api/project'
import BaseLoading from '@/components/common/BaseLoading.vue'
import SvgIcon from '@/components/base/SvgIcon.vue'

// Props
const props = defineProps<{
  isInTabBar?: boolean // 是否在 tabBar 页面中
}>()

// Emits
const emit = defineEmits<{
  projectSelected: [] // 项目选择后触发
}>()

// Store
const projectStore = useProjectStore()
const authStore = useAuthStore()
// 使用 store 的数据，确保数据同步
const projectList = computed(() => projectStore.projectList)
const activeProject = computed(() => projectStore.activeProject)
const isLoading = ref(false)

// 用户权限相关
const maxIpCount = computed(() => {
  const levelInfo = authStore.userInfo?.levelInfo
  return levelInfo?.max_ip_count ?? null
})

const canCreateProject = computed(() => {
  // 如果没有限制，可以创建
  if (maxIpCount.value === null) {
    return true
  }
  // 如果当前项目数量小于最大数量，可以创建
  return projectList.value.length < maxIpCount.value
})

// 状态
const isRefreshing = ref(false)

// 初始化
onMounted(async () => {
  // 加载项目列表
  isLoading.value = true
  try {
    await getProjectList()
  } catch (error) {
    console.error('Failed to fetch projects:', error)
    uni.showToast({ title: '加载失败', icon: 'none' })
  } finally {
    isLoading.value = false
  }
})

// 页面显示时检查是否需要刷新（备用方案，如果父组件没有处理）
onShow(async () => {
  // 检查 store 中的刷新标记（但不清除，因为父组件可能已经处理了）
  // 这里只作为备用，如果父组件没有处理，这里会处理
  if (projectStore.needRefresh) {
    projectStore.setNeedRefresh(false)
    // 刷新项目列表
    isLoading.value = true
    try {
      await getProjectList()
    } catch (error) {
      console.error('Failed to refresh projects:', error)
      uni.showToast({ title: '刷新失败', icon: 'none' })
    } finally {
      isLoading.value = false
    }
  }
})

async function getProjectList() {
  const response = await fetchProjects()
  // 更新 store 状态（projectList 现在是 computed，会自动从 store 读取）
  projectStore.setProjectList(response.projects, response.active_project_id)
}
// 下拉刷新
async function onRefresh() {
  isRefreshing.value = true
  try {
    await getProjectList()
  } catch (error) {
    console.error('Failed to refresh projects:', error)
    uni.showToast({ title: '刷新失败', icon: 'none' })
  } finally {
    isRefreshing.value = false
  }
}


// 选择项目
function handleSelectProject(project: Project) {
  // 更新 store 状态（会自动保存到 localStorage）
  projectStore.setActiveProjectLocal(project)

  uni.showToast({
    title: `已切换到：${project.name}`,
    icon: 'success'
  })

  // 触发事件让父组件处理（关闭抽屉）
  emit('projectSelected')
}

// 编辑项目
function handleEditProject(project: Project) {
  uni.navigateTo({
    url: `/pages/project/index?id=${project.id}&edit=true`
  })
}

// 跳转到创建项目页面
function navigateToCreate() {
  uni.navigateTo({
    url: '/pages/project/create'
  })
}

// 删除项目
async function handleDeleteProject(project: Project) {
  // 确认对话框
  uni.showModal({
    title: '确认删除',
    content: `确定要删除项目"${project.name}"吗？此操作不可恢复。`,
    confirmText: '删除',
    confirmColor: '#FF3B30',
    cancelText: '取消',
    success: async (res) => {
      if (res.confirm) {
        try {
          // 调用删除接口
          await deleteProject(project.id)

          // 更新 store（会自动从列表移除）
          projectStore.removeProject(project.id)

          // 如果删除的是当前激活项目，重新获取列表以更新激活状态
          if (activeProject.value?.id === project.id) {
            const response = await fetchProjects()
            // 更新 store（projectList 现在是 computed，会自动从 store 读取）
            projectStore.setProjectList(response.projects, response.active_project_id)
          }

          uni.showToast({
            title: '删除成功',
            icon: 'success'
          })
        } catch (error) {
          console.error('Failed to delete project:', error)
          uni.showToast({
            title: '删除失败，请重试',
            icon: 'none'
          })
        }
      }
    }
  })
}


</script>

<style lang="scss" scoped>
@import '@/styles/_variables.scss';
@import '@/styles/_animations.scss';

.project-list-container {
  width: 100%;
  min-height: 100%;
}

// 项目列表容器
.project-list-wrapper {
  position: relative;
  z-index: 10;
  padding: 0 32rpx;
  padding-bottom: 40rpx;
}

// 空状态样式已移至 EmptyState 组件

// 项目卡片列表
.project-cards {
  padding-bottom: 30rpx;
}

// 项目卡片
.project-card {
  background: rgba(255, 255, 255, 0.85);
  backdrop-filter: blur(20px);
  border-radius: 24rpx;
  padding: 20rpx;
    margin-bottom: 20rpx;
  display: flex;
  align-items: center;
  gap: 24rpx;
  position: relative;
  border: 2rpx solid rgba(0, 0, 0, 0.1);
  box-shadow: 0 4rpx 20rpx rgba(0, 0, 0, 0.04);
  transition: all 0.3s ease;

  &.enter-animation {
    animation: slideInUp 0.5s ease-out forwards;
    opacity: 0;
  }

  &.active {
    border-color: $primary-orange;
    background: rgba(255, 255, 255, 0.95);
    box-shadow: 0 8rpx 32rpx rgba($primary-orange, 0.15);
  }

  &:active {
    transform: scale(0.98);
  }

  .active-indicator {
    position: absolute;
    top: 5rpx;
      right: 5rpx;
    width: 40rpx;
    height: 40rpx;
    background: linear-gradient(135deg, $primary-orange 0%, $primary-orange-alt 100%);
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    box-shadow: 0 4rpx 12rpx rgba(255, 136, 0, 0.3);

    .indicator-icon {
      font-size: 22rpx;
      color: #fff;
      font-weight: 700;
    }
  }
}

// 项目头像
.project-avatar {
  width: 96rpx;
  height: 96rpx;
  border-radius: 24rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  background-color: #B85C00; // 暗橙色

  &:hover {
    background-color: $primary-orange;
  }

  .avatar-letter {
    font-size: 40rpx;
    font-weight: 700;
    color: #fff;
    text-transform: uppercase;
  }
}

// 项目信息
.project-info {
  flex: 1;
  min-width: 0;

  .project-name-row {
    display: flex;
    align-items: center;
    gap: 12rpx;
  }

  .project-name {
    font-size: 32rpx;
    font-weight: 600;
    color: #1a1a2e;
  }

                                                                .industry-tag-wrapper {
                                                                  display: flex;
                                                                  align-items: center;
                                                                  gap: 8rpx;
    .tag-label {
        font-size: 22rpx;
        color: #999;
      }

                                                                                                                                .industry-tag {
      display: inline-flex;
      align-items: center;

      .tag-text {
        font-size: 22rpx;
        color: $primary-orange;
          font-weight: 500;
        }
        }
                                                                                                                                }

  .project-meta {
    margin-bottom: 8rpx;

    .meta-item {
      font-size: 24rpx;
      color: #999;
    }
  }

  .persona-preview {
    display: flex;
    align-items: center;
    gap: 4rpx;

    .preview-label {
      font-size: 22rpx;
      color: #999;
    }

    .preview-value {
      font-size: 22rpx;
      color: $primary-orange;
    }
  }
}

// 项目操作按钮
.project-actions {
  display: flex;
  gap: 16rpx;

  .action-btn {
    width: 64rpx;
    height: 64rpx;
    border-radius: 16rpx;
    display: flex;
    align-items: center;
    justify-content: center;

    &.edit-btn {
      background: #F5F7FA;
    }

    &.delete-btn {
      background: #FFF5F5;
    }

    .btn-icon {
      font-size: 28rpx;
    }
  }
}

// 列表底部占位（为底部固定按钮预留空间）
.list-footer-spacer {
  height: 200rpx; // 预留足够空间给底部创建按钮
  }
  
  // 创建项目按钮（固定在底部）
  .create-project-btn-wrapper {
    position: fixed;
    bottom: 0;
    left: 0;
    right: 0;
    z-index: 100;
    padding: 10rpx 32rpx;
    // padding-bottom: calc(24rpx + env(safe-area-inset-bottom));
    background: linear-gradient(to top, rgba(238, 238, 238, 0.98) 0%, rgba(255, 255, 255, 0.98) 100%);
    backdrop-filter: blur(20px);
    border-top: 1rpx solid rgba(0, 0, 0, 0.05);
    box-shadow: 0 -4rpx 20rpx rgba(0, 0, 0, 0.05);
  
    .create-project-btn {
      width: 100%;
      height: 88rpx;
      background: linear-gradient(135deg, #1a1a2e 0%, #1a1a2e 100%);
      border-radius: 44rpx;
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 12rpx;
      box-shadow: 0 8rpx 24rpx rgba(#1a1a2e, 0.3);
      transition: all 0.3s ease;
  
      &:active {
        transform: scale(0.98);
        box-shadow: 0 4rpx 16rpx rgba($primary-orange, 0.3);
      }

                                                                                                                                                                                                .create-btn-text {
                                                                                                                                                                                                  font-size: 32rpx;
                                                                                                                                                                                                  font-weight: 600;
                                                                                                                                                                                                  color: #FFFFFF;
                                                                                                                                                                                                }
                                                                                                                                                                                                }

                                                                                                                                .create-btn-hint {
                                                                                                                                  display: block;
                                                                                                                                  text-align: center;
                                                                                                                                  margin-top: 12rpx;
                                                                                                                                  font-size: 24rpx;
                                                                                                                                  color: #999;
                                                                                                                                }
                                                                                                                                }

// Loading 样式已移至 BaseLoading 组件</style>
