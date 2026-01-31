<template>
  <view class="create-project-page">
    <SafeAreaTop />
    <!-- 顶部导航栏 -->
    <view class="page-header">
      <view class="header-back" @tap="handleClose">
        <text class="back-icon">←</text>
      </view>
      <view class="header-title">IP信息定位调研</view>
      <view class="header-placeholder"></view>
    </view>
    <!-- AI智能填写对话框（全屏显示） -->
    <IPCollectDialog
:visible="true" @close="handleClose"
      @complete="handleAIComplete"
    />
  </view>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { onLoad } from '@dcloudio/uni-app'
import { useProjectStore } from '@/stores/project'
import { useAuthStore } from '@/stores/auth'
import IPCollectDialog from './components/IPCollectDialog.vue'
import SafeAreaTop from '@/components/common/SafeAreaTop.vue'
import { createProject } from '@/api/project'
import { formDataToCreateRequest } from '@/utils/project'
import type { ProjectFormData } from '@/types/project'
import type { IPCollectFormData } from '@/api/project'

// Store
const projectStore = useProjectStore()
const authStore = useAuthStore()

// 提交状态
const isSubmitting = ref(false)

/**
 * 页面加载时检查登录状态
 * 如果是游客模式，友好提醒用户登录（不阻断页面）
 */
onLoad(() => {
  // 检查用户是否已登录
  if (!authStore.isLoggedIn) {
    uni.showModal({
      title: '提示',
      content: '该功能需登录才能体验完整流程',
      showCancel: true,
      cancelText: '稍后',
      confirmText: '去登录',
      success: (res) => {
        if (res.confirm) {
          // 点击"去登录"，跳转到登录页面
          uni.navigateTo({
            url: '/pages/login/index'
          })
        }
        // 点击"稍后"或取消，留在当前页面，不做任何操作
      }
    })
  }
})

// 处理关闭对话框
function handleClose() {
  uni.navigateBack({
    fail: () => {
      uni.switchTab({ url: '/pages/project/index' })
    }
  })
}

/**
 * 处理AI采集完成，创建项目
 * 
 * 数据流转：
 * IPCollectDialog 返回 IPCollectFormData → 
 * 转换为 ProjectFormData → 
 * formDataToCreateRequest() → 
 * createProject() → 
 * ProjectModel → 
 * store
 */
async function handleAIComplete(collectedInfo: IPCollectFormData) {
  if (isSubmitting.value) return
  
  isSubmitting.value = true
  
  try {
    // 将 IPCollectFormData 转换为 ProjectFormData（补充默认值）
    const formData: ProjectFormData = {
      name: collectedInfo.name?.trim() || '未命名项目',
      industry: collectedInfo.industry?.trim() || '通用',
      tone: collectedInfo.tone || '',
      catchphrase: collectedInfo.catchphrase || '',
      target_audience: collectedInfo.target_audience || '',
      introduction: collectedInfo.introduction || '',
      keywords: collectedInfo.keywords || [],
      industry_understanding: collectedInfo.industry_understanding || '',
      unique_views: collectedInfo.unique_views || '',
      target_pains: collectedInfo.target_pains || '',
      benchmark_accounts: [],
      content_style: '',
      taboos: []
    }
    
    // 使用数据转换工具函数，将表单数据转换为创建请求
    const requestData = formDataToCreateRequest(formData)

    console.log('创建项目请求数据:', requestData)

    // 创建项目
    const project = await createProject(requestData)

    // 更新 store 状态
    projectStore.upsertProject(project)

    // 设置刷新标记，跳转后会自动刷新列表
    projectStore.setNeedRefresh(true)

    uni.showToast({
      title: '创建成功',
      icon: 'success'
    })

    // 跳转到项目列表页（project/index 会根据是否有激活项目显示列表或操作台）
    // 创建完成后不自动激活，让用户在列表中选择要激活的项目
    setTimeout(() => {
      uni.switchTab({
        url: '/pages/project/index'
      })
    }, 500)
  } catch (error: any) {
    console.error('创建项目失败:', error)
    uni.showToast({
      title: error.message || '创建失败，请重试',
      icon: 'none'
    })
  } finally {
    isSubmitting.value = false
  }
}
</script>

<style lang="scss" scoped>
@import '@/styles/_variables.scss';
.create-project-page {
  min-height: 100vh;
  background: #F5F7FA;
  position: relative;
  overflow: hidden;
}

// 页面头部导航栏
.page-header {
    z-index: 100;
      background: #fff;
      padding: 20rpx 32rpx;
    display: flex;
    align-items: center;
      gap: 24rpx;
        box-shadow: 0 2rpx 8rpx rgba(0, 0, 0, 0.04);
  }
    
                                                                                                                                                                                                                                                                .header-back {
                                                                                                                                                                                                                                                                  width: 64rpx;
                                                                                                                                                                                                                                                                  height: 64rpx;
                                                                                                                                                                                                                                                                  display: flex;
                                                                                                                                                                                                                                                                  align-items: center;
                                                                                                                                                                                                                                                                  justify-content: center;
  border-radius: 50%;
  background: rgba(0, 0, 0, 0.05);
  }
                                                                                                                                .back-icon {
                                                                                                                                  font-size: 36rpx;
                                                                                                                                  color: $text-main;
      font-weight: 600;
}

.header-title {
  flex: 1;
  font-size: 36rpx;
  font-weight: 600;
color: $text-main;
  text-align: center;
}


                                                                                                                                .header-placeholder {
                                                                                                                                  width: 64rpx;
                                                                                                                                  height: 64rpx;
}
</style>

