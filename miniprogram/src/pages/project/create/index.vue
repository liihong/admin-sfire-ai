<template>
  <view class="create-project-page">
    <!-- 顶部导航栏 -->
    <BaseHeader :title="pageTitle" @back="handleClose" />
    <!-- AI智能填写对话框（全屏显示） -->
    <IPCollectDialog
      :visible="true"
      :edit-mode="isEditMode"
      :edit-project-id="editProjectId"
      @close="handleClose"
      @complete="handleEditComplete"
    />
  </view>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { onLoad } from '@dcloudio/uni-app'
import { useProjectStore } from '@/stores/project'
import { useAuthStore } from '@/stores/auth'
import IPCollectDialog from '../components/IPCollectDialog.vue'
import BaseHeader from '@/components/base/BaseHeader.vue'
import { updateProject } from '@/api/project'
import { formDataToUpdateRequest, ipCollectFormDataToProjectFormData } from '@/utils/project'
import type { IPCollectFormData } from '@/api/project'

// Store
const projectStore = useProjectStore()
const authStore = useAuthStore()

// 提交状态
const isSubmitting = ref(false)
const isEditMode = ref(false)
const editProjectId = ref<string | null>(null)

const pageTitle = computed(() =>
  isEditMode.value ? '微调人设' : 'IP信息定位调研'
)

/**
 * 页面加载时检查登录状态
 * 如果是游客模式，友好提醒用户登录（不阻断页面）
 */
onLoad((options) => {
  if (options?.mode === 'edit' && options?.id) {
    isEditMode.value = true
    editProjectId.value = String(options.id)
  }

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
 * 微调人设：最后一步保存，更新当前项目（不再走独立人设配置页）
 */
async function handleEditComplete(collectedInfo: IPCollectFormData) {
  if (isSubmitting.value || !editProjectId.value) return

  isSubmitting.value = true

  try {
    const formData = ipCollectFormDataToProjectFormData(collectedInfo)
    const requestData = formDataToUpdateRequest(formData)
    const project = await updateProject(editProjectId.value, requestData)

    projectStore.upsertProject(project)
    if (project.id === projectStore.activeProject?.id) {
      projectStore.setActiveProjectLocal(project)
    }
    projectStore.setNeedRefresh(true)
    projectStore.clearIPCollectFormData()

    uni.showToast({
      title: '已更新人设',
      icon: 'success'
    })

    setTimeout(() => {
      uni.navigateBack({
        fail: () => {
          uni.switchTab({ url: '/pages/project/index' })
        }
      })
    }, 400)
  } catch (error: unknown) {
    const errorMessage = error instanceof Error ? error.message : '保存失败，请重试'
    uni.showToast({
      title: errorMessage,
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
</style>

