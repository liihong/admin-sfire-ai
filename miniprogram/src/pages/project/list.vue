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
      <view class="header-back" @tap="goBack" v-if="canGoBack">
        <text class="back-icon">←</text>
      </view>
      <view class="header-content">
        <text class="header-title">选择你的操盘项目</text>
        <text class="header-subtitle">每个项目拥有独立的IP人设和内容风格</text>
      </view>
    </view>

    <!-- 项目列表区域 -->
    <scroll-view class="project-list-wrapper" scroll-y :refresher-enabled="true" @refresherrefresh="onRefresh" :refresher-triggered="isRefreshing">
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
        <view 
          class="project-card"
          v-for="(project, index) in projectList"
          :key="project.id"
          :class="{ 
            active: activeProject?.id === project.id,
            'enter-animation': true
          }"
          :style="{ animationDelay: `${index * 0.08}s` }"
          @tap="handleSelectProject(project)"
        >
          <!-- 选中指示器 -->
          <view class="active-indicator" v-if="activeProject?.id === project.id">
            <text class="indicator-icon">✓</text>
          </view>

          <!-- 项目头像 -->
          <view class="project-avatar" :style="{ background: project.avatar_color }">
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
    <view class="modal-overlay" v-if="showCreateModal" @tap="showCreateModal = false">
      <view class="modal-content create-modal" @tap.stop>
        <view class="modal-header">
          <text class="modal-title">创建新项目</text>
          <view class="modal-close" @tap="showCreateModal = false">
            <text class="close-icon">×</text>
          </view>
        </view>

        <view class="modal-body">
          <!-- 项目名称 -->
          <view class="form-item">
            <text class="form-label">项目名称</text>
            <input 
              class="form-input"
              v-model="newProjectName"
              placeholder="如：李医生科普IP"
              :maxlength="30"
            />
          </view>

          <!-- 赛道选择 -->
          <view class="form-item">
            <text class="form-label">所属赛道</text>
            <view class="industry-grid">
              <view 
                class="industry-option"
                v-for="industry in industryOptions.slice(0, 9)"
                :key="industry"
                :class="{ selected: newProjectIndustry === industry }"
                @tap="newProjectIndustry = industry"
              >
                <text class="option-text">{{ industry }}</text>
              </view>
            </view>
          </view>
        </view>

        <view class="modal-footer">
          <view class="modal-btn cancel-btn" @tap="showCreateModal = false">
            <text class="btn-text">取消</text>
          </view>
          <view 
            class="modal-btn confirm-btn"
            :class="{ disabled: !newProjectName.trim() }"
            @tap="handleCreateProject"
          >
            <text class="btn-text">创建</text>
          </view>
        </view>
      </view>
    </view>

    <!-- Loading 状态 -->
    <view class="loading-overlay" v-if="isLoading">
      <view class="loading-spinner"></view>
      <text class="loading-text">加载中...</text>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useProjectStore, INDUSTRY_OPTIONS, type Project } from '@/stores/project'

// Store
const projectStore = useProjectStore()
const projectList = computed(() => projectStore.projectList)
const activeProject = computed(() => projectStore.activeProject)
const isLoading = computed(() => projectStore.isLoading)

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
  await projectStore.fetchProjects()
})

// 返回上一页
function goBack() {
  uni.navigateBack({
    fail: () => {
      uni.switchTab({ url: '/pages/index/index' })
    }
  })
}

// 下拉刷新
async function onRefresh() {
  isRefreshing.value = true
  await projectStore.fetchProjects()
  isRefreshing.value = false
}

// 选择项目
async function handleSelectProject(project: Project) {
  await projectStore.setActiveProject(project)
  
  uni.showToast({
    title: `已切换到：${project.name}`,
    icon: 'success'
  })
  
  // 延迟跳转到控制台
  setTimeout(() => {
    uni.navigateTo({
      url: '/pages/project/dashboard'
    })
  }, 500)
}

// 编辑项目
function handleEditProject(project: Project) {
  uni.navigateTo({
    url: `/pages/project/dashboard?id=${project.id}&edit=true`
  })
}

// 跳转到创建页面
function navigateToCreate() {
  uni.navigateTo({
    url: '/pages/project/create'
  })
}

// 创建项目
async function handleCreateProject() {
  if (!newProjectName.value.trim()) {
    uni.showToast({ title: '请输入项目名称', icon: 'none' })
    return
  }
  
  const project = await projectStore.createProject({
    name: newProjectName.value.trim(),
    industry: newProjectIndustry.value
  })
  
  if (project) {
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
  } else {
    uni.showToast({ title: '创建失败，请重试', icon: 'none' })
  }
}

// 格式化日期
function formatDate(dateStr: string): string {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  const now = new Date()
  const diff = now.getTime() - date.getTime()
  
  const minutes = Math.floor(diff / 60000)
  const hours = Math.floor(diff / 3600000)
  const days = Math.floor(diff / 86400000)
  
  if (minutes < 1) return '刚刚'
  if (minutes < 60) return `${minutes}分钟前`
  if (hours < 24) return `${hours}小时前`
  if (days < 7) return `${days}天前`
  
  return `${date.getMonth() + 1}/${date.getDate()}`
}
</script>

<style lang="scss" scoped>
.project-list-page {
  min-height: 100vh;
  background: #F5F7FA;
  position: relative;
  overflow: hidden;
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
  
  .circle-3 {
    width: 150rpx;
    height: 150rpx;
    background: linear-gradient(135deg, rgba(59, 130, 246, 0.08) 0%, transparent 100%);
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
    padding-top: 8rpx;
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
    background: linear-gradient(135deg, #3B82F6 0%, #60A5FA 100%);
    border-radius: 48rpx;
    box-shadow: 0 8rpx 24rpx rgba(59, 130, 246, 0.3);
    
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
    border-color: #3B82F6;
    background: rgba(255, 255, 255, 0.95);
    box-shadow: 0 8rpx 32rpx rgba(59, 130, 246, 0.15);
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
    background: linear-gradient(135deg, #3B82F6 0%, #60A5FA 100%);
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    box-shadow: 0 4rpx 12rpx rgba(59, 130, 246, 0.3);
    
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
    background: linear-gradient(135deg, #EEF2FF 0%, #E0E7FF 100%);
    border-radius: 20rpx;
    
    .tag-text {
      font-size: 20rpx;
      color: #6366F1;
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
      color: #3B82F6;
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
    background: linear-gradient(135deg, #3B82F6 0%, #60A5FA 100%);
    border-radius: 50rpx;
    display: flex;
    align-items: center;
    justify-content: center;
    box-shadow: 0 8rpx 32rpx rgba(59, 130, 246, 0.35);
    overflow: hidden;
    
    &:active {
      transform: scale(0.98);
      box-shadow: 0 4rpx 16rpx rgba(59, 130, 246, 0.25);
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

// 弹窗
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  backdrop-filter: blur(4px);
  z-index: 1000;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 32rpx;
  animation: fadeIn 0.2s ease;
}

.modal-content {
  width: 100%;
  max-width: 640rpx;
  background: #fff;
  border-radius: 32rpx;
  overflow: hidden;
  animation: slideUp 0.3s ease;
  
  .modal-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 32rpx;
    border-bottom: 1rpx solid #f0f0f0;
    
    .modal-title {
      font-size: 34rpx;
      font-weight: 600;
      color: #1a1a2e;
    }
    
    .modal-close {
      width: 56rpx;
      height: 56rpx;
      background: #f5f5f5;
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
      
      .close-icon {
        font-size: 40rpx;
        color: #999;
        line-height: 1;
      }
    }
  }
  
  .modal-body {
    padding: 32rpx;
    
    .form-item {
      margin-bottom: 32rpx;
      
      &:last-child {
        margin-bottom: 0;
      }
      
      .form-label {
        font-size: 28rpx;
        font-weight: 500;
        color: #333;
        margin-bottom: 16rpx;
        display: block;
      }
      
      .form-input {
        width: 100%;
        height: 88rpx;
        background: #F5F7FA;
        border-radius: 16rpx;
        padding: 0 24rpx;
        font-size: 30rpx;
        color: #333;
        border: 2rpx solid transparent;
        
        &:focus {
          border-color: #3B82F6;
          background: #fff;
        }
      }
    }
  }
  
  .modal-footer {
    display: flex;
    gap: 24rpx;
    padding: 24rpx 32rpx 32rpx;
    
    .modal-btn {
      flex: 1;
      height: 88rpx;
      border-radius: 44rpx;
      display: flex;
      align-items: center;
      justify-content: center;
      
      &.cancel-btn {
        background: #F5F7FA;
        
        .btn-text {
          color: #666;
        }
      }
      
      &.confirm-btn {
        background: linear-gradient(135deg, #3B82F6 0%, #60A5FA 100%);
        
        .btn-text {
          color: #fff;
          font-weight: 600;
        }
        
        &.disabled {
          background: #e0e5ec;
          
          .btn-text {
            color: #999;
          }
        }
      }
      
      .btn-text {
        font-size: 30rpx;
      }
    }
  }
}

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
      background: linear-gradient(135deg, #EEF2FF 0%, #E0E7FF 100%);
      border-color: #3B82F6;
      
      .option-text {
        color: #3B82F6;
        font-weight: 500;
      }
    }
    
    .option-text {
      font-size: 24rpx;
      color: #666;
    }
  }
}

// Loading
.loading-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(255, 255, 255, 0.9);
  backdrop-filter: blur(4px);
  z-index: 2000;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 24rpx;
  
  .loading-spinner {
    width: 60rpx;
    height: 60rpx;
    border: 4rpx solid #e0e5ec;
    border-top-color: #3B82F6;
    border-radius: 50%;
    animation: spin 0.8s linear infinite;
  }
  
  .loading-text {
    font-size: 28rpx;
    color: #666;
  }
}

// 动画
@keyframes slideInUp {
  from {
    opacity: 0;
    transform: translateY(30rpx);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

@keyframes slideUp {
  from {
    opacity: 0;
    transform: translateY(40rpx);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes btnGlow {
  0% { left: -100%; }
  50%, 100% { left: 100%; }
}

@keyframes spin {
  to { transform: rotate(360deg); }
}
</style>


