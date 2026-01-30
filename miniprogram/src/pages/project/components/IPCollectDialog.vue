<template>
  <view class="ip-collect-dialog" v-if="visible">
    <view class="dialog-content">
      <!-- 步骤指示器 -->
      <StepIndicator :steps="steps" :current-step="currentStep" />
      
      <!-- Swiper 容器 -->
      <swiper 
        class="step-swiper"
        :current="currentStep"
        @change="handleSwiperChange"
        :disable-touch="false"
        :duration="300"
      >
        <!-- 步骤1: 设定身份 -->
        <swiper-item>
          <StepIdentity
:form-data="formData"
            :industry-options="industryOptions"
            :preview-data="previewData"
            @update:form-data="handleFormDataUpdate"
          />
        </swiper-item>
        
        <!-- 步骤2: 注入灵魂 -->
        <swiper-item>
          <StepSoul
:form-data="formData"
            :preview-data="previewData"
            @update:form-data="handleFormDataUpdate"
          />
        </swiper-item>
        
        <!-- 步骤3: 定义风格 -->
        <swiper-item>
          <StepStyle
:form-data="formData"
            :tone-options="toneOptions"
            :preview-data="previewData"
            @update:form-data="handleFormDataUpdate"
          />
        </swiper-item>
        
        <!-- 步骤4: 激活大脑 -->
        <swiper-item>
          <StepBrain
:form-data="formData"
            :is-generating-keywords="isGeneratingKeywords"
           @update:form-data="handleFormDataUpdate"
          />
        </swiper-item>
      </swiper>
      
      <!-- 底部导航按钮 -->
      <view class="dialog-footer">
        <view 
          v-if="currentStep > 0"
          class="nav-btn prev-btn"
          @tap="handlePrev"
        >
          <text class="btn-text">❮ 上一步</text>
        </view>
        <view 
          v-if="currentStep < 3"
          class="nav-btn next-btn"
          :class="{ disabled: !canNext }"
          @tap="handleNext"
        >
          <text class="btn-text">下一步 ❯</text>
        </view>
        <view 
          v-if="currentStep === 3"
          class="nav-btn complete-btn"
          :class="{ disabled: !canComplete }"
          @tap="handleComplete"
        >
         <text class="btn-text">生成IP定位报告 </text>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
/**
 * IP信息收集对话框组件
 * 
 * 创建流程说明：
 * 1. 用户通过多步骤表单填写IP信息
 * 2. 使用 usePersonaForm(mode: 'create') 管理表单数据
 * 3. 表单数据存储在 formData（ProjectFormData 类型，扁平结构）
 * 4. 用户完成所有步骤后，调用 handleComplete()
 * 5. handleComplete() 将 formData 转换为 IPCollectFormData（只包含收集的字段）
 * 6. 通过 emit('complete', collectedData) 传递给父组件
 * 7. 父组件（create.vue）接收数据后调用 formDataToCreateRequest() 转换为 API 请求
 * 8. 调用 createProject() 创建项目
 * 
 * 数据流转：
 * formData (ProjectFormData) → collectedData (IPCollectFormData) → emit → 
 * 父组件 → formDataToCreateRequest() → createProject() → ProjectModel → store
 */

import { ref, computed, watch } from 'vue'
import { type IPCollectFormData, aiCollectIPInfo } from '@/api/project'
import type { ProjectFormData } from '@/types/project'
import { usePersonaForm } from '@/composables/usePersonaForm'
import StepIndicator from './collect/StepIndicator.vue'
import StepIdentity from './collect/StepIdentity.vue'
import StepSoul from './collect/StepSoul.vue'
import StepStyle from './collect/StepStyle.vue'
import StepBrain from './collect/StepBrain.vue'

interface Props {
  visible: boolean
}

interface Emits {
  (e: 'close'): void
  (e: 'complete', data: IPCollectFormData): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

// 步骤定义
const steps = [
  { label: '人设定位', icon: 'account', iconType: 'u-icon' as const, key: 'identity' },
  { label: '受众定位', icon: 'star', iconType: 'u-icon' as const, key: 'soul' },
  { label: '风格定位', icon: 'fingerprint', iconType: 'u-icon' as const, key: 'fingerprint' },
  { label: '激活大脑', icon: 'grid', iconType: 'u-icon' as const, key: 'grid' }
]

// 使用 usePersonaForm 管理表单数据（创建模式）
const {
  formData,
  industryOptions,
  toneOptions,
  resetForm,
  initFormData
} = usePersonaForm({
  mode: 'create',
  autoSync: false
})

// 状态
const currentStep = ref(0)
const isGeneratingKeywords = ref(false)

// IP画像预览数据（从 formData 中提取）
const previewData = computed(() => {
  return {
    name: formData.name || '未命名',
    industry: formData.industry || '未选择',
    tone: formData.tone || '未选择',
    target_audience: formData.target_audience || '未填写',
    keywords: formData.keywords.length > 0 ? formData.keywords : []
  }
})

// 验证逻辑（使用 formData，不是 formData.value，因为它是 reactive）
const canNext = computed(() => {
  switch (currentStep.value) {
    case 0:
      return formData.name.trim() && formData.industry
    case 1:
      return formData.target_audience.trim().length > 0 &&
        formData.target_pains.trim().length > 0
    case 2:
      return formData.tone &&
        formData.introduction.trim().length >= 50
    default:
      return false
  }
})

const canComplete = computed(() => {
  return formData.keywords.length > 0
})

// 初始化：当对话框显示时重置表单
watch(() => props.visible, (newVal) => {
  if (newVal) {
    initDialog()
  }
})

function initDialog() {
  currentStep.value = 0
  resetForm() // 使用 composable 的 resetForm 方法
}

function handleSwiperChange(e: any) {
  const newStep = e.detail.current
  // 避免循环更新
  if (currentStep.value !== newStep) {
    currentStep.value = newStep
    // 如果进入步骤4且还没有关键词，生成关键词
    if (newStep === 3 && formData.keywords.length === 0) {
      generateKeywords()
    }
  }
}

async function generateKeywords() {
  if (isGeneratingKeywords.value) return
  
  isGeneratingKeywords.value = true
  
  try {
    // 构建请求数据（使用 formData，不是 formData.value）
    const requestData = {
      messages: [
        {
          role: 'user' as const,
          content: `基于以下IP信息，生成5-8个创作关键词：\n名称：${formData.name}\n行业：${formData.industry}\n受众：${formData.target_audience}\n风格：${formData.tone}\n描述：${formData.introduction}`
        }
      ],
      step: 3,
      context: {
        name: formData.name,
        industry: formData.industry,
        target_audience: formData.target_audience,
        tone: formData.tone,
        introduction: formData.introduction
      }
    }
    
    const response = await aiCollectIPInfo(requestData)
    
    // 从回复中提取关键词（简单处理，实际可能需要后端返回结构化数据）
    if (response.reply) {
      // 尝试从回复中提取关键词
      const keywords = extractKeywords(response.reply)
      if (keywords.length > 0) {
        formData.keywords = keywords
      } else {
        // 如果没有提取到，使用默认关键词
        formData.keywords = generateDefaultKeywords()
      }
    } else {
      formData.keywords = generateDefaultKeywords()
    }
  } catch (error: any) {
    console.error('生成关键词失败:', error)
    // 使用默认关键词
    formData.keywords = generateDefaultKeywords()
    uni.showToast({
      title: '关键词生成失败，请手动添加',
      icon: 'none'
    })
  } finally {
    isGeneratingKeywords.value = false
  }
}

function extractKeywords(text: string): string[] {
  // 简单的关键词提取逻辑
  const keywords: string[] = []
  const lines = text.split('\n')
  
  // 方法1: 查找包含"关键词"、"标签"等字样的行
  for (const line of lines) {
    if (line.includes('关键词') || line.includes('标签') || line.includes('标签：')) {
      // 提取#开头的标签
      const hashMatches = line.match(/#[\u4e00-\u9fa5a-zA-Z0-9]+/g)
      if (hashMatches) {
        keywords.push(...hashMatches.map(m => m.replace('#', '')))
      }
      
      // 提取冒号后的内容
      const colonIndex = line.indexOf('：') || line.indexOf(':')
      if (colonIndex > -1) {
        const afterColon = line.substring(colonIndex + 1).trim()
        // 尝试分割逗号、空格等
        const parts = afterColon.split(/[，,、\s]+/).filter(p => p.trim())
        keywords.push(...parts.slice(0, 5))
      }
    }
  }
  
  // 方法2: 如果没有找到，尝试从整个文本中提取#标签
  if (keywords.length === 0) {
    const hashMatches = text.match(/#[\u4e00-\u9fa5a-zA-Z0-9]+/g)
    if (hashMatches) {
      keywords.push(...hashMatches.map(m => m.replace('#', '')))
    }
  }
  
  // 去重并限制数量
  const uniqueKeywords = Array.from(new Set(keywords)).filter(k => k.length > 0 && k.length <= 10)
  return uniqueKeywords.slice(0, 8) // 最多8个
}

function generateDefaultKeywords(): string[] {
  // 基于已填信息生成默认关键词（使用 formData，不是 formData.value）
  const keywords: string[] = []
  
  if (formData.industry) {
    keywords.push(formData.industry)
  }
  if (formData.tone) {
    keywords.push(formData.tone)
  }
  if (formData.target_audience) {
    // 从目标受众中提取关键词（简单处理）
    const audience = formData.target_audience.trim()
    if (audience.length > 0 && audience.length <= 10) {
      keywords.push(audience)
    }
  }
  
  return keywords.length > 0 ? keywords : ['IP创作', '内容营销']
}

function handlePrev() {
  if (currentStep.value > 0) {
    currentStep.value--
  }
}

function handleNext() {
  if (!canNext.value) {
    let tipText = '请完成必填项'
    if (currentStep.value === 0 && !formData.name.trim()) {
      tipText = '请输入项目名称'
    } else if (currentStep.value === 0 && !formData.industry) {
      tipText = '请选择行业赛道'
    } else if (currentStep.value === 1 && !formData.target_audience.trim()) {
      tipText = '请输入目标受众'
    } else if (currentStep.value === 1 && !formData.target_pains.trim()) {
      tipText = '请输入目标人群痛点'
    } else if (currentStep.value === 2 && !formData.tone) {
      tipText = '请选择语气风格'
    } else if (currentStep.value === 2 && formData.introduction.trim().length < 50) {
      tipText = 'IP概况描述至少需要50字'
    }
    
    uni.showToast({
      title: tipText,
      icon: 'none'
    })
    return
  }
  
  if (currentStep.value < 3) {
    currentStep.value++
    
    // 如果进入步骤4，生成关键词
    if (currentStep.value === 3 && formData.keywords.length === 0) {
      generateKeywords()
    }
  }
}

function handleComplete() {
  if (!canComplete.value) {
    uni.showToast({
      title: '请至少添加一个关键词',
      icon: 'none'
    })
    return
  }
  
  // 构建表单数据（用于生成报告）
  const collectedData: IPCollectFormData = {
    name: formData.name,
    industry: formData.industry,
    industry_understanding: formData.industry_understanding || '',
    unique_views: formData.unique_views || '',
    tone: formData.tone,
    catchphrase: formData.catchphrase || '',
    target_audience: formData.target_audience,
    target_pains: formData.target_pains || '',
    introduction: formData.introduction,
    keywords: formData.keywords
  }
  
  // 保存表单数据到本地存储，然后跳转到报告页面
  try {
    const formDataStr = JSON.stringify(collectedData)
    uni.setStorageSync('ip_form_data_temp', formDataStr)

    console.log('表单数据已保存，准备跳转到报告页面')

    // 跳转到报告展示页面（报告页面会调用接口生成报告）
    uni.navigateTo({
      url: '/pages/project/report',
      success: () => {
        console.log('跳转成功')
        // 跳转成功后，关闭当前对话框
        // emit('close')
      },
      fail: (err) => {
        console.error('跳转失败:', err)
        uni.showToast({
          title: '跳转失败',
          icon: 'none'
        })
      }
    })
  } catch (error: any) {
    console.error('保存数据失败:', error)
    uni.showToast({
      title: error.message || '保存数据失败',
      icon: 'none',
      duration: 2000
    })
  }
}


function handleClose() {
  emit('close')
}

function handleFormDataUpdate(data: Partial<ProjectFormData>) {
  // 更新 formData（reactive 对象，直接赋值）
  Object.assign(formData, data)
}
</script>

<style lang="scss" scoped>
@import '@/styles/_variables.scss';
@import '@/styles/_mixins.scss';

.ip-collect-dialog {
  z-index: $z-index-modal;
  background: $bg-light;
}

.dialog-content {
  width: 100%;
  height: 100vh;
  background: $white;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

// Swiper容器
.step-swiper {
  flex: 1;
  height: 0;
}

// 底部导航
.dialog-footer {
  position: fixed;
  bottom: 0;
  width: 100%;
  display: flex;
  gap: $spacing-sm;
  padding: $spacing-md $spacing-lg;
  @include safe-area-bottom-padding;
  border-top: 1rpx solid $border-color;
  background: $white;
  box-shadow: 0 -4rpx 12rpx rgba(0, 0, 0, 0.04);
  
  .nav-btn {
    flex: 1;
    height: 88rpx;
    border-radius: $radius-xl;
    @include flex-center;
    font-size: $font-size-md;
    font-weight: 500;
    transition: all $transition-base;
    
    &.prev-btn {
      background: $bg-light;
      color: $text-second;
      
      &:active {
        background: rgba(0, 0, 0, 0.05);
      }
    }
    
    &.next-btn {
      background: linear-gradient(135deg, $primary-orange 0%, $primary-orange-alt 100%);
      color: $white;
      box-shadow: 0 4rpx 12rpx rgba($primary-orange, 0.3);
      
      &:active {
        transform: scale(0.98);
      }
      
      &.disabled {
        background: $border-color;
        color: $text-second;
        box-shadow: none;
      }
    }
    
    &.complete-btn {
      background: $text-main;
      color: $white;
      box-shadow: 0 4rpx 12rpx rgba(0, 0, 0, 0.2);
      
      &:active {
        transform: scale(0.98);
      }
      
      &.disabled {
        background: $border-color;
        color: $text-second;
        box-shadow: none;
      }
    }
  }
}
</style>
