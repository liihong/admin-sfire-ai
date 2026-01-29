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
            :form-data="{ name: formData.name, industry: formData.industry }"
            :industry-options="industryOptions"
            :preview-data="previewData"
            @update:form-data="handleFormDataUpdate"
          />
        </swiper-item>
        
        <!-- 步骤2: 注入灵魂 -->
        <swiper-item>
          <StepSoul
            :form-data="{
              target_audience: formData.target_audience
            }"
            :preview-data="previewData"
            @update:form-data="handleFormDataUpdate"
          />
        </swiper-item>
        
        <!-- 步骤3: 定义风格 -->
        <swiper-item>
          <StepStyle
            :form-data="{
              tone: formData.tone,
              introduction: formData.introduction,
              catchphrase: formData.catchphrase
            }"
            :tone-options="toneOptions"
            :preview-data="previewData"
            @update:form-data="handleFormDataUpdate"
          />
        </swiper-item>
        
        <!-- 步骤4: 激活大脑 -->
        <swiper-item>
          <StepBrain
            :keywords="formData.keywords"
            :is-generating-keywords="isGeneratingKeywords"
            @update:keywords="formData.keywords = $event"
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
          <text class="btn-text">激活 IP 并进入工作站 →</text>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import { getProjectOptions, type DictOption, aiCollectIPInfo } from '@/api/project'
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
  (e: 'complete', data: any): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

// 步骤定义
const steps = [
  { label: '设定身份', icon: 'account', iconType: 'u-icon' as const, key: 'identity' },
  { label: '注入灵魂', icon: 'star', iconType: 'u-icon' as const, key: 'soul' },
  { label: '定义风格', icon: 'fingerprint', iconType: 'u-icon' as const, key: 'fingerprint' },
  { label: '激活大脑', icon: 'grid', iconType: 'u-icon' as const, key: 'grid' }
]

// 表单数据
const formData = ref({
  // 步骤1: 基本信息
  name: '',
  industry: '',
  
  // 步骤2: 目标受众
  target_audience: '',
  
  // 步骤3: 风格设定
  tone: '',
  introduction: '',
  catchphrase: '',
  
  // 步骤4: 关键词
  keywords: [] as string[]
})

// 选项数据
const industryOptions = ref<DictOption[]>([])
const toneOptions = ref<DictOption[]>([])

// 状态
const currentStep = ref(0)
const isGeneratingKeywords = ref(false)

// IP画像预览数据
const previewData = computed(() => {
  return {
    name: formData.value.name || '未命名',
    industry: formData.value.industry || '未选择',
    tone: formData.value.tone || '未选择',
    target_audience: formData.value.target_audience || '未填写',
    keywords: formData.value.keywords.length > 0 ? formData.value.keywords : []
  }
})

// 验证逻辑
const canNext = computed(() => {
  switch (currentStep.value) {
    case 0:
      return formData.value.name.trim() && formData.value.industry
    case 1:
      return formData.value.target_audience.trim().length > 0
    case 2:
      return formData.value.tone && 
             formData.value.introduction.trim().length >= 50
    default:
      return false
  }
})

const canComplete = computed(() => {
  return formData.value.keywords.length > 0
})

// 初始化
watch(() => props.visible, (newVal) => {
  if (newVal) {
    initDialog()
  }
})

onMounted(() => {
  loadOptions()
})

async function loadOptions() {
  try {
    const options = await getProjectOptions()
    industryOptions.value = options.industries || []
    toneOptions.value = options.tones || []
  } catch (error: any) {
    console.error('加载选项失败:', error)
    // 使用默认值
    industryOptions.value = [
      { label: '通用', value: '通用' },
      { label: '医疗健康', value: '医疗健康' },
      { label: '教育培训', value: '教育培训' }
    ]
    toneOptions.value = [
      { label: '专业亲和', value: '专业亲和' },
      { label: '幽默风趣', value: '幽默风趣' },
      { label: '温暖治愈', value: '温暖治愈' }
    ]
  }
}

function initDialog() {
  currentStep.value = 0
  formData.value = {
    name: '',
    industry: '',
    target_audience: '',
    tone: '',
    introduction: '',
    catchphrase: '',
    keywords: []
  }
}

function handleSwiperChange(e: any) {
  const newStep = e.detail.current
  // 避免循环更新
  if (currentStep.value !== newStep) {
    currentStep.value = newStep
    // 如果进入步骤4且还没有关键词，生成关键词
    if (newStep === 3 && formData.value.keywords.length === 0) {
      generateKeywords()
    }
  }
}

async function generateKeywords() {
  if (isGeneratingKeywords.value) return
  
  isGeneratingKeywords.value = true
  
  try {
    // 构建请求数据
    const requestData = {
      messages: [
        {
          role: 'user' as const,
          content: `基于以下IP信息，生成5-8个创作关键词：\n名称：${formData.value.name}\n行业：${formData.value.industry}\n受众：${formData.value.target_audience}\n风格：${formData.value.tone}\n描述：${formData.value.introduction}`
        }
      ],
      step: 3,
      context: {
        name: formData.value.name,
        industry: formData.value.industry,
        target_audience: formData.value.target_audience,
        tone: formData.value.tone,
        introduction: formData.value.introduction
      }
    }
    
    const response = await aiCollectIPInfo(requestData)
    
    // 从回复中提取关键词（简单处理，实际可能需要后端返回结构化数据）
    if (response.reply) {
      // 尝试从回复中提取关键词
      const keywords = extractKeywords(response.reply)
      if (keywords.length > 0) {
        formData.value.keywords = keywords
      } else {
        // 如果没有提取到，使用默认关键词
        formData.value.keywords = generateDefaultKeywords()
      }
    } else {
      formData.value.keywords = generateDefaultKeywords()
    }
  } catch (error: any) {
    console.error('生成关键词失败:', error)
    // 使用默认关键词
    formData.value.keywords = generateDefaultKeywords()
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
  // 基于已填信息生成默认关键词
  const keywords: string[] = []
  
  if (formData.value.industry) {
    keywords.push(formData.value.industry)
  }
  if (formData.value.tone) {
    keywords.push(formData.value.tone)
  }
  if (formData.value.target_audience) {
    // 从目标受众中提取关键词（简单处理）
    const audience = formData.value.target_audience.trim()
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
    if (currentStep.value === 0 && !formData.value.name.trim()) {
      tipText = '请输入项目名称'
    } else if (currentStep.value === 0 && !formData.value.industry) {
      tipText = '请选择行业赛道'
    } else if (currentStep.value === 1 && !formData.value.target_audience.trim()) {
      tipText = '请输入目标受众'
    } else if (currentStep.value === 2 && !formData.value.tone) {
      tipText = '请选择语气风格'
    } else if (currentStep.value === 2 && formData.value.introduction.trim().length < 50) {
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
    if (currentStep.value === 3 && formData.value.keywords.length === 0) {
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
  
  // 构建收集的数据，符合数据库要求的格式（扁平格式，后端支持扁平方式）
  const collectedData = {
    name: formData.value.name,
    industry: formData.value.industry,
    tone: formData.value.tone,
    catchphrase: formData.value.catchphrase || '',
    target_audience: formData.value.target_audience,
    introduction: formData.value.introduction,
    keywords: formData.value.keywords
  }
  
  emit('complete', collectedData)
}

function handleClose() {
  emit('close')
}

function handleFormDataUpdate(data: Partial<typeof formData.value>) {
  Object.assign(formData.value, data)
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
