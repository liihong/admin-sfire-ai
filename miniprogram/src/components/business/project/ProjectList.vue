<template>
  <view class="project-list-page">
    <!-- 顶部装饰背景 -->
    <view class="bg-decoration">
      <view class="decoration-circle circle-1"></view>
      <view class="decoration-circle circle-2"></view>
      <view class="decoration-circle circle-3"></view>
    </view>

    <!-- 页面头部 -->
    <view class="page-header">
      <view class="header-back" @tap="goBack" v-if="canGoBack && !isInTabBar">
        <text class="back-icon">←</text>
      </view>
      <view class="header-content">
        <text class="header-title">选择你的操盘项目</text>
        <text class="header-subtitle">每个项目拥有独立的IP人设和内容风格</text>
      </view>
    </view>

    <!-- 项目列表区域 -->
    <scroll-view class="project-list-wrapper" scroll-y :refresher-enabled="true" @refresherrefresh="onRefresh"
      :refresher-triggered="isRefreshing">
      <!-- 空状态 -->
      <view class="empty-state" v-if="!isLoading && projectList.length === 0">
        <view class="empty-icon">🚀</view>
        <text class="empty-title">还没有项目</text>
        <text class="empty-desc">创建你的第一个 IP 项目，开启智能创作之旅</text>
        <view class="empty-action" @tap="navigateToCreate">
          <text class="action-text">立即创建</text>
        </view>
      </view>

      <!-- 项目卡片列表 -->
      <view class="project-cards" v-else>
        <view class="project-card" v-for="(project, index) in projectList" :key="project.id" :class="{
          active: activeProject?.id === project.id,
          'enter-animation': true
}" :style="{ animationDelay: `${index * 0.08}s` }" @tap="handleSelectProject(project)">
          <!-- 选中指示器 -->
          <view class="active-indicator" v-if="activeProject?.id === project.id">
            <text class="indicator-icon">✓</text>
          </view>

          <!-- 项目头像 -->
          <view class="project-avatar" :style="{ background: project.avatar_color || '#FF8800' }">
            <text class="avatar-letter">{{ project.avatar_letter || project.name[0] }}</text>
          </view>

          <!-- 项目信息 -->
          <view class="project-info">
            <view class="project-name-row">
              <text class="project-name">{{ project.name }}</text>
              <view class="industry-tag" v-if="project.industry && project.industry !== '通用'">
                <text class="tag-text">{{ project.industry }}</text>
              </view>
            </view>
            <view class="project-meta">
              <text class="meta-item">{{ formatDate(project.updated_at) }} 更新</text>
            </view>
            <view class="persona-preview" v-if="project.persona_settings?.tone">
              <text class="preview-label">语气：</text>
              <text class="preview-value">{{ project.persona_settings.tone }}</text>
            </view>
          </view>

          <!-- 操作按钮 -->
          <view class="project-actions" @tap.stop>
            <view class="action-btn edit-btn" @tap="handleEditProject(project)">
              <text class="btn-icon">✏️</text>
            </view>
            <view class="action-btn delete-btn" @tap="handleDeleteProject(project)">
              <text class="btn-icon">🗑️</text>
            </view>
          </view>
        </view>
      </view>

      <!-- 底部占位 -->
      <view class="list-footer-spacer"></view>
    </scroll-view>

    <!-- 底部创建按钮 -->
    <view class="create-btn-wrapper">
      <view class="create-btn" @tap="navigateToCreate">
        <view class="btn-glow"></view>
        <view class="btn-content">
          <text class="btn-icon">✨</text>
          <text class="btn-text">创建新项目</text>
        </view>
      </view>
    </view>

    <!-- 创建项目弹窗 -->
    <BaseModal :visible="showCreateModal" title="创建新项目" @update:visible="showCreateModal = $event">
      <template #footer>
        <view class="modal-footer">
          <view class="modal-btn cancel-btn" @tap="showCreateModal = false">
            <text class="btn-text">取消</text>
          </view>
          <view class="modal-btn confirm-btn" :class="{ disabled: !newProjectName.trim() }" @tap="handleCreateProject">
            <text class="btn-text">创建</text>
          </view>
        </view>
      </template>
      
      <!-- 项目名称 -->
      <view class="form-item">
        <text class="form-label">项目名称</text>
        <input class="form-input" v-model="newProjectName" placeholder="如：李医生科普IP" :maxlength="30" />
      </view>

      <!-- 赛道选择 -->
      <view class="form-item">
        <text class="form-label">所属赛道</text>
        <view class="industry-grid">
          <view class="industry-option" v-for="industry in industryOptions.slice(0, 9)" :key="industry"
            :class="{ selected: newProjectIndustry === industry }" @tap="newProjectIndustry = industry">
            <text class="option-text">{{ industry }}</text>
          </view>
        </view>
      </view>
    </BaseModal>

    <!-- Loading 状态 -->
    <BaseLoading :visible="isLoading" text="加载中..." />
  </view>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useProjectStore, INDUSTRY_OPTIONS, type Project } from '@/stores/project'
import { fetchProjects, createProject, deleteProject } from '@/api/project'
import { formatDate } from '@/utils/date'
import BaseModal from '@/components/common/BaseModal.vue'
import BaseLoading from '@/components/common/BaseLoading.vue'

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
// 直接使用本地状态存储接口返回的数据，不依赖 store 的缓存
const projectList = ref<Project[]>([])
const activeProject = computed(() => projectStore.activeProject)
const isLoading = ref(false)

// 状态
const isRefreshing = ref(false)
const showCreateModal = ref(false)
const newProjectName = ref('')
const newProjectIndustry = ref('通用')
const canGoBack = ref(false)

// 行业选项
const industryOptions = INDUSTRY_OPTIONS

// 初始化
onMounted(async () => {
  // 检查是否可以返回
  const pages = getCurrentPages()
  canGoBack.value = pages.length > 1

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

// 返回上一页
function goBack() {
  uni.navigateBack({
    fail: () => {
      uni.switchTab({ url: '/pages/index/index' })
    }
  })
}

async function getProjectList() {
  const response = await fetchProjects()
  console.log(response)
  projectList.value = response.projects
  // 更新 store 状态
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

  // 如果在 tabBar 页面中，不跳转，触发事件让父组件切换视图
  if (props.isInTabBar) {
    emit('projectSelected')
  } else {
    // 不在 tabBar 页面中，正常跳转
    setTimeout(() => {
      uni.navigateTo({
        url: '/pages/project/dashboard'
      })
    }, 500)
  }
}

// 编辑项目
function handleEditProject(project: Project) {
  uni.navigateTo({
    url: `/pages/project/dashboard?id=${project.id}&edit=true`
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

          // 从本地列表移除
          const index = projectList.value.findIndex(p => p.id === project.id)
          if (index >= 0) {
            projectList.value.splice(index, 1)
          }

          // 更新 store
          projectStore.removeProject(project.id)

          // 如果删除的是当前激活项目，重新获取列表以更新激活状态
          if (activeProject.value?.id === project.id) {
            const response = await fetchProjects()
            projectList.value = response.projects
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

// 打开创建项目弹窗
function navigateToCreate() {
  showCreateModal.value = true
  // 重置表单
  newProjectName.value = ''
  newProjectIndustry.value = '通用'
}

// 创建项目
async function handleCreateProject() {
  if (!newProjectName.value.trim()) {
    uni.showToast({ title: '请输入项目名称', icon: 'none' })
    return
  }

  try {
    const project = await createProject({
      name: newProjectName.value.trim(),
      industry: newProjectIndustry.value
    })

    // 更新 store 状态
    projectStore.upsertProject(project)
    // 如果是第一个项目，自动激活
    if (projectList.value.length === 0) {
      projectStore.setActiveProjectLocal(project)
    }
    // 重新获取项目列表以同步状态
    const response = await fetchProjects()
    projectList.value = response.projects
    projectStore.setProjectList(response.projects, response.active_project_id)

    showCreateModal.value = false
    newProjectName.value = ''
    newProjectIndustry.value = '通用'

    uni.showToast({ title: '创建成功', icon: 'success' })

    // 跳转到控制台编辑人设
    setTimeout(() => {
      uni.navigateTo({
        url: `/pages/project/dashboard?id=${project.id}&edit=true`
      })
    }, 500)
  } catch (error) {
    console.error('Failed to create project:', error)
    uni.showToast({ title: '创建失败，请重试', icon: 'none' })
  }
}
</script>

<style lang="scss" scoped>
@import '@/styles/_variables.scss';
@import '@/styles/_animations.scss';

.project-list-page {
  min-height: 100vh;
  background: $bg-light;
  position: relative;
  overflow: hidden;
}

// 背景装饰（与 ProjectDashboard 风格一致）
.bg-decoration {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  height: 500rpx;
  pointer-events: none;
  overflow: hidden;

  .decoration-circle {
    position: absolute;
    border-radius: 50%;
  }

  .circle-1 {
    width: 400rpx;
    height: 400rpx;
    background: radial-gradient(circle, rgba(255, 136, 0, 0.08) 0%, transparent 70%);
    top: -150rpx;
    right: -100rpx;
  }

  .circle-2 {
    width: 300rpx;
    height: 300rpx;
    background: radial-gradient(circle, rgba(59, 130, 246, 0.06) 0%, transparent 70%);
    top: 100rpx;
    left: -80rpx;
  }

  .circle-3 {
    width: 200rpx;
    height: 200rpx;
    background: radial-gradient(circle, rgba(255, 136, 0, 0.05) 0%, transparent 70%);
    top: 200rpx;
    right: 100rpx;
  }
}

// 页面头部
.page-header {
  position: relative;
  z-index: 10;
  padding: 60rpx 32rpx 40rpx;
  display: flex;
  align-items: flex-start;
  gap: 20rpx;

  .header-back {
    width: 72rpx;
    height: 72rpx;
    background: rgba(255, 255, 255, 0.9);
    backdrop-filter: blur(10px);
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    box-shadow: 0 4rpx 16rpx rgba(0, 0, 0, 0.06);

    .back-icon {
      font-size: 36rpx;
      color: #333;
    }
  }

  .header-content {
    flex: 1;
    padding-top: 40rpx;
  }

  .header-title {
    font-size: 44rpx;
    font-weight: 700;
    color: #1a1a2e;
    letter-spacing: 1rpx;
    display: block;
    margin-bottom: 12rpx;
  }

  .header-subtitle {
    font-size: 26rpx;
    color: #666;
    display: block;
  }
}

// 项目列表容器
.project-list-wrapper {
  position: relative;
  z-index: 10;
  height: calc(100vh - 300rpx);
  padding: 0 32rpx;
}

// 空状态
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 120rpx 40rpx;

  .empty-icon {
    font-size: 100rpx;
    margin-bottom: 32rpx;
  }

  .empty-title {
    font-size: 36rpx;
    font-weight: 600;
    color: #333;
    margin-bottom: 16rpx;
  }

  .empty-desc {
    font-size: 28rpx;
    color: #999;
    text-align: center;
    line-height: 1.6;
    margin-bottom: 48rpx;
  }

  .empty-action {
    padding: 24rpx 64rpx;
        background: linear-gradient(135deg, $primary-orange 0%, $primary-orange-alt 100%);
    border-radius: 48rpx;
    box-shadow: 0 8rpx 24rpx rgba(255, 136, 0, 0.3);

    .action-text {
      font-size: 30rpx;
      font-weight: 600;
      color: #fff;
    }
  }
}

// 项目卡片列表
.project-cards {
  padding-bottom: 40rpx;
}

// 项目卡片
.project-card {
  background: rgba(255, 255, 255, 0.85);
  backdrop-filter: blur(20px);
  border-radius: 24rpx;
  padding: 28rpx;
  margin-bottom: 24rpx;
  display: flex;
  align-items: center;
  gap: 24rpx;
  position: relative;
  border: 2rpx solid transparent;
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
    top: -8rpx;
    right: -8rpx;
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
    margin-bottom: 8rpx;
  }

  .project-name {
    font-size: 32rpx;
    font-weight: 600;
    color: #1a1a2e;
  }

  .industry-tag {
    padding: 4rpx 16rpx;
    background: linear-gradient(135deg, rgba($primary-orange, 0.1) 0%, rgba($primary-orange, 0.15) 100%);
    border-radius: 20rpx;

    .tag-text {
      font-size: 20rpx;
      color: $primary-orange;
      font-weight: 500;
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

// 列表底部占位
.list-footer-spacer {
  height: 200rpx;
}

// 创建按钮
.create-btn-wrapper {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  padding: 32rpx;
  padding-bottom: calc(32rpx + env(safe-area-inset-bottom));
  background: linear-gradient(180deg, transparent 0%, #F5F7FA 40%);
  z-index: 100;

  .create-btn {
    position: relative;
    height: 100rpx;
        background: linear-gradient(135deg, $primary-orange 0%, $primary-orange-alt 100%);
    border-radius: 50rpx;
    display: flex;
    align-items: center;
    justify-content: center;
    box-shadow: 0 8rpx 32rpx rgba(255, 136, 0, 0.35);
    overflow: hidden;

    &:active {
      transform: scale(0.98);
      box-shadow: 0 4rpx 16rpx rgba(255, 136, 0, 0.25);
    }

    .btn-glow {
      position: absolute;
      top: 0;
      left: -100%;
      width: 100%;
      height: 100%;
      background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.3), transparent);
      animation: btnGlow 3s infinite;
    }

    .btn-content {
      display: flex;
      align-items: center;
      gap: 12rpx;
      z-index: 1;

      .btn-icon {
        font-size: 36rpx;
      }

      .btn-text {
        font-size: 32rpx;
        font-weight: 600;
        color: #fff;
      }
    }
  }
}

// 弹窗样式已移至 BaseModal 组件，这里只保留页面特定样式

// 行业选择网格
.industry-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16rpx;

  .industry-option {
    padding: 20rpx 12rpx;
    background: #F5F7FA;
    border-radius: 12rpx;
    text-align: center;
    border: 2rpx solid transparent;
    transition: all 0.2s ease;

    &.selected {
      background: linear-gradient(135deg, rgba($primary-orange, 0.1) 0%, rgba($primary-orange, 0.15) 100%);
      border-color: $primary-orange;

      .option-text {
        color: $primary-orange;
        font-weight: 500;
      }
    }

    .option-text {
      font-size: 24rpx;
      color: #666;
    }
  }
}

// Loading 样式已移至 BaseLoading 组件
</style>

