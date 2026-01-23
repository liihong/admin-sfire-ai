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
        v-model="editForm.name"
        label="项目名称"
        placeholder="如：李医生科普IP"
      />
      
      <FormPicker
        v-model="editForm.industry"
        label="所属赛道"
        :range="industryOptions"
        placeholder="请选择赛道"
      />
    </view>
    
    <!-- 人设配置 -->
    <view class="setting-section">
      <text class="section-title">人设配置</text>
      
      <ToneSelector
        v-model="editForm.persona.tone"
        label="语气风格"
        :options="toneOptions"
      />
      
      <FormInput
        v-model="editForm.persona.catchphrase"
        label="口头禅"
        placeholder="如：记得三连支持一下~"
      />
      
      <FormInput
        v-model="editForm.persona.target_audience"
        label="目标受众"
        placeholder="如：25-40岁关注健康的职场人群"
      />
      
      <FormTextarea
        v-model="editForm.persona.content_style"
        label="内容风格"
        placeholder="描述你的内容特点和风格..."
        :maxlength="200"
      />
      
      <FormTextarea
        v-model="editForm.persona.introduction"
        label="IP 简介"
        placeholder="简单介绍这个IP的定位和特色..."
        :maxlength="300"
      />
      
      <TagInput
        v-model="editForm.persona.keywords"
        label="常用关键词"
        placeholder="+ 添加关键词"
        variant="default"
      />
      
      <TagInput
        v-model="editForm.persona.taboos"
        label="内容禁忌"
        placeholder="+ 添加禁忌词"
        variant="taboo"
      />
    </view>
    
    <view class="drawer-spacer"></view>
  </BaseDrawer>
</template>

<script setup lang="ts">
import BaseDrawer from '@/components/common/BaseDrawer.vue'
import FormInput from '@/components/form/FormInput.vue'
import FormTextarea from '@/components/form/FormTextarea.vue'
import FormPicker from '@/components/form/FormPicker.vue'
import TagInput from '@/components/form/TagInput.vue'
import ToneSelector from '@/components/form/ToneSelector.vue'
import { usePersonaForm } from '@/composables/usePersonaForm'
import { computed } from 'vue'
import type { Project } from '@/api/project'

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

const {
  editForm,
  isSaving,
  savePersonaSettings,
  toneOptions,
  industryOptions
} = usePersonaForm(projectRef)

async function handleSave() {
  const success = await savePersonaSettings()
  if (success) {
    uni.showToast({ title: '保存成功', icon: 'success' })
    emit('update:visible', false)
    emit('saved')
  } else {
    uni.showToast({ title: '保存失败', icon: 'none' })
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
