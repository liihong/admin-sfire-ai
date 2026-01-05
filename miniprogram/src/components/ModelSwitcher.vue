<template>
  <view 
    class="model-switcher" 
    :style="{ 
      right: position.x + 'rpx', 
      bottom: position.y + 'rpx' 
    }"
    @touchstart="onTouchStart"
    @touchmove.prevent="onTouchMove"
    @touchend="onTouchEnd"
    @tap="showModelPicker"
  >
    <view class="switcher-ball" :class="{ 'is-dragging': isDragging }">
      <text class="ball-icon">{{ currentModel.icon }}</text>
      <view class="ball-indicator"></view>
    </view>
    
    <!-- 模型名称提示 -->
    <view class="model-tooltip" v-if="showTooltip">
      <text class="tooltip-text">{{ currentModel.name }}</text>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, onUnmounted } from 'vue'
import { useSettingsStore, MODEL_LIST } from '@/stores/settings'
import type { ModelType } from '@/stores/settings'

const settingsStore = useSettingsStore()

// 当前模型
const currentModel = computed(() => settingsStore.currentModel)

// 位置状态
const position = reactive({
  x: 16, // 距离右边
  y: 280 // 距离底部
})

// 拖拽状态
const isDragging = ref(false)
const showTooltip = ref(false)
let tooltipTimer: number | null = null

// 触摸起始点
const touchStart = reactive({
  x: 0,
  y: 0,
  posX: 0,
  posY: 0,
  time: 0
})

// 屏幕信息
const screenInfo = reactive({
  width: 750,
  height: 1334
})

onMounted(() => {
  // 获取屏幕尺寸
  const systemInfo = uni.getSystemInfoSync()
  screenInfo.width = systemInfo.windowWidth * (750 / systemInfo.windowWidth)
  screenInfo.height = systemInfo.windowHeight * (750 / systemInfo.windowWidth)
  
  // 显示提示
  showTooltipBriefly()
})

onUnmounted(() => {
  if (tooltipTimer) {
    clearTimeout(tooltipTimer)
  }
})

/**
 * 短暂显示模型提示
 */
function showTooltipBriefly() {
  showTooltip.value = true
  if (tooltipTimer) clearTimeout(tooltipTimer)
  tooltipTimer = setTimeout(() => {
    showTooltip.value = false
  }, 2000) as unknown as number
}

/**
 * 触摸开始
 */
function onTouchStart(e: TouchEvent) {
  const touch = e.touches[0]
  touchStart.x = touch.clientX
  touchStart.y = touch.clientY
  touchStart.posX = position.x
  touchStart.posY = position.y
  touchStart.time = Date.now()
}

/**
 * 触摸移动
 */
function onTouchMove(e: TouchEvent) {
  isDragging.value = true
  const touch = e.touches[0]
  const systemInfo = uni.getSystemInfoSync()
  const scale = 750 / systemInfo.windowWidth
  
  // 计算移动距离（注意：x 是距离右边，所以移动方向相反）
  const deltaX = (touchStart.x - touch.clientX) * scale
  const deltaY = (touchStart.y - touch.clientY) * scale
  
  // 更新位置，限制在屏幕范围内
  const ballSize = 80 // 球的大小
  const margin = 16 // 边距
  
  position.x = Math.max(margin, Math.min(screenInfo.width - ballSize - margin, touchStart.posX + deltaX))
  position.y = Math.max(margin, Math.min(screenInfo.height - ballSize - margin - 120, touchStart.posY - deltaY))
}

/**
 * 触摸结束
 */
function onTouchEnd() {
  // 如果拖拽时间很短，认为是点击
  const touchDuration = Date.now() - touchStart.time
  if (touchDuration < 200 && !isDragging.value) {
    // 点击事件由 @tap 处理
  }
  
  isDragging.value = false
  
  // 吸附到屏幕边缘
  const centerX = screenInfo.width / 2
  const ballCenterX = screenInfo.width - position.x - 50
  
  // 根据当前位置决定吸附到左边还是右边
  if (ballCenterX < centerX) {
    position.x = screenInfo.width - 80 - 16 // 吸附到左边
  } else {
    position.x = 16 // 吸附到右边
  }
}

/**
 * 显示模型选择器
 */
function showModelPicker() {
  // 只有点击（非拖拽）时才显示
  if (isDragging.value) return
  
  const availableModels = MODEL_LIST.filter(m => m.available)
  const itemList = availableModels.map(m => `${m.icon} ${m.name} - ${m.description}`)
  
  uni.showActionSheet({
    itemList,
    success: (res) => {
      const selectedModel = availableModels[res.tapIndex]
      if (selectedModel) {
        settingsStore.setModelType(selectedModel.type)
        showTooltipBriefly()
        
        uni.showToast({
          title: `已切换至 ${selectedModel.name}`,
          icon: 'none',
          duration: 1500
        })
      }
    }
  })
}
</script>

<style lang="scss" scoped>
.model-switcher {
  position: fixed;
  z-index: 9999;
  opacity: 0.7;
  transition: opacity 0.3s ease;
  
  &:active {
    opacity: 1;
  }
  
  .switcher-ball {
    width: 80rpx;
    height: 80rpx;
    border-radius: 50%;
    background: linear-gradient(145deg, rgba(255, 255, 255, 0.95), rgba(240, 243, 248, 0.95));
    box-shadow: 
      0 6rpx 24rpx rgba(0, 0, 0, 0.12),
      0 2rpx 6rpx rgba(0, 0, 0, 0.08),
      inset 0 -2rpx 4rpx rgba(0, 0, 0, 0.04);
    display: flex;
    align-items: center;
    justify-content: center;
    position: relative;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    
    // 外发光效果
    &::before {
      content: '';
      position: absolute;
      inset: -3rpx;
      border-radius: 50%;
      background: linear-gradient(145deg, #4facfe, #00f2fe);
      opacity: 0.3;
      z-index: -1;
      animation: pulse 2s ease-in-out infinite;
    }
    
    &:active,
    &.is-dragging {
      transform: scale(1.1);
      box-shadow: 
        0 10rpx 32rpx rgba(79, 172, 254, 0.35),
        0 3rpx 10rpx rgba(0, 0, 0, 0.1);
      
      &::before {
        opacity: 0.5;
      }
    }
    
    .ball-icon {
      font-size: 40rpx;
      z-index: 1;
    }
    
    .ball-indicator {
      position: absolute;
      top: 6rpx;
      right: 6rpx;
      width: 14rpx;
      height: 14rpx;
      background: linear-gradient(135deg, #43e97b, #38f9d7);
      border-radius: 50%;
      border: 2rpx solid #fff;
      box-shadow: 0 2rpx 4rpx rgba(67, 233, 123, 0.4);
    }
  }
  
  .model-tooltip {
    position: absolute;
    right: 100rpx;
    top: 50%;
    transform: translateY(-50%);
    background: rgba(0, 0, 0, 0.75);
    backdrop-filter: blur(10px);
    padding: 10rpx 20rpx;
    border-radius: 16rpx;
    white-space: nowrap;
    animation: fadeIn 0.3s ease-out;
    
    // 箭头
    &::after {
      content: '';
      position: absolute;
      right: -10rpx;
      top: 50%;
      transform: translateY(-50%);
      border: 5rpx solid transparent;
      border-left-color: rgba(0, 0, 0, 0.75);
    }
    
    .tooltip-text {
      font-size: 22rpx;
      color: #ffffff;
      font-weight: 500;
    }
  }
}

@keyframes pulse {
  0%, 100% {
    transform: scale(1);
    opacity: 0.3;
  }
  50% {
    transform: scale(1.15);
    opacity: 0.2;
  }
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(-50%) translateX(10rpx);
  }
  to {
    opacity: 1;
    transform: translateY(-50%) translateX(0);
  }
}
</style>




