<template>
  <!-- Loading状态 - 步骤式进度提示 -->
  <view class="loading-section">
    <view class="loading-header">
      <u-loading-icon mode="spinner" color="#F37021" size="60"></u-loading-icon>
      <text class="loading-title">AI正在生成报告中</text>
      <text class="loading-subtitle">请耐心等待，预计需要30-60秒</text>
    </view>

    <view class="steps-container">
      <view v-for="(step, index) in loadingSteps" :key="index" class="step-item" :class="{
        'active': step.status === 'active',
        'completed': step.status === 'completed',
        'pending': step.status === 'pending'
      }">
        <view class="step-icon-wrapper">
          <view v-if="step.status === 'completed'" class="step-icon completed-icon">
            <u-icon name="checkmark" color="#FFFFFF" size="14"></u-icon>
          </view>
          <view v-else-if="step.status === 'active'" class="step-icon active-icon">
            <u-loading-icon mode="spinner" color="#FFFFFF" size="14"></u-loading-icon>
          </view>
          <view v-else class="step-icon pending-icon">
            <text class="step-number">{{ index + 1 }}</text>
          </view>
        </view>
        <view class="step-content">
          <text class="step-title">{{ step.title }}</text>
          <text v-if="step.status === 'active'" class="step-desc">{{ step.desc }}</text>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, onUnmounted } from 'vue'

// 步骤状态类型
type StepStatus = 'pending' | 'active' | 'completed'

// 步骤接口定义
interface LoadingStep {
  title: string
  desc: string
  status: StepStatus
}

// 加载步骤配置
const loadingSteps = ref<LoadingStep[]>([
  { title: '分析IP信息', desc: '正在解析IP基本信息...', status: 'pending' },
  { title: '生成数字化人格画像', desc: '正在构建人格标签和原型...', status: 'pending' },
  { title: '分析内容护城河', desc: '正在挖掘反共识洞察和情感钩子...', status: 'pending' },
  { title: '生成语言指纹分析', desc: '正在建模语感和氛围特征...', status: 'pending' },
  { title: '评估商业潜力', desc: '正在分析爆款潜质和风险点...', status: 'pending' },
  { title: '生成专家寄语', desc: '正在撰写专业建议...', status: 'pending' }
])

// 步骤进度定时器
let stepTimer: ReturnType<typeof setTimeout> | null = null

// 组件卸载时清理定时器
onUnmounted(() => {
  if (stepTimer) {
    clearTimeout(stepTimer)
    stepTimer = null
  }
})

/**
 * 初始化步骤状态（重置所有步骤为pending）
 */
function initSteps() {
  loadingSteps.value.forEach(step => {
    step.status = 'pending'
  })
}

/**
 * 开始步骤进度动画
 */
function startStepProgress() {
  let currentStepIndex = 0

  // 立即激活第一个步骤
  if (loadingSteps.value.length > 0) {
    loadingSteps.value[0].status = 'active'
  }

  // 每个步骤的持续时间（根据步骤索引调整，前面的步骤稍快，后面的步骤稍慢）
  const getStepDuration = (index: number) => {
    const baseDuration = 5000 // 基础持续时间2.5秒
    const variation = index * 500 // 每个步骤增加0.5秒
    return baseDuration + variation
  }

  const processNextStep = () => {
    // 完成当前步骤
    if (currentStepIndex < loadingSteps.value.length) {
      loadingSteps.value[currentStepIndex].status = 'completed'
    }

    // 移动到下一个步骤
    currentStepIndex++

    if (currentStepIndex < loadingSteps.value.length) {
      // 激活下一个步骤
      loadingSteps.value[currentStepIndex].status = 'active'
      // 设置下一个步骤的定时器
      const duration = getStepDuration(currentStepIndex)
      stepTimer = setTimeout(processNextStep, duration) as unknown as ReturnType<typeof setTimeout>
    } else {
      // 所有步骤完成，清除定时器
      stepTimer = null
    }
  }

  // 启动第一个步骤的定时器
  const firstDuration = getStepDuration(0)
  stepTimer = setTimeout(processNextStep, firstDuration) as unknown as ReturnType<typeof setTimeout>
}

/**
 * 标记所有步骤为完成，并清除定时器
 */
function completeAllSteps() {
  loadingSteps.value.forEach(step => {
    if (step.status !== 'completed') {
      step.status = 'completed'
    }
  })

  if (stepTimer) {
    clearTimeout(stepTimer)
    stepTimer = null
  }
}

/**
 * 停止步骤动画（清除定时器）
 */
function stopProgress() {
  if (stepTimer) {
    clearTimeout(stepTimer)
    stepTimer = null
  }
}

// 暴露方法给父组件调用
defineExpose({
  initSteps,
  startStepProgress,
  completeAllSteps,
  stopProgress
})
</script>

<style lang="scss" scoped>
@import '@/styles/_variables.scss';
@import '@/styles/_mixins.scss';

.loading-section {
  @include flex-column;
  gap: $spacing-xl;
  padding: $spacing-xl;
}

.loading-header {
  @include flex-center;
  @include flex-column;
  gap: $spacing-sm;

  .loading-title {
    font-size: $font-size-xl;
    font-weight: 600;
    color: $text-main;
    margin-top: $spacing-sm;
  }

  .loading-subtitle {
    font-size: $font-size-sm;
    color: $text-second;
  }
}

.steps-container {
  @include flex-column;
  gap: $spacing-lg;
  padding: $spacing-lg;
  background: $white;
  border-radius: $radius-lg;
  box-shadow: 0 2rpx 8rpx rgba(0, 0, 0, 0.04);
}

.step-item {
  @include flex-center-vertical;
  gap: $spacing-md;
  padding: $spacing-md;
  border-radius: $radius-md;
  transition: all $transition-base;

  &.pending {
    opacity: 0.5;
  }

  &.active {
    background: rgba($primary-orange, 0.05);
    opacity: 1;
    animation: pulse 2s ease-in-out infinite;
  }

  &.completed {
    opacity: 1;
  }

  // 激活状态下的标题颜色
  &.active .step-content .step-title {
    color: $primary-orange;
    font-weight: 600;
  }

  // 完成状态下的标题颜色
  &.completed .step-content .step-title {
    color: $text-main;
  }
}

.step-icon-wrapper {
  flex-shrink: 0;

  .step-icon {
    width: 35rpx;
    height: 35rpx;
    border-radius: 50%;
    @include flex-center;
    transition: all $transition-base;

    &.pending-icon {
      background: rgba($text-second, 0.1);
      border: 2rpx solid rgba($text-second, 0.2);

      .step-number {
        font-size: $font-size-md;
        font-weight: 600;
        color: $text-second;
      }
    }

    &.active-icon {
      background: linear-gradient(135deg, $primary-orange 0%, $primary-orange-alt 100%);
      box-shadow: 0 4rpx 12rpx rgba($primary-orange, 0.3);
    }

    &.completed-icon {
      background: linear-gradient(135deg, #52c41a 0%, #73d13d 100%);
      animation: scaleIn 0.3s ease-out;
    }
  }
}

.step-content {
  flex: 1;
  @include flex-column;
  gap: $spacing-xs;

  .step-title {
    font-size: $font-size-md;
    font-weight: 500;
    color: $text-main;
    transition: color $transition-base;
  }

  .step-desc {
    font-size: $font-size-sm;
    color: $text-second;
    animation: fadeIn 0.3s ease-out;
  }
}

// 动画定义
@keyframes pulse {
  0%, 100% {
    transform: scale(1);
  }
  50% {
    transform: scale(1.02);
  }
}

@keyframes scaleIn {
  0% {
    transform: scale(0);
    opacity: 0;
  }
  50% {
    transform: scale(1.1);
  }
  100% {
    transform: scale(1);
    opacity: 1;
  }
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(-10rpx);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
</style>


