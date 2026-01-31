<template>
  <BaseDrawer :visible="visible" title="IP 人设配置" @update:visible="$emit('update:visible', $event)">
    <template #footer>
      <view class="save-btn" :class="{ loading: isSaving }" @tap="handleSave">
        <text class="btn-text" v-if="!isSaving">保存设置</text>
        <view class="loading-spinner" v-else></view>
      </view>
    </template>
    
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
        :range="industryOptions"
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
    
    <view class="drawer-spacer"></view>
  </BaseDrawer>
</template>

<script setup lang="ts">
/**
 * IP人设配置编辑抽屉组件
 * 
 * 编辑流程说明：
 * 1. 组件接收 project 属性（Project 类型）
 * 2. 使用 usePersonaForm(mode: 'edit', project) 管理表单数据
 * 3. composable 自动从 project.persona_settings 同步数据到 formData（扁平结构）
 * 4. 用户修改表单字段，formData 自动更新（reactive）
 * 5. 用户点击保存，调用 handleSave()
 * 6. handleSave() 调用 saveForm() → updateProjectFromForm()
 * 7. updateProjectFromForm() 内部调用 formDataToUpdateRequest() 转换为 API 请求
 * 8. 调用 updateProject() 更新项目
 * 9. 更新成功后，更新 store 状态
 * 
 * 数据流转：
 * ProjectModel → modelToFormData() → formData (ProjectFormData) → 
 * formDataToUpdateRequest() → updateProject() → ProjectModel → store
 */

import BaseDrawer from '@/components/common/BaseDrawer.vue'
import FormInput from '@/components/form/FormInput.vue'
import FormTextarea from '@/components/form/FormTextarea.vue'
import FormPicker from '@/components/form/FormPicker.vue'
import TagInput from '@/components/form/TagInput.vue'
import ToneSelector from '@/components/form/ToneSelector.vue'
import { usePersonaForm } from '@/composables/usePersonaForm'
import { computed } from 'vue'
import type { Project } from '@/types/project'

interface Props {
  visible: boolean
  project: Project | null
}

const props = defineProps<Props>()

const emit = defineEmits<{
  'update:visible': [value: boolean]
  saved: []
}>()

const projectRef = computed(() => props.project)

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
  autoSync: true // 自动同步项目数据到表单
})

async function handleSave() {
  try {
    const result = await saveForm()
    if (result) {
      uni.showToast({ title: '保存成功', icon: 'success' })
      emit('update:visible', false)
      emit('saved')
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
</script>

<style lang="scss" scoped>
@import '@/styles/_variables.scss';

.setting-section {
  margin-bottom: $spacing-lg;
  
  .section-title {
    font-size: $font-size-md;
    font-weight: 600;
    color: $text-main;
    margin-bottom: $spacing-md;
    display: block;
  }
}

.drawer-spacer {
  height: $spacing-lg;
}

.save-btn {
  height: 96rpx;
  background: linear-gradient(135deg, $primary-orange 0%, $primary-orange-alt 100%);
  border-radius: 48rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 8rpx 24rpx rgba($primary-orange, 0.3);
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
</style>
