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
      <PersonaContextBar
        :label="personaContextLabel"
        show-new-session
        @new-session="startNewSession"
        @setup="openPersonaSetup"
      />
    </view>

    <scroll-view class="chat-container" scroll-y :scroll-into-view="scrollIntoView" :scroll-with-animation="true"
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
            <image class="ai-avatar-img" :src="assistantAvatarUrl" mode="aspectFill" />
          </view>
          <view class="message-bubble assistant-bubble">
            <text class="bubble-text">{{ msg.content }}</text>
            <view v-if="shouldShowAssistantCopy(msg, idx)" class="bubble-actions">
              <view class="action-item" @tap="copyMessage(msg.content)">
                <SvgIcon name="edit" size="24" color="#999" />
                <text class="action-label">复制文案话术</text>
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
            <image class="ai-avatar-img" :src="assistantAvatarUrl" mode="aspectFill" />
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
            <image class="ai-avatar-img" :src="assistantAvatarUrl" mode="aspectFill" />
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

      <view id="scroll-bottom-anchor" class="scroll-bottom-spacer"></view>
    </scroll-view>

    <view class="bottom-bar" :style="{ bottom: keyboardHeight + 'px' }">
      <view class="input-bar">
        <view class="input-container">
          <view class="input-wrapper">
            <textarea v-model="inputText" class="chat-input" :placeholder="inputPlaceholder" :maxlength="2000"
              :auto-height="true" :show-confirm-bar="false" :adjust-position="false" :cursor-spacing="20"
              @confirm="handleTextareaConfirm" @linechange="onInputLineChange" />
          </view>

          <view class="send-btn" :class="{ active: canSend, disabled: !canSend || isGenerating }" @tap="handleSendTap">
            <view v-if="isGenerating" class="send-btn-spinner"></view>
            <SvgIcon v-else name="send" size="36"
              :color="canSend ? '#fff' : '#999'" />
          </view>
        </view>
      </view>

      <view class="ai-disclaimer">
        <text class="disclaimer-text">本内容由 AI 生成，不代表开发者立场。</text>
      </view>
    </view>

    <PersonaProfileModal
      v-model:visible="showPersonaModal"
      :default-name="authStore.userInfo?.nickname"
      @saved="onPersonaSaved"
    />
  </view>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, onUnmounted, nextTick } from 'vue'
import { onLoad, onShow } from '@dcloudio/uni-app'
import { useAuthStore } from '@/stores/auth'
import { useAgentStore } from '@/stores/agent'
import { useProjectStore } from '@/stores/project'
import { fetchProjects } from '@/api/project'
import { chatStream } from '@/api/generate'
import { msgSecCheck } from '@/utils/security'
import { getConversationDetail, getConversationList } from '@/api/conversation'
import { buildPersonaContextLabel, resolveChatProjectId } from '@/utils/persona'
import SvgIcon from '@/components/base/SvgIcon.vue'
import SafeAreaTop from '@/components/common/SafeAreaTop.vue'
import PersonaContextBar from '@/components/chat/PersonaContextBar.vue'
import PersonaProfileModal from '@/components/mine/PersonaProfileModal.vue'
import { DINGMA_AGENT_DEFAULT_AVATAR_URL } from '@/constants/tenant'

const assistantAvatarUrl = DINGMA_AGENT_DEFAULT_AVATAR_URL

const authStore = useAuthStore()
const agentStore = useAgentStore()
const projectStore = useProjectStore()

interface ChatMessage {
  role: 'user' | 'assistant' | 'system_hint' | 'membership_hint'
  content: string
  timestamp: number
  /** 为 true 时不展示复制（如首条欢迎语） */
  hideCopy?: boolean
}

const chatHistory = reactive<ChatMessage[]>([])
const inputText = ref('')
const isGenerating = ref(false)
const scrollIntoView = ref('')
const conversationId = ref<number | undefined>(undefined)
const isFromConversationHistory = ref(false)
const keyboardHeight = ref(0)
const showPersonaModal = ref(false)

const personaContextLabel = computed(() => buildPersonaContextLabel(projectStore.activeProject))
/** 防止 @tap 和 @confirm 同时触发导致重复发送 */
let isSendingLock = false

const canSend = computed(() => inputText.value.trim().length > 0)

const userAvatarUrl = computed(() => {
  const info = authStore.userInfo
  return info?.avatar || info?.avatarUrl || '/static/default-avatar.png'
})

const inputPlaceholder = computed(() => {
  return '向智能体发送消息...'
})

/** 欢迎语或未序列化到端的 hideCopy 时仍隐藏复制（小程序等对 v-for 项自定义字段绑定可能不完整） */
function shouldShowAssistantCopy(msg: ChatMessage, index: number): boolean {
  if (msg.role !== 'assistant') return true
  if (msg.hideCopy === true) return false
  const welcome = agentStore.activeAgent?.welcomeMessage?.trim()
  if (!welcome) return true
  const firstAssistantIdx = chatHistory.findIndex((m) => m.role === 'assistant')
  if (firstAssistantIdx !== index) return true
  return msg.content.trim() !== welcome
}

function goBack() {
  uni.navigateBack({
    fail: () => {
      uni.switchTab({ url: '/pages/home/index' })
    }
  })
}

function goToMembership() {
  uni.navigateTo({
    url: '/pages/mine/membership/index'
  })
}

async function loadPersonaProject() {
  try {
    const res = await fetchProjects()
    projectStore.setProjectList(res.projects, res.active_project_id)
  } catch (e) {
    console.error('加载人设项目失败:', e)
  }
}

function openPersonaSetup() {
  showPersonaModal.value = true
}

function onPersonaSaved() {
  loadPersonaProject()
}

function startNewSession() {
  if (chatHistory.length === 0 && !conversationId.value) {
    uni.showToast({ title: '已是新会话', icon: 'none' })
    return
  }
  uni.showModal({
    title: '新开会话',
    content: '确定开启新会话吗？当前对话记录将被清空，IP 人设关联保持不变。',
    success: (res) => {
      if (!res.confirm) return
      chatHistory.splice(0, chatHistory.length)
      conversationId.value = undefined
      appendWelcomeBubbleIfEmpty()
      uni.showToast({ title: '已开启新会话', icon: 'success' })
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
  const scroll = () => {
    scrollIntoView.value = ''
    nextTick(() => {
      scrollIntoView.value = 'scroll-bottom-anchor'
    })
  }
  scroll()
  // 历史消息异步渲染后再次滚动，确保到达底部
  nextTick(() => {
    nextTick(scroll)
  })
  setTimeout(scroll, 120)
}

function onScrollToUpper() {
  // 加载历史消息（功能待实现）
}

function onInputLineChange() {
  // 输入框高度变化时的处理
}

function handleSendTap() {
  if (isGenerating.value || !canSend.value) return
  sendMessage()
}

function handleTextareaConfirm() {
  if (isGenerating.value || !canSend.value) return
  sendMessage()
}

async function sendMessage() {
  if (!canSend.value || isGenerating.value) return
  if (isSendingLock) return
  isSendingLock = true
  try {
    const loggedIn = await authStore.requireLogin()
  if (!loggedIn) return

  // 前端判断：非会员直接返回 AI 气泡提示，不请求后端
  const levelCode = authStore.userInfo?.level_code
  if (levelCode === 'normal' || !levelCode) {
    const userMessage = inputText.value.trim()
    inputText.value = ''
    chatHistory.push({
      role: 'user',
      content: userMessage,
      timestamp: Date.now()
    })
    chatHistory.push({
      role: 'membership_hint',
      content: '您还不是会员。请点击下方按钮进入会员权益页查看说明并开通，开通后即可继续使用。',
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

    const projectId = resolveChatProjectId(projectStore.activeProject)

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
  } finally {
    isSendingLock = false
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

function appendWelcomeBubbleIfEmpty() {
  if (chatHistory.length > 0) return
  const welcome = agentStore.activeAgent?.welcomeMessage?.trim()
  if (!welcome) return
  chatHistory.push({
    role: 'assistant',
    content: welcome,
    timestamp: Date.now(),
    hideCopy: true,
  })
  nextTick(() => scrollToBottom())
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
    } else {
      scrollToBottom()
    }
    appendWelcomeBubbleIfEmpty()
    return true
  } catch (error) {
    console.error('加载历史对话失败:', error)
    uni.showToast({
      title: error instanceof Error ? error.message : '加载对话失败',
      icon: 'none',
      duration: 2000
    })
    return false
  }
}

/** 加载当前智能体最近一次对话（首页进入时默认恢复上下文） */
async function loadLatestConversationForAgent(agentId: string): Promise<boolean> {
  const agentIdNum = parseInt(agentId, 10)
  if (Number.isNaN(agentIdNum)) return false
  if (!authStore.hasToken) return false

  try {
    const projectId = resolveChatProjectId(projectStore.activeProject)
    const response = await getConversationList({
      pageNum: 1,
      pageSize: 1,
      status: 'active',
      agent_id: agentIdNum,
      ...(projectId ? { project_id: projectId } : {}),
    })

    const latest = response.data?.list?.[0]
    if (!latest?.id) return false

    return await loadConversationHistory(latest.id)
  } catch (error) {
    console.error('加载最近对话失败:', error)
    return false
  }
}

onLoad(async (options?: PageOptions) => {
  await loadPersonaProject()

  if (options?.conversationId) {
    const convId = parseInt(options.conversationId)
    if (!isNaN(convId)) {
      isFromConversationHistory.value = true
      await loadConversationHistory(convId)
      return
    }
  }

  if (options?.agentId) {
    let labelFromUrl = ''
    if (options.label) {
      try {
        labelFromUrl = decodeURIComponent(String(options.label))
      } catch {
        labelFromUrl = String(options.label)
      }
    }
    await agentStore.setActiveAgentById(String(options.agentId))
    if (labelFromUrl && agentStore.activeAgent) {
      const cur = agentStore.activeAgent
      agentStore.setActiveAgent({ ...cur, label: labelFromUrl }, { persist: true })
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
    } else if (agentStore.getActiveAgentId) {
      await agentStore.setActiveAgentById(agentStore.getActiveAgentId)
    }
  }

  const agentIdForHistory = options?.agentId || agentStore.getActiveAgentId
  if (agentIdForHistory) {
    const loaded = await loadLatestConversationForAgent(String(agentIdForHistory))
    if (loaded) return
  }

  if (options?.content) {
    inputText.value = decodeURIComponent(options.content)
  }

  appendWelcomeBubbleIfEmpty()
})

onShow(() => {
  loadPersonaProject()
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
@import '@/styles/_variables.scss';

.chat-page {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background: $bg-base;
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
  padding-top: 280rpx; /* 固定头部占位：安全区 + nav-content + 人设条 */
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
      overflow: hidden;
      margin-right: 16rpx;
      flex-shrink: 0;
      box-shadow: 0 4rpx 12rpx rgba(0, 0, 0, 0.1);
      background: #fff;

      .ai-avatar-img {
        width: 100%;
        height: 100%;
        display: block;
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
  background-color: $bubble-user-bg;
  color: $bubble-user-text;
  border: 1rpx solid rgba(217, 75, 54, 0.15);
  border-bottom-right-radius: 8rpx;
  max-width: 85%;
  box-shadow: $shadow-premium;
}

.assistant-bubble {
  background: $bg-card;
  color: $text-primary;
  border: 1rpx solid rgba(44, 30, 26, 0.04);
  border-bottom-left-radius: 8rpx;
  box-shadow: $shadow-premium;

  &.membership-hint-bubble {
    .membership-link {
      margin-top: 16rpx;
      padding-top: 12rpx;
      border-top: 1rpx solid $border-light;

      .link-text {
        font-size: 28rpx;
        color: $accent-gold;
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
      padding: 8rpx 24rpx;
      background: $white;
      border: 1rpx solid rgba(217, 75, 54, 0.2);
      border-radius: 28rpx;

      .action-label {
        font-size: 22rpx;
        color: $accent-gold;
        font-weight: 700;
      }

      &:active {
        background: $accent-gold-light;
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
      background: $accent-gold;
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

@keyframes spin {
  to { transform: rotate(360deg); }
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
  background: $bg-base;
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
  background: $bg-card;
  backdrop-filter: blur(20px);
  padding: 20rpx 40rpx 28rpx;
  border-top: 1rpx solid rgba(44, 30, 26, 0.02);
  box-shadow: 0 -2rpx 16rpx rgba(44, 30, 26, 0.03);

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
    background: #f4f2ee;
    border-radius: 40rpx;
    padding: 10rpx 28rpx;
    border: 1rpx solid rgba(44, 30, 26, 0.04);
    transition: all 0.3s ease;

    &:focus-within {
      background: $white;
      border-color: rgba(217, 75, 54, 0.25);
      box-shadow: 0 0 0 4rpx rgba(217, 75, 54, 0.06);
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
      background: linear-gradient(135deg, $accent-gold 0%, $accent-gold-deep 100%);
      box-shadow: 0 4rpx 16rpx rgba(255, 107, 53, 0.35);
    }

    &.disabled {
      opacity: 0.6;
      pointer-events: none;
    }

    .send-btn-spinner {
      width: 40rpx;
      height: 40rpx;
      border: 4rpx solid rgba(255, 255, 255, 0.3);
      border-top-color: #fff;
      border-radius: 50%;
      animation: spin 0.8s linear infinite;
    }

    &:active:not(.disabled) {
      transform: scale(0.95);
    }
  }
}
</style>
