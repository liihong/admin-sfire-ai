<template>
  <view class="chat-page">
    <view class="nav-header">
      <SafeAreaTop />
      <view class="nav-content">
        <view class="nav-left" @tap="goBack">
          <text class="back-icon">‹</text>
        </view>
        <view class="nav-center">
          <text class="nav-title">{{ agentStore.getActiveAgentLabel || '智能体' }}</text>
          <view class="agent-tag">
            <text class="tag-dot"></text>
            <text class="tag-text">AI 对话助手</text>
          </view>
        </view>
      </view>
    </view>

    <scroll-view class="chat-container" scroll-y :scroll-top="scrollTop" :scroll-with-animation="true"
      @scrolltoupper="onScrollToUpper">

      <view v-for="(msg, idx) in chatHistory" :key="idx" class="message-wrapper" :class="msg.role">
        <view v-if="msg.role === 'user'" class="message-row user-row">
          <view class="message-bubble user-bubble">
            <text class="bubble-text">{{ msg.content }}</text>
          </view>
          <view class="user-avatar">
            <image class="avatar-img" :src="userAvatarUrl" mode="aspectFill" />
          </view>
        </view>

        <view v-else-if="msg.role === 'assistant'" class="message-row assistant-row">
          <view class="ai-avatar">
            <SvgIcon name="agent" size="36" color="#fff" />
          </view>
          <view class="message-bubble assistant-bubble">
            <text class="bubble-text">{{ msg.content }}</text>
            <view class="bubble-actions">
              <view class="action-item" @tap="copyMessage(msg.content)">
                <SvgIcon name="edit" size="24" color="#999" />
                <text class="action-label">复制</text>
              </view>
            </view>
          </view>
        </view>

        <view v-else-if="msg.role === 'system_hint'" class="system-hint-wrapper">
          <view class="system-hint-bubble">
            <text class="hint-text">{{ msg.content }}</text>
          </view>
        </view>

        <view v-else-if="msg.role === 'membership_hint'" class="message-row assistant-row">
          <view class="ai-avatar">
            <SvgIcon name="agent" size="36" color="#fff" />
          </view>
          <view class="message-bubble assistant-bubble membership-hint-bubble">
            <text class="bubble-text">{{ msg.content }}</text>
            <view class="membership-link" @tap="goToMembership">
              <text class="link-text">去开通会员</text>
            </view>
          </view>
        </view>
      </view>

      <view v-if="isGenerating" class="message-wrapper assistant">
        <view class="message-row assistant-row">
          <view class="ai-avatar">
            <SvgIcon name="agent" size="36" color="#fff" />
          </view>
          <view class="message-bubble assistant-bubble loading-bubble">
            <view class="typing-indicator">
              <view class="typing-dot"></view>
              <view class="typing-dot"></view>
              <view class="typing-dot"></view>
            </view>
            <text class="loading-text">AI 正在思考...</text>
          </view>
        </view>
      </view>

      <view class="scroll-bottom-spacer"></view>
    </scroll-view>

    <view class="bottom-bar" :style="{ bottom: keyboardHeight + 'px' }">
      <view class="input-bar">
        <view class="input-container">
          <view class="input-wrapper">
            <textarea v-model="inputText" class="chat-input" :placeholder="inputPlaceholder" :maxlength="2000"
              :auto-height="true" :show-confirm-bar="false" :adjust-position="false" :cursor-spacing="20"
              @confirm="sendMessage" @linechange="onInputLineChange" />
          </view>

          <view class="send-btn" :class="{ active: canSend, disabled: !canSend || isGenerating }" @tap="sendMessage">
            <SvgIcon :name="isGenerating ? 'ready2' : 'send'" size="36"
              :color="canSend && !isGenerating ? '#fff' : '#999'" />
          </view>
        </view>
      </view>

      <view class="ai-disclaimer">
        <text class="disclaimer-text">本内容由 AI 生成，不代表开发者立场。</text>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, onUnmounted, nextTick } from 'vue'
import { onLoad } from '@dcloudio/uni-app'
import { useAuthStore } from '@/stores/auth'
import { useAgentStore } from '@/stores/agent'
import { chatStream } from '@/api/generate'
import { msgSecCheck } from '@/utils/security'
import { getConversationDetail } from '@/api/conversation'
import SvgIcon from '@/components/base/SvgIcon.vue'
import SafeAreaTop from '@/components/common/SafeAreaTop.vue'

const authStore = useAuthStore()
const agentStore = useAgentStore()

interface ChatMessage {
  role: 'user' | 'assistant' | 'system_hint' | 'membership_hint'
  content: string
  timestamp: number
}

const chatHistory = reactive<ChatMessage[]>([])
const inputText = ref('')
const isGenerating = ref(false)
const scrollTop = ref(0)
const conversationId = ref<number | undefined>(undefined)
const isFromConversationHistory = ref(false)
const keyboardHeight = ref(0)
let scrollCounter = 0

const canSend = computed(() => inputText.value.trim().length > 0)

const userAvatarUrl = computed(() => {
  const info = authStore.userInfo
  return info?.avatar || info?.avatarUrl || '/static/default-avatar.png'
})

const inputPlaceholder = computed(() => {
  return '向智能体发送消息...'
})

function goBack() {
  uni.navigateBack({
    fail: () => {
      uni.switchTab({ url: '/pages/project/index' })
    }
  })
}

function goToMembership() {
  uni.navigateTo({
    url: '/pages/mine/membership'
  })
}

function clearChat() {
  if (chatHistory.length === 0) {
    uni.showToast({
      title: '暂无对话记录',
      icon: 'none'
    })
    return
  }

  uni.showModal({
    title: '清空对话',
    content: '确定要清空当前对话记录吗？',
    success: (res) => {
      if (res.confirm) {
        chatHistory.splice(0, chatHistory.length)
        conversationId.value = undefined
        uni.showToast({
          title: '对话已清空',
          icon: 'success'
        })
      }
    }
  })
}

function scrollToBottom() {
  nextTick(() => {
    scrollCounter++
    scrollTop.value = scrollCounter
  })
}

function onScrollToUpper() {
  // 加载历史消息（功能待实现）
}

function onInputLineChange() {
  // 输入框高度变化时的处理
}

async function sendMessage() {
  if (!canSend.value || isGenerating.value) return

  const loggedIn = await authStore.requireLogin()
  if (!loggedIn) return

  // 前端判断：非会员直接返回 AI 气泡提示，不请求后端
  const level = authStore.userInfo?.level
  if (level === 'normal' || !level) {
    const userMessage = inputText.value.trim()
    inputText.value = ''
    chatHistory.push({
      role: 'user',
      content: userMessage,
      timestamp: Date.now()
    })
    chatHistory.push({
      role: 'membership_hint',
      content: '您还没有开通会员，请先联系客服开通后再使用',
      timestamp: Date.now()
    })
    scrollToBottom()
    return
  }

  const userMessage = inputText.value.trim()

  const securityCheck = await msgSecCheck(userMessage, {
    showLoading: false
  })

  if (!securityCheck.pass) {
    uni.showToast({
      title: securityCheck.message || '内容包含违规信息，请修改后重试',
      icon: 'none',
      duration: 2500
    })
    return
  }

  inputText.value = ''

  chatHistory.push({
    role: 'user',
    content: userMessage,
    timestamp: Date.now()
  })

  scrollToBottom()
  isGenerating.value = true

  let assistantMessage: ChatMessage | null = null
  let hasReceivedFirstChunk = false
  let receivedContent = ''

  try {
    const messages = chatHistory
      .filter(msg => (msg.role === 'user' || msg.role === 'assistant') && msg !== assistantMessage)
      .map(msg => ({
        role: msg.role,
        content: msg.content
      }))

    const agentType = agentStore.getActiveAgentId

    if (!agentType) {
      throw new Error('智能体ID不能为空')
    }

    await chatStream(
      {
        agent_type: agentType.toString(),
        conversation_id: conversationId.value,
        messages: messages,
        project_id: undefined,
        stream: true
      },
      {
        onChunk: (content: string) => {
          receivedContent += content

          if (!hasReceivedFirstChunk) {
            hasReceivedFirstChunk = true
            assistantMessage = {
              role: 'assistant',
              content: receivedContent,
              timestamp: Date.now()
            }
            chatHistory.push(assistantMessage)
            isGenerating.value = false
          } else if (assistantMessage) {
            assistantMessage.content = receivedContent
          }

          nextTick(() => {
            scrollToBottom()
          })
        },
        onConversationId: (id: number) => {
          conversationId.value = id
        },
        onDone: () => {
          isGenerating.value = false
          if (!hasReceivedFirstChunk && !assistantMessage) {
            assistantMessage = {
              role: 'assistant',
              content: '❌ 未收到任何响应内容',
              timestamp: Date.now()
            }
            chatHistory.push(assistantMessage)
          }
          scrollToBottom()
        },
        onError: (error: string) => {
          isGenerating.value = false

          const errorContent = `❌ 生成失败：${error}`
          let lastAssistantIndex = -1
          for (let i = chatHistory.length - 1; i >= 0; i--) {
            if (chatHistory[i].role === 'assistant') {
              lastAssistantIndex = i
              break
            }
          }

          if (lastAssistantIndex >= 0) {
            const existingMessage = chatHistory[lastAssistantIndex]
            const updatedMessage: ChatMessage = {
              ...existingMessage,
              content: errorContent
            }
            chatHistory.splice(lastAssistantIndex, 1, updatedMessage)
            if (assistantMessage) {
              assistantMessage.content = errorContent
            }
          } else {
            assistantMessage = {
              role: 'assistant',
              content: errorContent,
              timestamp: Date.now()
            }
            chatHistory.push(assistantMessage)
          }

          nextTick(() => {
            scrollToBottom()
          })
        }
      }
    )
  } catch (error) {
    const errorMessage = error instanceof Error ? error.message : '生成失败，请稍后重试'

    isGenerating.value = false

    if (!assistantMessage) {
      assistantMessage = {
        role: 'assistant',
        content: `❌ 生成失败：${errorMessage}`,
        timestamp: Date.now()
      }
      chatHistory.push(assistantMessage)
    } else {
      const msg = assistantMessage as ChatMessage
      msg.content = `❌ 生成失败：${errorMessage}`
    }

    scrollToBottom()
  } finally {
    isGenerating.value = false
  }
}

function copyMessage(content: string) {
  uni.setClipboardData({
    data: content,
    success: () => {
      uni.showToast({
        title: '已复制到剪贴板',
        icon: 'success'
      })
    }
  })
}

interface PageOptions {
  agentId?: string
  label?: string
  content?: string
  conversationId?: string
  [key: string]: any
}

async function loadConversationHistory(convId: number) {
  try {
    const detail = await getConversationDetail(convId)

    conversationId.value = detail.id

    if (detail.agent_id) {
      await agentStore.setActiveAgentById(String(detail.agent_id))
    }

    if (detail.messages && detail.messages.length > 0) {
      chatHistory.splice(0, chatHistory.length)

      detail.messages.forEach((msg) => {
        if (msg.role === 'user' || msg.role === 'assistant') {
          chatHistory.push({
            role: msg.role as 'user' | 'assistant',
            content: msg.content,
            timestamp: new Date(msg.created_at).getTime(),
          })
        }
      })

      nextTick(() => {
        scrollToBottom()
      })
    }
  } catch (error) {
    console.error('加载历史对话失败:', error)
    uni.showToast({
      title: error instanceof Error ? error.message : '加载对话失败',
      icon: 'none',
      duration: 2000
    })
  }
}

onLoad(async (options?: PageOptions) => {
  if (options?.conversationId) {
    const convId = parseInt(options.conversationId)
    if (!isNaN(convId)) {
      isFromConversationHistory.value = true
      await loadConversationHistory(convId)
      return
    }
  }

  if (options?.agentId) {
    if (!agentStore.activeAgent || agentStore.activeAgent.id !== options.agentId) {
      agentStore.loadActiveAgentFromStorage()

      if (!agentStore.activeAgent || agentStore.activeAgent.id !== options.agentId) {
        agentStore.setActiveAgent({
          id: options.agentId,
          name: '智能体',
          label: options.label,
          icon: '',
          description: ''
        }, { persist: false })
      }
    }
  } else {
    if (!agentStore.activeAgent) {
      agentStore.loadActiveAgentFromStorage()
    }
    if (!agentStore.activeAgent) {
      uni.showToast({
        title: '缺少智能体ID参数',
        icon: 'none'
      })
      setTimeout(() => goBack(), 1500)
    }
  }

  if (options?.content) {
    inputText.value = decodeURIComponent(options.content)
  }
})

const onKeyboardHeightChange = (res: { height: number }) => {
  keyboardHeight.value = res.height || 0
}

onMounted(() => {
  scrollToBottom()
  // 监听键盘高度，配合 adjust-position=false 避免整页上推、头部被顶走
  uni.onKeyboardHeightChange(onKeyboardHeightChange)
})

onUnmounted(() => {
  uni.offKeyboardHeightChange(onKeyboardHeightChange)
})
</script>

<style lang="scss" scoped>
$primary-orange: #FF6B35;
$primary-orange-light: #FF8C5A;
$accent-blue: #4FACFE;
$accent-cyan: #00F2FE;
$bg-dark: #1A1A2E;
$bg-card: rgba(255, 255, 255, 0.95);
$text-primary: #1A1A2E;
$text-secondary: #666;
$text-muted: #999;
$border-light: rgba(0, 0, 0, 0.06);

.chat-page {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background: linear-gradient(165deg, #F8FAFF 0%, #EEF2FF 50%, #FFF5F0 100%);
}

.nav-header {
  position: fixed;
    top: 0;
    left: 0;
    right: 0;
  display: flex;
  flex-direction: column;
  background: rgba(255, 255, 255, 0.9);
  backdrop-filter: blur(20px);
  border-bottom: 1rpx solid $border-light;
  z-index: 100;

  .nav-content {
    display: flex;
    align-items: center;
    justify-content: space-between;
  }

  .nav-left {
    position: relative;
    z-index: 10;
    width: 72rpx;
    height: 72rpx;
    display: flex;
    align-items: center;
    justify-content: center;

    .back-icon {
      font-size: 56rpx;
      color: $text-primary;
      font-weight: 300;
    }
  }

  .nav-center {
    flex: 1;
    display: flex;
    flex-direction: column;
    align-items: center;
    margin-left: -80rpx;
    .nav-title {
      font-size: 32rpx;
      font-weight: 600;
      color: $text-primary;
    }

    .agent-tag {
      display: flex;
      align-items: center;
      gap: 8rpx;
      margin-top: 4rpx;

      .tag-dot {
        width: 12rpx;
        height: 12rpx;
        border-radius: 50%;
        background: linear-gradient(135deg, #4CAF50, #8BC34A);
        animation: pulse 2s infinite;
      }

      .tag-text {
        font-size: 22rpx;
        color: $text-muted;
      }
    }
  }
}

@keyframes pulse {
  0%, 100% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.6; transform: scale(0.9); }
}

.chat-container {
  flex: 1;
  padding: 0 24rpx;
  padding-top: 220rpx; /* 固定头部占位：安全区 + nav-content */
  padding-bottom: 200rpx; /* 底部输入栏占位，避免被 fixed 底部栏遮挡 */
  overflow: hidden;
}

.message-wrapper {
  margin-bottom: 28rpx;

  &.user {
    display: flex;
    justify-content: flex-end;
  }

  &.assistant,
  &.membership_hint {
    display: flex;
    justify-content: flex-start;
  }
}

.message-row {
  display: flex;
  align-items: flex-start;
  max-width: 85%;

  &.user-row {
    margin-left: auto;

    .user-avatar {
      width: 72rpx;
      height: 72rpx;
      border-radius: 50%;
      overflow: hidden;
      margin-left: 16rpx;
      flex-shrink: 0;
      background: #E8ECEF;

      .avatar-img {
        width: 100%;
        height: 100%;
      }
    }
  }

  &.assistant-row {
    .ai-avatar {
      width: 72rpx;
      height: 72rpx;
      border-radius: 50%;
      background: linear-gradient(135deg, #667EEA, #764BA2);
      display: flex;
      align-items: center;
      justify-content: center;
      margin-right: 16rpx;
      flex-shrink: 0;
      box-shadow: 0 4rpx 12rpx rgba(102, 126, 234, 0.3);
    }
  }
}

.message-bubble {
  padding: 24rpx 28rpx;
  border-radius: 24rpx;
  position: relative;

  .bubble-text {
    font-size: 28rpx;
    line-height: 1.7;
    white-space: pre-wrap;
    word-break: break-word;
  }
}

.user-bubble {
  background: linear-gradient(135deg, $primary-orange, $primary-orange-light);
  color: #fff;
  border-bottom-right-radius: 8rpx;
  max-width: 85%;
  box-shadow: 0 4rpx 16rpx rgba(255, 107, 53, 0.25);
}

.assistant-bubble {
  background: $bg-card;
  color: $text-primary;
  border-bottom-left-radius: 8rpx;
  box-shadow: 0 4rpx 16rpx rgba(0, 0, 0, 0.06);

  &.membership-hint-bubble {
    .membership-link {
      margin-top: 16rpx;
      padding-top: 12rpx;
      border-top: 1rpx solid $border-light;

      .link-text {
        font-size: 28rpx;
        color: $primary-orange;
        font-weight: 500;
      }

      &:active {
        opacity: 0.8;
      }
    }
  }

  .bubble-actions {
    display: flex;
    justify-content: flex-end;
    margin-top: 16rpx;
    padding-top: 12rpx;
    border-top: 1rpx solid $border-light;

    .action-item {
      display: flex;
      align-items: center;
      gap: 6rpx;
      padding: 8rpx 16rpx;
      background: #F5F7FA;
      border-radius: 16rpx;

      .action-label {
        font-size: 22rpx;
        color: $text-muted;
      }

      &:active {
        background: #E8ECEF;
      }
    }
  }
}

.system-hint-wrapper {
  display: flex;
  justify-content: center;
  margin: 24rpx 0;
}

.system-hint-bubble {
  background: rgba(0, 0, 0, 0.04);
  padding: 12rpx 24rpx;
  border-radius: 20rpx;

  .hint-text {
    font-size: 24rpx;
    color: $text-muted;
  }
}

.loading-bubble {
  display: flex;
  align-items: center;
  gap: 16rpx;
  padding: 28rpx 32rpx;

  .typing-indicator {
    display: flex;
    gap: 8rpx;

    .typing-dot {
      width: 16rpx;
      height: 16rpx;
      border-radius: 50%;
      background: $accent-blue;
      animation: typingBounce 1.4s infinite both;

      &:nth-child(1) { animation-delay: 0s; }
      &:nth-child(2) { animation-delay: 0.2s; }
      &:nth-child(3) { animation-delay: 0.4s; }
    }
  }

  .loading-text {
    font-size: 26rpx;
    color: $text-muted;
  }
}

@keyframes typingBounce {
  0%, 80%, 100% { transform: scale(0.6); opacity: 0.5; }
  40% { transform: scale(1); opacity: 1; }
}

.scroll-bottom-spacer {
  height: 200rpx;
}

.bottom-bar {
  position: fixed;
  left: 0;
  right: 0;
  width: 100%;
  z-index: 99;
  background: linear-gradient(165deg, #F8FAFF 0%, #EEF2FF 50%, #FFF5F0 100%);
  padding-bottom: constant(safe-area-inset-bottom);
  padding-bottom: env(safe-area-inset-bottom);
}

.ai-disclaimer {
  padding: 16rpx 24rpx;
  text-align: center;
  background: rgba(255, 255, 255, 0.95);
  /* 底部安全区由 .bottom-bar 的 padding-bottom 统一处理 */

  .disclaimer-text {
    font-size: 22rpx;
    color: #999;
    line-height: 1.5;
  }
}

.input-bar {
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(20px);
  padding: 20rpx 24rpx;
  border-top: 1rpx solid $border-light;
  box-shadow: 0 -4rpx 24rpx rgba(0, 0, 0, 0.05);

  .input-container {
    display: flex;
    align-items: flex-end;
    gap: 16rpx;
  }

  .clear-btn {
    width: 80rpx;
    height: 80rpx;
    border-radius: 50%;
    background: #F5F7FA;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;

    &:active {
      background: #E8ECEF;
    }
  }

  .input-wrapper {
    flex: 1;
    background: #F5F7FA;
    border-radius: 40rpx;
    padding: 10rpx 28rpx;
    border: 2rpx solid transparent;
    transition: all 0.3s ease;

    &:focus-within {
      background: #fff;
      border-color: $accent-blue;
      box-shadow: 0 0 0 4rpx rgba(79, 172, 254, 0.1);
    }

    .chat-input {
      width: 100%;
      font-size: 28rpx;
      color: $text-primary;
      line-height: 1.5;
      min-height: 40rpx;
      max-height: 200rpx;
    }
  }

  .send-btn {
    width: 80rpx;
    height: 80rpx;
    border-radius: 50%;
    background: #E0E5EC;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
    transition: all 0.3s ease;

    &.active {
      background: linear-gradient(135deg, $primary-orange, $primary-orange-light);
      box-shadow: 0 4rpx 16rpx rgba(255, 107, 53, 0.35);
    }

    &.disabled {
      opacity: 0.6;
      pointer-events: none;
    }

    &:active:not(.disabled) {
      transform: scale(0.95);
    }
  }
}
</style>
