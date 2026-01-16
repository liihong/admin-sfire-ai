<template>
  <view class="ip-collect-dialog" v-if="visible" @tap.stop>
    <view class="dialog-mask" @tap="handleClose"></view>
    <view class="dialog-content">
      <!-- 头部 -->
      <view class="dialog-header">
        <text class="dialog-title">AI智能填写</text>
        <view class="close-btn" @tap="handleClose">
          <text class="close-icon">×</text>
        </view>
      </view>
      
      <!-- 步骤指示器 -->
      <view class="step-indicator">
        <view 
          class="step-item"
          v-for="(step, index) in steps"
          :key="index"
          :class="{ active: currentStep >= index, completed: currentStep > index }"
        >
          <view class="step-dot">
            <text v-if="currentStep > index" class="step-check">✓</text>
            <text v-else class="step-number">{{ index + 1 }}</text>
          </view>
          <text class="step-label">{{ step.label }}</text>
        </view>
      </view>
      
      <!-- 对话区域 -->
      <scroll-view class="dialog-messages" scroll-y :scroll-top="scrollTop" scroll-with-animation>
        <view 
          class="message-item"
          v-for="(msg, index) in messages"
          :key="index"
          :class="msg.role"
        >
          <view class="message-avatar">
            <text v-if="msg.role === 'assistant'" class="avatar-icon">🤖</text>
            <text v-else class="avatar-icon">👤</text>
          </view>
          <view class="message-bubble">
            <text class="message-text">{{ msg.content }}</text>
          </view>
        </view>
        
        <!-- 加载中提示 -->
        <view class="message-item assistant" v-if="isLoading">
          <view class="message-avatar">
            <text class="avatar-icon">🤖</text>
          </view>
          <view class="message-bubble loading">
            <view class="loading-dots">
              <view class="dot"></view>
              <view class="dot"></view>
              <view class="dot"></view>
            </view>
          </view>
        </view>
      </scroll-view>
      
      <!-- 输入区域 -->
      <view class="dialog-input-area" v-if="!isComplete">
        <input 
          class="input-field"
          v-model="userInput"
          placeholder="请输入..."
          :disabled="isLoading"
          @confirm="handleSend"
          confirm-type="send"
        />
        <view 
          class="send-btn"
          :class="{ disabled: !userInput.trim() || isLoading }"
          @tap="handleSend"
        >
          <text class="send-icon">发送</text>
        </view>
      </view>
      
      <!-- 完成按钮 -->
      <view class="dialog-footer" v-if="isComplete">
        <view class="complete-btn" @tap="handleComplete">
          <text class="btn-text">完成采集</text>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, watch, nextTick } from 'vue'

interface Message {
  role: 'user' | 'assistant'
  content: string
  timestamp?: number
}

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
  { label: '基本信息', key: 'basic' },
  { label: 'IP简介', key: 'intro' },
  { label: '风格受众', key: 'style' },
  { label: '标签关键词', key: 'tags' }
]

// 状态
const currentStep = ref(0)
const messages = ref<Message[]>([])
const userInput = ref('')
const isLoading = ref(false)
const isComplete = ref(false)
const scrollTop = ref(0)
const collectedInfo = ref<Record<string, any>>({})

// 初始化对话
watch(() => props.visible, (newVal) => {
  if (newVal) {
    initDialog()
  }
})

function initDialog() {
  currentStep.value = 0
  messages.value = []
  userInput.value = ''
  isLoading.value = false
  isComplete.value = false
  collectedInfo.value = {}
  
  // 添加欢迎消息
  addMessage('assistant', '你好！我是AI助手，将帮助你完善IP信息。让我们开始吧！')
  
  // 发送初始请求
  sendMessage('', true)
}

function addMessage(role: 'user' | 'assistant', content: string) {
  messages.value.push({
    role,
    content,
    timestamp: Date.now()
  })
  scrollToBottom()
}

function scrollToBottom() {
  nextTick(() => {
    scrollTop.value = 99999
  })
}

async function sendMessage(input: string, isInit = false) {
  if (!isInit && !input.trim()) return
  
  // 添加用户消息
  if (!isInit) {
    addMessage('user', input)
    userInput.value = ''
  }
  
  isLoading.value = true
  
  try {
    const { aiCollectIPInfo } = await import('@/api/project')
    
    const response = await aiCollectIPInfo({
      messages: messages.value.map(msg => ({
        role: msg.role,
        content: msg.content
      })),
      step: currentStep.value,
      context: collectedInfo.value
    })
    
    // 添加AI回复
    addMessage('assistant', response.reply)
    
    // 更新收集的信息
    if (response.collected_info) {
      Object.assign(collectedInfo.value, response.collected_info)
    }
    
    // 检查是否完成
    if (response.is_complete) {
      isComplete.value = true
    } else if (response.next_step !== undefined) {
      currentStep.value = response.next_step
    }
    
  } catch (error: any) {
    console.error('采集对话失败:', error)
    addMessage('assistant', `抱歉，出现了错误：${error.message || '未知错误'}`)
    uni.showToast({
      title: error.message || '对话失败',
      icon: 'none'
    })
  } finally {
    isLoading.value = false
  }
}

function handleSend() {
  if (!userInput.value.trim() || isLoading.value) return
  sendMessage(userInput.value)
}

function handleComplete() {
  emit('complete', collectedInfo.value)
  handleClose()
}

function handleClose() {
  emit('close')
}
</script>

<style lang="scss" scoped>
.ip-collect-dialog {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 2000;
  display: flex;
  align-items: center;
  justify-content: center;
}

.dialog-mask {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.6);
  backdrop-filter: blur(4px);
}

.dialog-content {
  position: relative;
  width: 90%;
  max-width: 600rpx;
  max-height: 80vh;
  background: #fff;
  border-radius: 32rpx;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  animation: scaleIn 0.3s ease;
}

.dialog-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 32rpx;
  border-bottom: 1rpx solid #F3F4F6;
  
  .dialog-title {
    font-size: 32rpx;
    font-weight: 600;
    color: #1a1a2e;
  }
  
  .close-btn {
    width: 56rpx;
    height: 56rpx;
    display: flex;
    align-items: center;
    justify-content: center;
    
    .close-icon {
      font-size: 48rpx;
      color: #999;
      line-height: 1;
    }
  }
}

.step-indicator {
  display: flex;
  align-items: center;
  justify-content: space-around;
  padding: 24rpx 32rpx;
  background: #F9FAFB;
  
  .step-item {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 8rpx;
    flex: 1;
    
    .step-dot {
      width: 48rpx;
      height: 48rpx;
      border-radius: 50%;
      background: #E5E7EB;
      display: flex;
      align-items: center;
      justify-content: center;
      transition: all 0.3s ease;
      
      .step-number {
        font-size: 24rpx;
        color: #9CA3AF;
        font-weight: 600;
      }
      
      .step-check {
        font-size: 28rpx;
        color: #fff;
      }
    }
    
    .step-label {
      font-size: 22rpx;
      color: #9CA3AF;
    }
    
    &.active {
      .step-dot {
        background: #3B82F6;
        
        .step-number {
          color: #fff;
        }
      }
      
      .step-label {
        color: #3B82F6;
        font-weight: 500;
      }
    }
    
    &.completed {
      .step-dot {
        background: #22C55E;
      }
      
      .step-label {
        color: #22C55E;
      }
    }
  }
}

.dialog-messages {
  flex: 1;
  padding: 24rpx;
  min-height: 400rpx;
  max-height: 500rpx;
}

.message-item {
  display: flex;
  gap: 16rpx;
  margin-bottom: 24rpx;
  
  &.user {
    flex-direction: row-reverse;
    
    .message-bubble {
      background: linear-gradient(135deg, #3B82F6 0%, #60A5FA 100%);
      color: #fff;
    }
  }
  
  &.assistant {
    .message-bubble {
      background: #F5F7FA;
      color: #333;
    }
  }
  
  .message-avatar {
    width: 64rpx;
    height: 64rpx;
    border-radius: 50%;
    background: #F3F4F6;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
    
    .avatar-icon {
      font-size: 32rpx;
    }
  }
  
  .message-bubble {
    max-width: 70%;
    padding: 20rpx 24rpx;
    border-radius: 20rpx;
    word-wrap: break-word;
    
    .message-text {
      font-size: 28rpx;
      line-height: 1.6;
    }
    
    &.loading {
      padding: 16rpx 24rpx;
    }
  }
}

.loading-dots {
  display: flex;
  gap: 8rpx;
  
  .dot {
    width: 12rpx;
    height: 12rpx;
    border-radius: 50%;
    background: #9CA3AF;
    animation: bounce 1.4s infinite ease-in-out;
    
    &:nth-child(1) {
      animation-delay: -0.32s;
    }
    
    &:nth-child(2) {
      animation-delay: -0.16s;
    }
  }
}

.dialog-input-area {
  display: flex;
  align-items: center;
  gap: 16rpx;
  padding: 24rpx 32rpx;
  border-top: 1rpx solid #F3F4F6;
  background: #fff;
  
  .input-field {
    flex: 1;
    height: 72rpx;
    background: #F5F7FA;
    border-radius: 36rpx;
    padding: 0 24rpx;
    font-size: 28rpx;
    color: #333;
  }
  
  .send-btn {
    padding: 0 32rpx;
    height: 72rpx;
    background: linear-gradient(135deg, #3B82F6 0%, #60A5FA 100%);
    border-radius: 36rpx;
    display: flex;
    align-items: center;
    justify-content: center;
    
    &.disabled {
      background: #E5E7EB;
      
      .send-icon {
        color: #9CA3AF;
      }
    }
    
    .send-icon {
      font-size: 28rpx;
      color: #fff;
      font-weight: 500;
    }
  }
}

.dialog-footer {
  padding: 24rpx 32rpx;
  border-top: 1rpx solid #F3F4F6;
  background: #fff;
  
  .complete-btn {
    width: 100%;
    height: 88rpx;
    background: linear-gradient(135deg, #22C55E 0%, #4ADE80 100%);
    border-radius: 44rpx;
    display: flex;
    align-items: center;
    justify-content: center;
    
    .btn-text {
      font-size: 32rpx;
      color: #fff;
      font-weight: 600;
    }
  }
}

@keyframes scaleIn {
  from {
    opacity: 0;
    transform: scale(0.9);
  }
  to {
    opacity: 1;
    transform: scale(1);
  }
}

@keyframes bounce {
  0%, 80%, 100% {
    transform: scale(0);
  }
  40% {
    transform: scale(1);
  }
}
</style>






