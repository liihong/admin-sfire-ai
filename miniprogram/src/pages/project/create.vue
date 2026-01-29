<template>
  <view class="create-project-page">
    <SafeAreaTop />
    <!-- 顶部导航栏 -->
    <view class="page-header">
      <view class="header-back" @tap="handleClose">
        <text class="back-icon">←</text>
      </view>
      <view class="header-title">IP信息定位智能体</view>
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
import { useProjectStore } from '@/stores/project'
import IPCollectDialog from './components/IPCollectDialog.vue'
import SafeAreaTop from '@/components/common/SafeAreaTop.vue'
import { createProject, fetchProjects } from '@/api/project'

// Store
const projectStore = useProjectStore()

// 提交状态
const isSubmitting = ref(false)

// 处理关闭对话框
function handleClose() {
  uni.navigateBack({
    fail: () => {
      uni.switchTab({ url: '/pages/project/index' })
    }
  })
}

// 处理AI采集完成，直接创建项目
async function handleAIComplete(collectedInfo: any) {
  if (isSubmitting.value) return
  
  isSubmitting.value = true
  
  try {
    // 新版本表单式收集，数据已经是结构化格式，直接使用
    // 构建创建项目的请求数据，符合后端扁平格式要求
    const requestData: any = {
      name: collectedInfo.name?.trim() || '未命名项目',
      industry: collectedInfo.industry?.trim() || '通用'
    }

    // 添加人设字段（扁平格式，后端会自动合并到 persona_settings）
    // 只添加非空字段，避免发送空字符串
    if (collectedInfo.introduction?.trim()) {
      requestData.introduction = collectedInfo.introduction.trim()
    }
    if (collectedInfo.tone?.trim()) {
      requestData.tone = collectedInfo.tone.trim()
    }
    if (collectedInfo.target_audience?.trim()) {
      requestData.target_audience = collectedInfo.target_audience.trim()
    }
    if (collectedInfo.catchphrase?.trim()) {
      requestData.catchphrase = collectedInfo.catchphrase.trim()
    }
    // keywords 必须是数组格式
    if (collectedInfo.keywords && Array.isArray(collectedInfo.keywords) && collectedInfo.keywords.length > 0) {
      // 过滤空字符串
      const validKeywords = collectedInfo.keywords.filter((k: string) => k && k.trim())
      if (validKeywords.length > 0) {
        requestData.keywords = validKeywords
      }
    }

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

