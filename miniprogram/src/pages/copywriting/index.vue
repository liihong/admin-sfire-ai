<template>
  <view class="chat-page">
    <!-- 顶部导航栏 -->
    <view class="nav-header">
      <!-- iPhone 灵动岛安全区适配 -->
      <!-- 使用动态组件（推荐，微信小程序中更可靠） -->
      <SafeAreaTop />
      <!-- 导航栏内容 -->
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

    <!-- IP 档案卡片 / 无项目提示卡片 -->
    <view class="persona-card-wrapper">
      <AgentCard :project="activeProject" :persona-settings="currentPersonaSettings" />
    </view>

    <!-- 聊天消息区域 -->
    <scroll-view class="chat-container" scroll-y :scroll-top="scrollTop" :scroll-with-animation="true"
      @scrolltoupper="onScrollToUpper">


      <!-- 对话消息列表 -->
      <view v-for="msg in chatHistory" :key="`${msg.role}-${msg.timestamp}`" class="message-wrapper" :class="msg.role">
        <!-- 用户消息 -->
        <view v-if="msg.role === 'user'" class="message-bubble user-bubble">
          <text class="bubble-text">{{ msg.content }}</text>
        </view>

        <!-- AI 消息 -->
        <view v-else-if="msg.role === 'assistant'" class="message-row assistant-row">
          <view class="ai-avatar">
            <SvgIcon name="agent" size="36" color="#fff" />
          </view>
          <view class="message-bubble assistant-bubble">
            <text class="bubble-text">{{ msg.content }}</text>
            <!-- 复制按钮 -->
            <view class="bubble-actions">
              <view class="action-item" @tap="copyMessage(msg.content)">
                <SvgIcon name="edit" size="24" color="#999" />
                <text class="action-label">复制</text>
              </view>
            </view>
          </view>
        </view>

        <!-- 系统提示消息 (智能体切换等) -->
        <view v-else-if="msg.role === 'system_hint'" class="system-hint-wrapper">
          <view class="system-hint-bubble">
            <text class="hint-text">{{ msg.content }}</text>
          </view>
        </view>
      </view>

      <!-- 加载中状态 -->
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

      <!-- 底部占位 -->
      <view class="scroll-bottom-spacer"></view>
    </scroll-view>

    <!-- 底部输入栏 -->
    <view class="input-bar">
      <view class="input-container">
        <!-- 清空对话按钮 -->
        <view class="clear-btn" @tap="clearChat">
          <SvgIcon name="delete" size="36" color="#666" />
        </view>

        <!-- 输入框 -->
        <view class="input-wrapper">
          <textarea v-model="inputText" class="chat-input" :placeholder="inputPlaceholder" :maxlength="2000"
            :auto-height="true" :show-confirm-bar="false" :adjust-position="true" :cursor-spacing="20"
            @confirm="sendMessage" @linechange="onInputLineChange" />
        </view>

        <!-- 发送按钮 -->
        <view class="send-btn" :class="{ active: canSend, disabled: !canSend || isGenerating }" @tap="sendMessage">
          <SvgIcon :name="isGenerating ? 'ready2' : 'send'" size="36"
            :color="canSend && !isGenerating ? '#fff' : '#999'" />
        </view>
      </view>
    </view>

    <!-- AI 生成提示 -->
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
import { chatStream, type ChatResponseData } from '@/api/generate'
import { msgSecCheck } from '@/utils/security'
import SvgIcon from '@/components/base/SvgIcon.vue'
import AgentCard from './components/AgentCard.vue'
import SafeAreaTop from '@/components/common/SafeAreaTop.vue'

// ============== Store ==============
const authStore = useAuthStore()
const projectStore = useProjectStore()
const agentStore = useAgentStore()
const quickEntryStore = useQuickEntryStore()

const activeProject = computed(() => projectStore.activeProject)
const currentPersonaSettings = computed(() => projectStore.currentPersonaSettings)

// ============== 状态定义 ==============
interface ChatMessage {
  role: 'user' | 'assistant' | 'system_card' | 'system_hint'
  content: string
  timestamp: number
}

const chatHistory = reactive<ChatMessage[]>([])
const inputText = ref('')
const isGenerating = ref(false)
const scrollTop = ref(0)
const ipCardMessage = ref<ChatMessage | null>(null)
const conversationId = ref<number | undefined>(undefined)

// ============== 计算属性 ==============
const canSend = computed(() => inputText.value.trim().length > 0)

const inputPlaceholder = computed(() => {
  return '向智能体发送创作指令...'
})

// ============== 方法定义 ==============

/**
 * 返回上一页
 */
function goBack() {
  uni.navigateBack({
    fail: () => {
      uni.switchTab({ url: '/pages/index/index' })
    }
  })
}


/**
 * 初始化 IP 卡片消息 (Task 1)
 */
function initIPCard() {
  if (activeProject.value) {
    ipCardMessage.value = {
      role: 'system_card',
      content: `当前智能体：${agentStore.activeAgent?.name || '未选择'}\n绑定 IP：${activeProject.value?.name || '未选择'}\n准备就绪，请告诉我你想拍什么？`,
      timestamp: Date.now()
    }
  }
}



/**
 * 清空对话 (Task 3)
 * 清除除"IP 卡片"外的所有对话
 */
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
        // 清空聊天历史，但保留 IP 卡片
        chatHistory.splice(0, chatHistory.length)
        // 重置会话ID
        conversationId.value = undefined
        uni.showToast({
          title: '对话已清空',
          icon: 'success'
        })
      }
    }
  })
}

/**
 * 滚动到底部
 */
function scrollToBottom() {
  nextTick(() => {
    // 使用一个很大的数值确保滚动到底部
    scrollTop.value = scrollTop.value === 99999 ? 100000 : 99999
  })
}

/**
 * 滚动到顶部事件（预留：可用于加载历史消息）
 */
function onScrollToUpper() {
  // TODO: 实现历史消息加载功能
}

/**
 * 输入框行数变化
 */
function onInputLineChange() {
  // 输入框高度变化时的处理（当前无需特殊处理）
}

/**
 * 发送消息 (Task 3)
 * 使用流式输出实时更新 AI 回复内容
 */
async function sendMessage() {
  if (!canSend.value || isGenerating.value) return

  // 登录检查
  const loggedIn = await authStore.requireLogin()
  if (!loggedIn) return

  const userMessage = inputText.value.trim()

  // 内容安全检测
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

  // 添加用户消息
  chatHistory.push({
    role: 'user',
    content: userMessage,
    timestamp: Date.now()
  })

  scrollToBottom()
  isGenerating.value = true

  console.log('[copywriting] 开始发送消息，显示加载状态')

  // AI 回复消息占位符，将在收到第一个内容块时创建
  let assistantMessage: ChatMessage | null = null
  let hasReceivedFirstChunk = false
  let receivedContent = '' // 累积接收的内容

  // 用于在回调中访问 assistantMessage
  const messageRef = { current: assistantMessage }

  try {
    // 获取当前激活的项目ID
    const projectId = activeProject.value?.id ? parseInt(activeProject.value.id) : undefined

    // 构建消息列表（只包含 user 和 assistant 消息，排除当前正在生成的消息）
    const messages = chatHistory
      .filter(msg => (msg.role === 'user' || msg.role === 'assistant') && msg !== assistantMessage)
      .map(msg => ({
        role: msg.role,
        content: msg.content
      }))

    // 使用智能体的 ID 作为后端的 agent_type
    const agentType = agentStore.getActiveAgentId

    if (!agentType) {
      throw new Error('智能体ID不能为空')
    }

    // 使用流式聊天接口
    await chatStream(
      {
        agent_type: agentType.toString(),
        conversation_id: conversationId.value,
        messages: messages,
        project_id: projectId,
        stream: true
      },
      {
        // 接收到内容块时，实时更新消息内容
        onChunk: (content: string) => {
          console.log('[sendMessage] 收到内容块:', content, '长度:', content.length, '当前累积长度:', receivedContent.length)

          // 后端返回的是增量内容（delta.content），需要累积
          receivedContent += content
          console.log('[sendMessage] 累积内容，新长度:', receivedContent.length)

          // 如果是第一个内容块，创建消息占位符
          if (!hasReceivedFirstChunk) {
            hasReceivedFirstChunk = true
            assistantMessage = {
              role: 'assistant',
              content: receivedContent,
              timestamp: Date.now()
            }
            chatHistory.push(assistantMessage)
            // 隐藏加载状态，显示实际消息
            isGenerating.value = false
            console.log('[sendMessage] 创建第一条消息，内容:', assistantMessage.content)
          } else if (assistantMessage) {
            // 直接更新整个 content 属性，确保 Vue 响应式生效
            assistantMessage.content = receivedContent
            console.log('[sendMessage] 更新消息内容，总长度:', assistantMessage.content.length)
          }

          // 实时滚动到底部，提供流畅的体验
          nextTick(() => {
            scrollToBottom()
          })
        },
        // 接收到会话ID时保存
        onConversationId: (id: number) => {
          conversationId.value = id
        },
        // 流式响应完成
        onDone: () => {
          console.log('[sendMessage] 流式响应完成')
          // 确保加载状态已隐藏
          isGenerating.value = false
          // 如果没有收到任何内容，创建错误消息
          if (!hasReceivedFirstChunk && !assistantMessage) {
            assistantMessage = {
              role: 'assistant',
              content: '❌ 未收到任何响应内容',
              timestamp: Date.now()
            }
            chatHistory.push(assistantMessage)
          }
          // 确保最终滚动到底部
          scrollToBottom()
        },
        // 发生错误时处理
        onError: (error: string) => {
          console.error('[sendMessage] 发生错误:', error)
          isGenerating.value = false
          // 如果还没有创建消息，创建一个错误消息
          if (!assistantMessage) {
            assistantMessage = {
              role: 'assistant',
              content: `❌ 生成失败：${error}`,
              timestamp: Date.now()
            }
            chatHistory.push(assistantMessage)
          } else {
            assistantMessage.content = `❌ 生成失败：${error}`
          }
          scrollToBottom()
          uni.showToast({
            title: error,
            icon: 'none',
            duration: 2500
          })
        }
      }
    )

  } catch (error) {
    const errorMessage = error instanceof Error ? error.message : '生成失败，请稍后重试'
    console.error('[sendMessage] 捕获异常:', error)

    isGenerating.value = false

    // 如果还没有创建消息，创建一个错误消息
    if (!assistantMessage) {
      assistantMessage = {
        role: 'assistant',
        content: `❌ 生成失败：${errorMessage}`,
        timestamp: Date.now()
      }
      chatHistory.push(assistantMessage)
    } else {
      // assistantMessage 不为 null，可以安全访问 content
      const msg = assistantMessage as ChatMessage
      msg.content = `❌ 生成失败：${errorMessage}`
    }

    scrollToBottom()

    uni.showToast({
      title: errorMessage,
      icon: 'none',
      duration: 2500
    })
  } finally {
    // 确保加载状态已隐藏
    isGenerating.value = false
  }
}

/**
 * 复制消息
 */
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

// ============== 生命周期 ==============
// 页面加载时接收参数
interface PageOptions {
  agentId?: string
  [key: string]: any
}

onLoad(async (options?: PageOptions) => {
  // 加载存储的快捷指令信息
  quickEntryStore.loadActiveQuickEntryFromStorage()

  if (options?.agentId) {
    // 如果 store 中没有激活的智能体，或者 ID 不匹配，尝试从 storage 加载
    if (!agentStore.activeAgent || agentStore.activeAgent.id !== options.agentId) {
      agentStore.loadActiveAgentFromStorage()
      // 如果仍然不匹配，从 API 获取真实的智能体信息
      if (!agentStore.activeAgent || agentStore.activeAgent.id !== options.agentId) {
        await agentStore.setActiveAgentById(options.agentId)
      }
    }
  } else {
    // 如果没有传入 agentId，尝试从 store 读取
    if (!agentStore.activeAgent) {
      agentStore.loadActiveAgentFromStorage()
    }

    // 如果仍然没有，提示错误
    if (!agentStore.activeAgent) {
      uni.showToast({
        title: '缺少智能体ID参数',
        icon: 'none'
      })
      // 延迟返回上一页
      setTimeout(() => {
        goBack()
      }, 1500)
    }
  }
})

// 页面加载时处理URL参数
onLoad((options: any) => {
  // 处理灵感参数
  if (options.inspiration_id || options.content) {
    if (options.content) {
      // 预填充输入框
      inputText.value = decodeURIComponent(options.content)
    }
  }
})

onMounted(async () => {
  // Task 1: 初始化 IP 卡片
  initIPCard()
  // 初始化时滚动到底部
  scrollToBottom()

  // 如果页面加载时已经有快捷指令且输入框为空，则填充 instructions
  if (!inputText.value.trim() && quickEntryStore.activeQuickEntry?.instructions) {
    inputText.value = quickEntryStore.activeQuickEntry.instructions
  }
})

// 监听项目变化，更新 IP 卡片
watch(activeProject, () => {
  initIPCard()
}, { immediate: true })

// 监听快捷指令变化，自动填充到输入框（仅在输入框为空时填充）
watch(
  () => quickEntryStore.activeQuickEntry,
  (newEntry) => {
    // 如果输入框为空且有快捷指令的 instructions，则自动填充
    if (!inputText.value.trim() && newEntry?.instructions) {
      inputText.value = newEntry.instructions
    }
  }
)
</script>

<style lang="scss" scoped>
// ============== 变量定义 ==============
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

// ============== 页面容器 ==============
.chat-page {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background: linear-gradient(165deg, #F8FAFF 0%, #EEF2FF 50%, #FFF5F0 100%);
}

// ============== 顶部导航栏 ==============
.nav-header {
  display: flex;
  flex-direction: column;
  background: rgba(255, 255, 255, 0.9);
  backdrop-filter: blur(20px);
  border-bottom: 1rpx solid $border-light;
  position: relative;
  z-index: 100;

  // 导航栏内容区域（横向布局）
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

// ============== PersonaCard 包装容器 ==============
.persona-card-wrapper {
  flex-shrink: 0;
  overflow: visible;
}

// ============== 聊天容器 ==============
.chat-container {
  flex: 1;
  padding: 24rpx;
  overflow: hidden;
}

// ============== 消息气泡 ==============
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

// ============== 系统提示消息 ==============
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

// ============== AI 生成提示 ==============
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

// ============== 底部输入栏 ==============
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

