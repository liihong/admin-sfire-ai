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
 * 4. 表单数据变化时自动保存到 store（持久化到 localStorage），防抖500ms
 * 5. 用户完成所有步骤后，调用 handleComplete()
 * 6. handleComplete() 将 formData 转换为 IPCollectFormData（只包含收集的字段）
 * 7. 保存到 store 并跳转到报告页面
 * 8. 报告页面可以保存项目，保存成功后自动清空缓存
 * 
 * 持久化机制：
 * - 填写过程中自动保存到 localStorage（通过 projectStore.saveIPCollectFormData）
 * - 点击创建项目按钮时，如果有缓存数据会弹出提示框，让用户选择"继续使用"或"清空重填"
 * - 用户选择"继续使用"：自动回填缓存数据到表单
 * - 用户选择"清空重填"：清空缓存并重置表单
 * - 项目创建成功后自动清空缓存（create.vue 和 report.vue 中都会清空）
 * 
 * 数据流转：
 * formData (ProjectFormData) → formDataToIPCollectFormData() → 
 * IPCollectFormData → store (localStorage) → 
 * 报告页面 → ipCollectFormDataToProjectFormData() → 
 * ProjectFormData → formDataToCreateRequest() → createProject() → ProjectModel → store
 */

import { ref, computed, watch, onMounted, onUnmounted, nextTick } from 'vue'
import { type IPCollectFormData } from '@/api/project'
import type { ProjectFormData } from '@/types/project'
import { usePersonaForm } from '@/composables/usePersonaForm'
import { useProjectStore } from '@/stores/project'
import { formDataToIPCollectFormData, ipCollectFormDataToProjectFormData } from '@/utils/project'
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
// 使用 onMounted 确保只初始化一次，避免响应式循环
onMounted(() => {
  // 组件挂载时初始化（visible 在 create.vue 中始终为 true）
  initDialog()
})

// 是否启用自动保存（初始化完成后启用）
const enableAutoSave = ref(false)

// 是否已经初始化过（使用普通变量，避免响应式循环）
let isInitialized = false

// 监听表单数据变化，自动保存到store（使用防抖，避免频繁保存）
let saveTimer: ReturnType<typeof setTimeout> | null = null
watch(() => formData, () => {
  // 如果未启用自动保存，跳过
  if (!enableAutoSave.value) return

  // 清除之前的定时器
  if (saveTimer) {
    clearTimeout(saveTimer)
    saveTimer = null
  }

  // 延迟500ms保存，避免频繁保存
  saveTimer = setTimeout(() => {
    saveFormDataToStore()
    saveTimer = null
  }, 500)
}, { deep: true })

// 组件卸载时清理定时器，防止内存泄漏
onUnmounted(() => {
  if (saveTimer) {
    clearTimeout(saveTimer)
    saveTimer = null
  }
})

/**
 * 初始化对话框
 * 检查是否有缓存的表单数据，如果有则提示用户是否继续使用
 */
async function initDialog() {
  // 防止重复初始化
  if (isInitialized) {
    return
  }

  // 立即标记为已初始化，防止重复调用
  isInitialized = true

  // 使用 nextTick 确保在下一个事件循环中执行，避免响应式循环
  await nextTick()

  currentStep.value = 0
  // 重要：先禁用自动保存，避免 resetForm() 触发自动保存覆盖缓存
  enableAutoSave.value = false
  
  // 检查是否有缓存的表单数据（在重置表单之前检查，避免被覆盖）
  const cachedData = projectStore.loadIPCollectFormData()

  if (cachedData) {
    // 有缓存数据，提示用户是否继续使用
    uni.showModal({
      title: '发现未完成的表单',
      content: `检测到您之前填写的IP信息（${cachedData.name || '未命名'}），是否继续使用？`,
      confirmText: '继续使用',
      cancelText: '清空重填',
      success: async (res) => {
        if (res.confirm) {
          // 用户选择继续使用，加载缓存数据
          // 注意：此时 enableAutoSave 仍然是 false，加载数据不会触发自动保存
          loadCachedFormData(cachedData)
          // 加载完成后启用自动保存
          enableAutoSave.value = true
        } else {
          // 用户选择清空，重置表单并清除缓存
          // 先清空缓存，确保不会被自动保存覆盖
          projectStore.clearIPCollectFormData()
          // 使用 Promise 延迟执行，避免嵌套 setTimeout
          await clearAndResetForm()
        }
      },
      fail: () => {
        // 用户取消操作，默认加载缓存数据（不清空缓存）
        // 注意：此时 enableAutoSave 仍然是 false，加载数据不会触发自动保存
        loadCachedFormData(cachedData)
      // 加载完成后启用自动保存
        enableAutoSave.value = true
      }
    })
  } else {
    // 没有缓存数据，直接重置表单
    // 注意：此时 enableAutoSave 是 false，resetForm() 不会触发自动保存
    resetForm()
    // 重置完成后启用自动保存
    enableAutoSave.value = true
  }
}

/**
 * 清空并重置表单（异步执行，避免 watch 延迟覆盖清空操作）
 */
async function clearAndResetForm() {
  // 等待当前事件循环完成，确保清空操作生效
  await nextTick()
  // 重置表单（此时 enableAutoSave 仍然是 false，不会触发自动保存）
  resetForm()
  // 延迟启用自动保存，确保 watch 的延迟执行（500ms）不会覆盖清空操作
  await new Promise(resolve => setTimeout(resolve, 600))
  enableAutoSave.value = true
}

/**
 * 加载缓存的表单数据到formData
 * 使用工具函数将 IPCollectFormData 转换为 ProjectFormData
 */
function loadCachedFormData(cachedData: IPCollectFormData) {
  const projectFormData = ipCollectFormDataToProjectFormData(cachedData)
  Object.assign(formData, projectFormData)
}

/**
 * Swiper 切换事件类型
 */
interface SwiperChangeEvent {
  detail: {
    current: number
  }
}

function handleSwiperChange(e: SwiperChangeEvent) {
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
  
  // 使用工具函数将 formData 转换为 IPCollectFormData
  const collectedData = formDataToIPCollectFormData(formData)
  
  // 保存表单数据到store（持久化）
  // 注意：这里不立即清空缓存，等用户点击"注入基因库"后再清空
  projectStore.saveIPCollectFormData(collectedData)

  // 跳转到报告展示页面（报告页面会调用接口生成报告）
  uni.navigateTo({
    url: '/pages/project/report',
    success: () => {
      // 跳转成功
    },
    fail: () => {
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

  // 只有在启用自动保存时才保存到store（避免初始化时保存空表单）
  if (enableAutoSave.value) {
    // 自动保存到store（持久化）
    saveFormDataToStore()
  }
}

/**
 * 检查 introduction 是否是模板文本（占位符）
 * StepStyle 组件会在 introduction 为空时自动设置模板文本
 */
function isIntroductionTemplate(text: string): boolean {
  if (!text || !text.trim()) return true
  // 检查是否包含模板的关键标识
  return text.includes('个人经历：') &&
    text.includes('为什么做这个项目：') &&
    text.includes('产品或服务特色：')
}

/**
 * 检查表单是否为空（只有默认值，没有用户实际输入）
 * 如果表单为空，不应该保存到缓存
 */
function isFormEmpty(): boolean {
  const isIntroTemplate = isIntroductionTemplate(formData.introduction)
  // 检查关键字段是否为空，如果都是空说明用户还没有开始填写
  // introduction 如果是模板文本，也应该视为空
  return !formData.name.trim() &&
    !formData.target_audience.trim() &&
    !formData.target_pains.trim() &&
    (isIntroTemplate || !formData.introduction.trim()) &&
    formData.keywords.length === 0 &&
    !formData.industry_understanding.trim() &&
    !formData.unique_views.trim() &&
    !formData.catchphrase.trim()
}

/**
 * 保存表单数据到store（持久化）
 * 使用工具函数将formData转换为IPCollectFormData格式后保存
 * 如果表单为空（只有默认值），则不保存
 */
function saveFormDataToStore() {
  // 如果表单为空（只有默认值），不保存到缓存
  if (isFormEmpty()) {
    return
  }

  const collectedData = formDataToIPCollectFormData(formData)
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
