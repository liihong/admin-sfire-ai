<template>
  <view class="persona-page">
    <BaseHeader title="IP 人设配置" @back="handleBack" />
    
    <scroll-view class="content-scroll" scroll-y>
      <!-- 项目基本信息 -->
      <view class="setting-section">
        <text class="section-title">基本信息</text>
        
        <FormInput
          v-model="formData.name"
          label="项目名称"
          placeholder="如：李医生科普IP"
        />
        
        <FormPicker
          v-model="formData.industry"
          label="所属赛道"
          :range="industryOptionsList"
          placeholder="请选择赛道"
        />
      </view>
      
      <!-- 人设配置 -->
      <view class="setting-section">
        <text class="section-title">人设配置</text>
        
        <ToneSelector
          v-model="formData.tone"
          label="语气风格"
          :options="toneOptions.map(v => v.value)"
        />
        
        <FormInput
          v-model="formData.catchphrase"
          label="口头禅"
          placeholder="如：记得三连支持一下~"
        />
        
        <FormInput
          v-model="formData.target_audience"
          label="目标受众"
          placeholder="如：25-40岁关注健康的职场人群"
        />
        
        <!-- 扩展字段 -->
        <FormTextarea
          v-model="formData.industry_understanding"
          label="行业理解"
          placeholder="请输入你对这个行业的理解..."
          :maxlength="200"
        />
        
        <FormTextarea
          v-model="formData.unique_views"
          label="对行业不同的看法"
          placeholder="请输入你对行业不同的看法..."
          :maxlength="200"
        />
        
        <FormInput
          v-model="formData.target_pains"
          label="目标人群痛点"
          placeholder="例如：工作压力大，需要减压"
        />
        
        <FormTextarea
          v-model="formData.content_style"
          label="内容风格"
          placeholder="描述你的内容特点和风格..."
          :maxlength="200"
        />
        
        <FormTextarea
          v-model="formData.introduction"
          label="IP 简介"
          placeholder="简单介绍这个IP的定位和特色..."
          :maxlength="300"
        />
        
        <TagInput
          v-model="formData.keywords"
          label="常用关键词"
          placeholder="+ 添加关键词"
          variant="default"
        />
        
        <TagInput
          v-model="formData.taboos"
          label="内容禁忌"
          placeholder="+ 添加禁忌词"
          variant="taboo"
        />
      </view>
      
      <view class="bottom-spacer"></view>
    </scroll-view>
    
    <!-- 底部保存按钮 -->
    <view class="footer-bar">
      <view class="save-btn" :class="{ loading: isSaving }" @tap="handleSave">
        <text class="btn-text" v-if="!isSaving">保存设置</text>
        <view class="loading-spinner" v-else></view>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
/**
 * IP人设配置编辑页面（二级页面）
 * 
 * 从 PersonaDrawer 抽离为独立页面，提供更大的操作空间
 * 
 * 使用方式：uni.navigateTo({ url: '/pages/project/persona/index?id=xxx' })
 * - id: 项目ID，不传则使用当前激活项目
 */

import { computed, ref } from 'vue'
import { onLoad } from '@dcloudio/uni-app'
import { useProjectStore } from '@/stores/project'
import { fetchProjects } from '@/api/project'
import FormInput from '@/components/form/FormInput.vue'
import FormTextarea from '@/components/form/FormTextarea.vue'
import FormPicker from '@/components/form/FormPicker.vue'
import TagInput from '@/components/form/TagInput.vue'
import ToneSelector from '@/components/form/ToneSelector.vue'
import BaseHeader from '@/components/base/BaseHeader.vue'
import { usePersonaForm } from '@/composables/usePersonaForm'
import type { Project } from '@/types/project'

const projectStore = useProjectStore()
const projectId = ref<string | null>(null)
const project = ref<Project | null>(null)
const isLoading = ref(true)
const loadError = ref(false)

const projectRef = computed(() => project.value)

// 使用 usePersonaForm 管理表单数据（编辑模式）
const {
  formData,
  isSaving,
  saveForm,
  toneOptions,
  industryOptions
} = usePersonaForm({
  mode: 'edit',
  project: projectRef,
  autoSync: true
})

// 将 DictOption[] 转换为字符串数组供 FormPicker 使用
const industryOptionsList = computed(() =>
  industryOptions.value.map((item) => item.value || item.label)
)

/**
 * 加载项目数据
 */
async function loadProject() {
  if (!projectId.value) {
    // 无 projectId 时使用当前激活项目
    project.value = projectStore.activeProject
    isLoading.value = false
    if (!project.value) {
      loadError.value = true
      uni.showToast({ title: '请先选择项目', icon: 'none' })
      setTimeout(() => uni.navigateBack(), 1500)
    }
    return
  }

  try {
    const idStr = String(projectId.value)
    let p = projectStore.projectList.find((item) => String(item.id) === idStr)
    if (!p) {
      const response = await fetchProjects()
      projectStore.setProjectList(response.projects, response.active_project_id)
      p = projectStore.projectList.find((item) => String(item.id) === idStr)
    }
    project.value = p || null
    if (!project.value) {
      loadError.value = true
      uni.showToast({ title: '项目不存在', icon: 'none' })
      setTimeout(() => uni.navigateBack(), 1500)
    }
  } catch (error) {
    console.error('加载项目失败:', error)
    loadError.value = true
    uni.showToast({ title: '加载失败', icon: 'none' })
    setTimeout(() => uni.navigateBack(), 1500)
  } finally {
    isLoading.value = false
  }
}

function handleBack() {
  uni.navigateBack({
    fail: () => {
      uni.switchTab({ url: '/pages/project/index' })
    }
  })
}

async function handleSave() {
  try {
    const result = await saveForm()
    if (result) {
      uni.showToast({ title: '保存成功', icon: 'success' })
      projectStore.setNeedRefresh(true)
      uni.navigateBack()
    } else {
      uni.showToast({ title: '保存失败', icon: 'none' })
    }
  } catch (error: any) {
    console.error('保存失败:', error)
    uni.showToast({
      title: error.message || '保存失败',
      icon: 'none'
    })
  }
}

onLoad((options) => {
  projectId.value = options?.id || null
  loadProject()
})
</script>

<style lang="scss" scoped>
@import '@/styles/_variables.scss';

.persona-page {
  height: 100vh;
  min-height: 100vh;
  background: linear-gradient(180deg, #FAFBFC 0%, #F5F7FA 100%);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.content-scroll {
  flex: 1;
  min-height: 0;
  height: calc(100vh - 380rpx);
  padding: $spacing-md $spacing-lg;
  box-sizing: border-box;
}

.setting-section {
  margin-bottom: $spacing-xl;
  padding: $spacing-lg;
  background: $white;
  border-radius: $radius-lg;
  box-shadow: $shadow-sm;
  
  .section-title {
    font-size: $font-size-md;
    font-weight: 600;
    color: $text-main;
    margin-bottom: $spacing-md;
    padding-bottom: $spacing-sm;
    border-bottom: 2rpx solid rgba(0, 0, 0, 0.06);
    display: block;
  }
}

/* 底部留白需大于 footer 高度，避免滚动时「内容禁忌」等最后一项被按钮遮挡 */
.bottom-spacer {
  height: 280rpx;
}

.footer-bar {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  z-index: 10;
  padding: $spacing-md $spacing-lg;
  padding-bottom: calc($spacing-md + constant(safe-area-inset-bottom));
  padding-bottom: calc($spacing-md + env(safe-area-inset-bottom));
  background: $white;
  box-shadow: 0 -4rpx 16rpx rgba(0, 0, 0, 0.08);
}

.save-btn {
  height: 96rpx;
  background: linear-gradient(135deg, $primary-orange 0%, $primary-orange-alt 100%);
  border-radius: 48rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 8rpx 24rpx rgba($primary-orange, 0.35);
  transition: all $transition-base;
  
  &.loading {
    background: rgba($primary-orange, 0.6);
  }
  
  &:active:not(.loading) {
    transform: scale(0.98);
  }
  
  .btn-text {
    font-size: $font-size-lg;
    font-weight: 600;
    color: $white;
  }
  
  .loading-spinner {
    width: 36rpx;
    height: 36rpx;
    border: 3rpx solid rgba(255, 255, 255, 0.3);
    border-top-color: $white;
    border-radius: 50%;
    animation: spin 0.8s linear infinite;
  }
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}
</style>
