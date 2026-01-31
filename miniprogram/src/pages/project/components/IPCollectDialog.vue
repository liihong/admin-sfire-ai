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
:industry-options="industryOptions" :tone-options="toneOptions"
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
import { type IPCollectFormData } from '@/api/project'
import type { ProjectFormData } from '@/types/project'
import { usePersonaForm } from '@/composables/usePersonaForm'
import { useProjectStore } from '@/stores/project'
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

// Store
const projectStore = useProjectStore()

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
  // 最后一步只需要基本信息完整即可，关键词可选
  return formData.name.trim() && formData.industry && formData.target_audience.trim() && formData.tone && formData.introduction.trim().length >= 50
})

// 初始化：当对话框显示时检查缓存并初始化表单
watch(() => props.visible, (newVal) => {
  if (newVal) {
    initDialog()
  }
})

// 是否启用自动保存（初始化完成后启用）
const enableAutoSave = ref(false)

// 监听表单数据变化，自动保存到store（使用防抖，避免频繁保存）
let saveTimer: ReturnType<typeof setTimeout> | null = null
watch(() => formData, () => {
  // 如果未启用自动保存，跳过
  if (!enableAutoSave.value) return

  // 清除之前的定时器
  if (saveTimer) {
    clearTimeout(saveTimer)
  }

  // 延迟500ms保存，避免频繁保存
  saveTimer = setTimeout(() => {
    saveFormDataToStore()
  }, 500)
}, { deep: true })

/**
 * 初始化对话框
 * 检查是否有缓存的表单数据，如果有则提示用户
 */
async function initDialog() {
  currentStep.value = 0
  enableAutoSave.value = false // 初始化时禁用自动保存
  
  // 检查是否有缓存的表单数据
  const cachedData = projectStore.loadIPCollectFormData()

  if (cachedData) {
    // 有缓存数据，提示用户是否继续使用
    uni.showModal({
      title: '发现未完成的表单',
      content: `检测到您之前填写的IP信息（${cachedData.name || '未命名'}），是否继续使用？`,
      confirmText: '继续使用',
      cancelText: '清空重填',
      success: (res) => {
        if (res.confirm) {
          // 用户选择继续使用，加载缓存数据
          loadCachedFormData(cachedData)
        } else {
          // 用户选择清空，重置表单并清除缓存
          resetForm()
          projectStore.clearIPCollectFormData()
        }
        // 初始化完成后启用自动保存
        enableAutoSave.value = true
      }
    })
  } else {
    // 没有缓存数据，直接重置表单
    resetForm()
    // 初始化完成后启用自动保存
    enableAutoSave.value = true
  }
}

/**
 * 加载缓存的表单数据到formData
 */
function loadCachedFormData(cachedData: IPCollectFormData) {
  // 将IPCollectFormData转换为ProjectFormData格式
  Object.assign(formData, {
    name: cachedData.name || '',
    industry: cachedData.industry || '',
    industry_understanding: cachedData.industry_understanding || '',
    unique_views: cachedData.unique_views || '',
    tone: cachedData.tone || '',
    catchphrase: cachedData.catchphrase || '',
    target_audience: cachedData.target_audience || '',
    target_pains: cachedData.target_pains || '',
    introduction: cachedData.introduction || '',
    keywords: cachedData.keywords || [],
    benchmark_accounts: [],
    content_style: '',
    taboos: []
  })
}

function handleSwiperChange(e: any) {
  const newStep = e.detail.current
  // 避免循环更新
  if (currentStep.value !== newStep) {
    currentStep.value = newStep
  }
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
  }
}

function handleComplete() {
  if (!canComplete.value) {
    uni.showToast({
      title: '请完成必填项',
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
  
  // 保存表单数据到store（持久化）
  // 注意：这里不立即清空缓存，等用户点击"注入基因库"后再清空
  projectStore.saveIPCollectFormData(collectedData)

  // 跳转到报告展示页面（报告页面会调用接口生成报告）
  uni.navigateTo({
    url: '/pages/project/report',
    success: () => {
      // 跳转成功
    },
    fail: (err) => {
      console.error('跳转失败:', err)
      uni.showToast({
        title: '跳转失败',
        icon: 'none'
      })
    }
  })
}


function handleClose() {
  emit('close')
}

function handleFormDataUpdate(data: Partial<ProjectFormData>) {
  // 更新 formData（reactive 对象，直接赋值）
  Object.assign(formData, data)

  // 自动保存到store（持久化）
  saveFormDataToStore()
}

/**
 * 保存表单数据到store（持久化）
 * 将formData转换为IPCollectFormData格式后保存
 */
function saveFormDataToStore() {
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

  // 保存到store（会自动持久化到本地存储）
  projectStore.saveIPCollectFormData(collectedData)
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
