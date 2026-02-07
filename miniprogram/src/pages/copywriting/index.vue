<template>
  <view class="chat-page">
    <view class="nav-header">
      <SafeAreaTop />
      <view class="nav-content">
        <view class="nav-left" @tap="goBack">
          <text class="back-icon">‹</text>
        </view>
        <view class="nav-center">
          <text class="nav-title">{{ agentStore.activeAgent?.name || '智能体' }}</text>
          <view class="agent-tag">
            <text class="tag-dot"></text>
            <text class="tag-text">AI 创作助手</text>
          </view>
        </view>
      </view>
    </view>

    <view class="persona-card-wrapper">
      <AgentCard :project="activeProject" :persona-settings="currentPersonaSettings" />
    </view>

    <scroll-view class="chat-container" scroll-y :scroll-top="scrollTop" :scroll-with-animation="true"
      @scrolltoupper="onScrollToUpper">

      <view v-for="msg in chatHistory" :key="`${msg.role}-${msg.timestamp}`" class="message-wrapper" :class="msg.role">
        <view v-if="msg.role === 'user'" class="message-bubble user-bubble">
          <text class="bubble-text">{{ msg.content }}</text>
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

    <view class="input-bar">
      <view class="input-container">
        <view class="clear-btn" @tap="clearChat">
          <SvgIcon name="delete" size="36" color="#666" />
        </view>

        <view class="input-wrapper">
          <textarea v-model="inputText" class="chat-input" :placeholder="inputPlaceholder" :maxlength="2000"
            :auto-height="true" :show-confirm-bar="false" :adjust-position="true" :cursor-spacing="20"
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
</template>

<script setup lang="ts">
import { ref, reactive, computed, watch, onMounted, nextTick } from 'vue'
import { onLoad } from '@dcloudio/uni-app'
import { useAuthStore } from '@/stores/auth'
import { useProjectStore } from '@/stores/project'
import { useAgentStore } from '@/stores/agent'
import { useQuickEntryStore } from '@/stores/quickEntry'
import { chatStream } from '@/api/generate'
import { msgSecCheck } from '@/utils/security'
import { getConversationDetail } from '@/api/conversation'
import SvgIcon from '@/components/base/SvgIcon.vue'
import AgentCard from './components/AgentCard.vue'
import SafeAreaTop from '@/components/common/SafeAreaTop.vue'

const authStore = useAuthStore()
const projectStore = useProjectStore()
const agentStore = useAgentStore()
const quickEntryStore = useQuickEntryStore()

// 添加防御性检查，确保数据安全
const activeProject = computed(() => {
  const project = projectStore.activeProject
  if (!project) return null
  // 确保关键字段存在且类型正确
  return {
    ...project,
    name: project.name && typeof project.name === 'string' ? project.name : '',
    avatar_color: project.avatar_color && typeof project.avatar_color === 'string' ? project.avatar_color : '#667eea',
    avatar_letter: project.avatar_letter && typeof project.avatar_letter === 'string' ? project.avatar_letter : ''
  }
})

const currentPersonaSettings = computed(() => {
  const settings = projectStore.currentPersonaSettings
  if (!settings) return {}
  // 确保设置对象安全
  return {
    tone: settings.tone && typeof settings.tone === 'string' ? settings.tone : undefined,
    target_audience: settings.target_audience && typeof settings.target_audience === 'string' ? settings.target_audience : undefined
  }
})

interface ChatMessage {
  role: 'user' | 'assistant' | 'system_hint'
  content: string
  timestamp: number
}

const chatHistory = reactive<ChatMessage[]>([])
const inputText = ref('')
const isGenerating = ref(false)
const scrollTop = ref(0)
const conversationId = ref<number | undefined>(undefined)
// 标记是否是从历史对话跳转的（从历史对话跳转时不需要设置默认指令）
const isFromConversationHistory = ref(false)
// 滚动计数器，用于触发滚动到底部
let scrollCounter = 0

const canSend = computed(() => inputText.value.trim().length > 0)

const inputPlaceholder = computed(() => {
  return '向智能体发送创作指令...'
})

function goBack() {
  uni.navigateBack({
    fail: () => {
      uni.switchTab({ url: '/pages/index/index' })
    }
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
    content: '确定要清空当前对话记录吗？IP 档案卡片将保留。',
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
    // 使用递增计数器，确保每次调用都有不同的值，避免触发无限循环
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
    const projectId = activeProject.value?.id ? parseInt(activeProject.value.id) : undefined

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
        project_id: projectId,
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

          // 查找 chatHistory 中最后一条 assistant 消息（如果存在）
          const errorContent = `❌ 生成失败：${error}`
          let lastAssistantIndex = -1
          for (let i = chatHistory.length - 1; i >= 0; i--) {
            if (chatHistory[i].role === 'assistant') {
              lastAssistantIndex = i
              break
            }
          }

          if (lastAssistantIndex >= 0) {
            // 更新现有的 assistant 消息 - 使用 splice 确保 Vue 响应式更新
            const existingMessage = chatHistory[lastAssistantIndex]
            const updatedMessage: ChatMessage = {
              ...existingMessage,
              content: errorContent
            }
            chatHistory.splice(lastAssistantIndex, 1, updatedMessage)
            // 同步更新局部变量引用（如果存在）
            if (assistantMessage) {
              assistantMessage.content = errorContent
            }
          } else {
            // 创建新的错误消息
            const newMessage: ChatMessage = {
              role: 'assistant',
              content: errorContent,
              timestamp: Date.now()
            }
            chatHistory.push(newMessage)
            assistantMessage = newMessage
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
  content?: string
  inspiration_id?: string
  conversationId?: string
  [key: string]: any
}

/**
 * 加载历史对话
 */
async function loadConversationHistory(convId: number) {
  try {
    const detail = await getConversationDetail(convId)

    // 设置会话ID
    conversationId.value = detail.id

    // 根据对话的 agent_id 设置智能体
    if (detail.agent_id) {
      await agentStore.setActiveAgentById(String(detail.agent_id))
    }

    // 将历史消息加载到 chatHistory
    if (detail.messages && detail.messages.length > 0) {
      // 清空现有消息
      chatHistory.splice(0, chatHistory.length)

      // 转换消息格式
      detail.messages.forEach((msg) => {
        // 只加载 user 和 assistant 角色的消息
        if (msg.role === 'user' || msg.role === 'assistant') {
          chatHistory.push({
            role: msg.role as 'user' | 'assistant',
            content: msg.content,
            timestamp: new Date(msg.created_at).getTime(),
          })
        }
      })

      // 滚动到底部
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
  quickEntryStore.loadActiveQuickEntryFromStorage()

  // 如果提供了 conversationId，优先加载历史对话
  if (options?.conversationId) {
    const convId = parseInt(options.conversationId)
    if (!isNaN(convId)) {
      // 标记为从历史对话跳转，不设置默认指令
      isFromConversationHistory.value = true
      await loadConversationHistory(convId)
      return // 历史对话加载完成后直接返回，不再处理 agentId
    }
  }

  // 如果没有 conversationId，按原有逻辑处理 agentId
  if (options?.agentId) {
    // 如果当前 activeAgent 的 ID 不匹配，需要重新设置
    if (!agentStore.activeAgent || agentStore.activeAgent.id !== options.agentId) {
      // 先尝试从 storage 加载
      agentStore.loadActiveAgentFromStorage()
      
      // 如果从 storage 加载后仍然不匹配，需要设置新的 agent
      if (!agentStore.activeAgent || agentStore.activeAgent.id !== options.agentId) {
        // 直接设置一个默认值，避免发起 API 请求
        // 页面可以正常使用，智能体的详细信息会在需要时再加载
        agentStore.setActiveAgent({
          id: options.agentId,
          name: '智能体',
          icon: '',
          description: ''
        })
        // 注意：这里不再调用 setActiveAgentById，避免发起 /api/v1/client/agents 请求
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

onMounted(async () => {
  scrollToBottom()

  // 只有从快捷指令跳转时才设置默认指令，从历史对话跳转时不设置
  if (!isFromConversationHistory.value && !inputText.value.trim() && quickEntryStore.activeQuickEntry?.instructions) {
    inputText.value = quickEntryStore.activeQuickEntry.instructions
  }
})

watch(
  () => quickEntryStore.activeQuickEntry,
  (newEntry) => {
    // 只有从快捷指令跳转时才设置默认指令，从历史对话跳转时不设置
    if (!isFromConversationHistory.value && !inputText.value.trim() && newEntry?.instructions) {
      inputText.value = newEntry.instructions
    }
  }
)

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
  display: flex;
  flex-direction: column;
  background: rgba(255, 255, 255, 0.9);
  backdrop-filter: blur(20px);
  border-bottom: 1rpx solid $border-light;
  position: relative;
  z-index: 100;

  .nav-content {
    display: flex;
    align-items: center;
    justify-content: space-between;
  }

  .nav-left {
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
  0%,
  100% {
    opacity: 1;
    transform: scale(1);
  }

  50% {
    opacity: 0.6;
    transform: scale(0.9);
  }
}

.persona-card-wrapper {
  flex-shrink: 0;
  overflow: visible;
}

.chat-container {
  flex: 1;
  padding: 0 24rpx;
  overflow: hidden;
}

.message-wrapper {
  margin-bottom: 28rpx;

  &.user {
    display: flex;
    justify-content: flex-end;
  }

  &.assistant {
    display: flex;
    justify-content: flex-start;
  }
}

.message-row {
  display: flex;
  align-items: flex-start;
  max-width: 85%;

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

      .ai-avatar-icon {
        font-size: 36rpx;
      }
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

      &:nth-child(1) {
        animation-delay: 0s;
      }

      &:nth-child(2) {
        animation-delay: 0.2s;
      }

      &:nth-child(3) {
        animation-delay: 0.4s;
      }
    }
  }

  .loading-text {
    font-size: 26rpx;
    color: $text-muted;
  }
}

@keyframes typingBounce {
  0%,
  80%,
  100% {
    transform: scale(0.6);
    opacity: 0.5;
  }

  40% {
    transform: scale(1);
    opacity: 1;
  }
}

.scroll-bottom-spacer {
  height: 200rpx;
}

.ai-disclaimer {
  padding: 16rpx 24rpx;
  text-align: center;
  background: rgba(255, 255, 255, 0.95);
  padding-bottom: calc(env(safe-area-inset-bottom));

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
    padding: 20rpx 28rpx;
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