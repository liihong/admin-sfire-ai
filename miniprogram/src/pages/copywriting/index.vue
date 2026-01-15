<template>
  <view class="chat-page">
    <!-- 顶部导航栏 -->
    <view class="nav-header">
      <view class="nav-left" @tap="goBack">
        <text class="back-icon">‹</text>
      </view>
      <view class="nav-center">
        <text class="nav-title">{{ currentAgent?.name || '智能体' }}</text>
        <view class="agent-tag">
          <text class="tag-dot"></text>
          <text class="tag-text">AI 创作助手</text>
        </view>
      </view>
      <!-- <view class="nav-right">
        <view class="model-chip" @tap="showModelPicker">
          <text class="model-icon">{{ currentModel.icon }}</text>
          <text class="model-text">{{ currentModel.name }}</text>
        </view>
      </view> -->
    </view>

    <!-- 聊天消息区域 -->
    <scroll-view 
      class="chat-container"
      scroll-y
      :scroll-top="scrollTop"
      :scroll-with-animation="true"
      @scrolltoupper="onScrollToUpper"
    >
      <!-- IP 档案卡片 (系统消息) -->
      <view class="system-card" v-if="activeProject && ipCardMessage">
        <view class="card-header">
          <view class="card-avatar" :style="{ background: activeProject.avatar_color }">
            <text class="avatar-letter">{{ activeProject.avatar_letter }}</text>
          </view>
          <view class="card-title-group">
            <text class="card-title">{{ activeProject.name }}</text>
            <text class="card-subtitle">IP 档案 · AI 已就位</text>
          </view>
          <view class="card-status">
            <view class="status-pulse"></view>
            <text class="status-text">在线</text>
          </view>
        </view>
        <view class="card-body">
          <view class="info-row">
            <text class="info-label">🤖 当前智能体</text>
            <text class="info-value agent-value">{{ currentAgent?.name || '未选择' }}</text>
          </view>
          <view class="info-row" v-if="activeProject.industry">
            <text class="info-label">🏷️ 行业领域</text>
            <text class="info-value">{{ activeProject.industry }}</text>
          </view>
          <view class="info-row" v-if="currentPersonaSettings.tone">
            <text class="info-label">🎭 风格标签</text>
            <text class="info-value">{{ formatStyleTags(currentPersonaSettings.tone) }}</text>
          </view>
          <view class="info-row" v-if="currentPersonaSettings.target_audience">
            <text class="info-label">👥 目标受众</text>
            <text class="info-value">{{ currentPersonaSettings.target_audience }}</text>
          </view>
        </view>
        <view class="card-footer">
          <text class="footer-hint">🎯 准备就绪，请告诉我你想拍什么？</text>
        </view>
      </view>

      <!-- 无项目提示卡片 -->
      <view class="empty-project-card" v-if="!activeProject">
        <text class="empty-icon">📋</text>
        <text class="empty-title">尚未选择 IP 项目</text>
        <text class="empty-desc">请先创建或选择一个 IP 项目，以便 AI 更好地理解您的创作需求</text>
        <button class="create-btn" @tap="goToProjectList">
          <text>选择项目</text>
        </button>
      </view>

      <!-- 对话消息列表 -->
      <view 
        v-for="(msg, index) in chatHistory" 
        :key="index"
        class="message-wrapper"
        :class="msg.role"
      >
        <!-- 用户消息 -->
        <view v-if="msg.role === 'user'" class="message-bubble user-bubble">
          <text class="bubble-text">{{ msg.content }}</text>
        </view>
        
        <!-- AI 消息 -->
        <view v-else-if="msg.role === 'assistant'" class="message-row assistant-row">
          <view class="ai-avatar">
            <text class="ai-avatar-icon">{{ currentAgent?.icon || '🤖' }}</text>
          </view>
          <view class="message-bubble assistant-bubble">
            <text class="bubble-text">{{ msg.content }}</text>
            <!-- 复制按钮 -->
            <view class="bubble-actions">
              <view class="action-item" @tap="copyMessage(msg.content)">
                <text class="action-icon">📋</text>
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
            <text class="ai-avatar-icon">{{ currentAgent?.icon || '🤖' }}</text>
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

    <!-- 智能体切换悬浮球 -->
    <view class="agent-fab" @tap="showAgentPicker">
      <text class="fab-icon">{{ currentAgent?.icon || '🤖' }}</text>
    </view>

    <!-- 底部输入栏 -->
    <view class="input-bar">
      <view class="input-container">
        <!-- 清空对话按钮 -->
        <view class="clear-btn" @tap="clearChat">
          <text class="clear-icon">🗑️</text>
        </view>
        
        <!-- 输入框 -->
        <view class="input-wrapper">
          <textarea
            v-model="inputText"
            class="chat-input"
            :placeholder="inputPlaceholder"
            :maxlength="2000"
            :auto-height="true"
            :show-confirm-bar="false"
            :adjust-position="true"
            :cursor-spacing="20"
            @confirm="sendMessage"
            @linechange="onInputLineChange"
          />
        </view>
        
        <!-- 发送按钮 -->
        <view 
          class="send-btn"
          :class="{ active: canSend, disabled: !canSend || isGenerating }"
          @tap="sendMessage"
        >
          <text class="send-icon">{{ isGenerating ? '⏳' : '🚀' }}</text>
        </view>
      </view>
    </view>

    <!-- 智能体选择弹窗 -->
    <view class="agent-modal" v-if="showAgentModal" @tap="showAgentModal = false">
      <view class="modal-content" @tap.stop>
        <view class="modal-header">
          <text class="modal-title">选择智能体</text>
          <view class="modal-close" @tap="showAgentModal = false">
            <text>✕</text>
          </view>
        </view>
        <view class="agent-list">
          <view 
            v-for="(agent, idx) in agentList" 
            :key="idx"
            class="agent-item"
            :class="{ active: currentAgent?.id === agent.id }"
            @tap="selectAgent(agent)"
          >
            <view class="agent-icon-wrap">
              <text class="agent-icon">{{ agent.icon }}</text>
            </view>
            <view class="agent-info">
              <text class="agent-name">{{ agent.name }}</text>
              <text class="agent-desc">{{ agent.description }}</text>
            </view>
            <view class="agent-check" v-if="currentAgent?.id === agent.id">
              <text>✓</text>
            </view>
          </view>
        </view>
      </view>
    </view>

    <!-- 模型选择弹窗 -->
    <view class="model-modal" v-if="showModelModal" @tap="showModelModal = false">
      <view class="modal-content" @tap.stop>
        <view class="modal-header">
          <text class="modal-title">切换 AI 模型</text>
          <view class="modal-close" @tap="showModelModal = false">
            <text>✕</text>
          </view>
        </view>
        <view class="model-list">
          <view 
            v-for="(model, idx) in availableModels" 
            :key="idx"
            class="model-item"
            :class="{ active: currentModel.type === model.type }"
            @tap="selectModel(model)"
          >
            <text class="model-item-icon">{{ model.icon }}</text>
            <view class="model-item-info">
              <text class="model-item-name">{{ model.name }}</text>
              <text class="model-item-desc">{{ model.description }}</text>
            </view>
            <view class="model-check" v-if="currentModel.type === model.type">
              <text>✓</text>
            </view>
          </view>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, reactive, computed, watch, onMounted, nextTick } from 'vue'
import { onLoad } from '@dcloudio/uni-app'
import { useSettingsStore, type ModelConfig } from '@/stores/settings'
import { useAuthStore } from '@/stores/auth'
import { useProjectStore } from '@/stores/project'
import { chat, type ChatResponseData } from '@/api/generate'
import { getAgentList } from '@/api/agent'

// ============== Store ==============
const settingsStore = useSettingsStore()
const authStore = useAuthStore()
const projectStore = useProjectStore()

const currentModel = computed(() => settingsStore.currentModel)
const availableModels = computed(() => settingsStore.availableModels)
const activeProject = computed(() => projectStore.activeProject)
const currentPersonaSettings = computed(() => projectStore.currentPersonaSettings)

// ============== 智能体配置 ==============
interface Agent {
  id: string
  type: string  // 智能体类型，用于映射到后端的 agent_type
  name: string
  icon: string
  description: string
  systemPrompt?: string  // 可选，从数据库获取时可能没有
}

const agentList = reactive<Agent[]>([])
const currentAgent = ref<Agent | null>(null)
const pageAgentId = ref<string | null>(null) // 从页面参数获取的智能体ID

// 加载智能体列表
async function loadAgentList() {
  try {
    const response = await getAgentList()
    console.log(response)
    // 后端返回格式: {code: 200, data: {agents: [...]}, msg: "..."}
    if (response.code === 200 && response.data?.agents) {
      // 清空现有列表
      agentList.length = 0
      
      // 将接口返回的数据转换为前端需要的格式
      response.data.agents.forEach((agent) => {
        agentList.push({
          id: agent.id,  // 使用数据库返回的 id
          type: agent.type,  // 使用数据库返回的 type（可能是 id 的字符串形式）
          name: agent.name,
          icon: agent.icon,
          description: agent.description,
          systemPrompt: ''  // 数据库返回的数据中没有 systemPrompt，如果需要可以从其他地方获取
        })
      })
      
      // 如果有传入的 agentId，优先选中该智能体
      if (pageAgentId.value) {
        const targetAgent = agentList.find(agent => agent.id === pageAgentId.value)
        if (targetAgent) {
          currentAgent.value = targetAgent
        } else {
          // 如果找不到对应的智能体，使用第一个
          if (agentList.length > 0) {
            currentAgent.value = agentList[0]
          }
        }
      } else {
        // 设置默认选中的智能体（第一个）
        if (agentList.length > 0 && !currentAgent.value) {
          currentAgent.value = agentList[0]
        }

        // 确保 currentAgent 不为 null
        if (!currentAgent.value && agentList.length > 0) {
          currentAgent.value = agentList[0]
        }
      }
    } else {
      console.error('获取智能体列表失败:', (response as any).msg)
      uni.showToast({
        title: (response as any).msg || '获取智能体列表失败',
        icon: 'none'
      })
    }
  } catch (error: any) {
    console.error('加载智能体列表错误:', error)
    uni.showToast({
      title: error.message || '加载智能体列表失败',
      icon: 'none'
    })
  }
}

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
const showAgentModal = ref(false)
const showModelModal = ref(false)
const ipCardMessage = ref<ChatMessage | null>(null)
const conversationId = ref<number | undefined>(undefined)

// ============== 计算属性 ==============
const canSend = computed(() => inputText.value.trim().length > 0)

const inputPlaceholder = computed(() => {
  return `向${currentAgent.value?.name || '智能体'}发送创作指令...`
})

// ============== API 配置 ==============
const API_BASE_URL = __API_BASE_URL__

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
 * 跳转到项目列表
 */
function goToProjectList() {
  uni.navigateTo({ url: '/pages/project/list' })
}

/**
 * 格式化风格标签
 */
function formatStyleTags(tone: string): string {
  if (!tone) return ''
  // 如果已经是数组格式的字符串，尝试解析
  try {
    const parsed = JSON.parse(tone)
    if (Array.isArray(parsed)) {
      return parsed.join(', ')
    }
  } catch {
    // 不是 JSON，直接返回
  }
  return tone
}

/**
 * 初始化 IP 卡片消息 (Task 1)
 */
function initIPCard() {
  if (activeProject.value) {
    ipCardMessage.value = {
      role: 'system_card',
      content: `🤖 当前智能体：${currentAgent.value?.name || '未选择'}\n👤 绑定 IP：${activeProject.value?.name || '未选择'}\n🏷️ 风格标签：${formatStyleTags(currentPersonaSettings.value?.tone || '默认')}\n🎯 准备就绪，请告诉我你想拍什么？`,
      timestamp: Date.now()
    }
  }
}

/**
 * 显示智能体选择器
 */
function showAgentPicker() {
  showAgentModal.value = true
}

/**
 * 选择智能体 (Task 2)
 */
function selectAgent(agent: Agent) {
  if (currentAgent.value && currentAgent.value.id === agent.id) {
    showAgentModal.value = false
    return
  }

  const previousAgent = currentAgent.value
  currentAgent.value = agent
  showAgentModal.value = false

  // 切换智能体时重置会话ID，因为不同智能体应该有不同的会话
  conversationId.value = undefined

  // 插入系统提示消息，不清除历史记录
  chatHistory.push({
    role: 'system_hint',
    content: `已切换为 [${agent.name}]，接下来的内容将按此风格生成。`,
    timestamp: Date.now()
  })

  // 更新 IP 卡片中的智能体信息
  initIPCard()

  uni.showToast({
    title: `已切换到 ${agent.name}`,
    icon: 'none'
  })

  scrollToBottom()
}

/**
 * 显示模型选择器
 */
function showModelPicker() {
  showModelModal.value = true
}

/**
 * 选择模型
 */
function selectModel(model: ModelConfig) {
  settingsStore.setModelType(model.type)
  showModelModal.value = false
  uni.showToast({
    title: `已切换到 ${model.name}`,
    icon: 'none'
  })
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
 * 滚动到顶部事件
 */
function onScrollToUpper() {
  // 预留：可用于加载历史消息
}

/**
 * 输入框行数变化
 */
function onInputLineChange() {
  // 输入框高度变化时的处理
}

/**
 * 发送消息 (Task 3)
 */
async function sendMessage() {
  if (!canSend.value || isGenerating.value) return

  // 登录检查
  const loggedIn = await authStore.requireLogin()
  if (!loggedIn) return

  const userMessage = inputText.value.trim()
  inputText.value = ''

  // 添加用户消息
  chatHistory.push({
    role: 'user',
    content: userMessage,
    timestamp: Date.now()
  })

  scrollToBottom()
  isGenerating.value = true

  try {
    // 获取当前激活的项目ID
    const projectId = activeProject.value?.id ? parseInt(activeProject.value.id) : undefined

    // 构建消息列表（只包含 user 和 assistant 消息）
    const messages = chatHistory
      .filter(msg => msg.role === 'user' || msg.role === 'assistant')
      .map(msg => ({
        role: msg.role,
        content: msg.content
      }))

    // 使用智能体的 ID 作为后端的 agent_type
    const agentType = currentAgent.value?.id || ''
    
    if (!agentType) {
      throw new Error('请先选择一个智能体')
    }

    // 使用新的 chat 接口
    const response = await chat({
      agent_type: agentType.toString(),
      conversation_id: conversationId.value,
      messages: messages,
      project_id: projectId,
      stream: true
    })

    // 后端返回格式: {code: 200, data: {content: "...", conversation_id: 15, ...}, msg: "..."}
    if (response.code === 200 && response.data) {
      const responseData = response.data as ChatResponseData
      // 保存 conversation_id（如果响应中包含）
      if (responseData.conversation_id) {
        conversationId.value = responseData.conversation_id
      }

      // 添加 AI 回复消息
      if (responseData.content) {
        chatHistory.push({
          role: 'assistant',
          content: responseData.content,
          timestamp: Date.now()
        })
        scrollToBottom()
      } else {
        throw new Error('响应中未包含内容')
      }
    } else {
      throw new Error(response.msg || '生成失败')
    }

  } catch (error: any) {
    console.error('生成失败:', error)
    uni.showToast({
      title: error.message || '生成失败，请稍后重试',
      icon: 'none',
      duration: 2500
    })
    // 添加错误消息
    chatHistory.push({
      role: 'assistant',
      content: `❌ 生成失败：${error.message || '请稍后重试'}`,
      timestamp: Date.now()
    })
    scrollToBottom()
  } finally {
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
onLoad((options: any) => {
  if (options.agentId) {
    pageAgentId.value = options.agentId
  }
})

onMounted(async () => {
  // 加载智能体列表
  await loadAgentList()
  // Task 1: 初始化 IP 卡片
  initIPCard()
  // 初始化时滚动到底部
  scrollToBottom()
})

// 监听项目变化，更新 IP 卡片
watch(activeProject, () => {
  initIPCard()
}, { immediate: true })
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
  align-items: center;
  justify-content: space-between;
  padding: 20rpx 24rpx;
  background: rgba(255, 255, 255, 0.9);
  backdrop-filter: blur(20px);
  border-bottom: 1rpx solid $border-light;
  position: relative;
  z-index: 100;

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

  .nav-right {
    .model-chip {
      display: flex;
      align-items: center;
      gap: 8rpx;
      padding: 12rpx 20rpx;
      background: linear-gradient(135deg, #F0F4FF 0%, #E8EEFF 100%);
      border-radius: 32rpx;
      border: 1rpx solid rgba(79, 172, 254, 0.2);

      .model-icon {
        font-size: 28rpx;
      }

      .model-text {
        font-size: 24rpx;
        color: $accent-blue;
        font-weight: 500;
      }
    }
  }
}

@keyframes pulse {
  0%, 100% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.6; transform: scale(0.9); }
}

// ============== 聊天容器 ==============
.chat-container {
  flex: 1;
  padding: 24rpx;
  overflow: hidden;
}

// ============== IP 档案卡片 ==============
.system-card {
  background: $bg-card;
  border-radius: 28rpx;
  padding: 32rpx;
  margin-bottom: 32rpx;
  border: 2rpx solid transparent;
  background-clip: padding-box;
  position: relative;
  box-shadow: 0 8rpx 32rpx rgba(79, 172, 254, 0.1);

  &::before {
    content: '';
    position: absolute;
    inset: -2rpx;
    border-radius: 30rpx;
    background: linear-gradient(135deg, $accent-blue, $accent-cyan, $primary-orange);
    z-index: -1;
    opacity: 0.6;
  }

  .card-header {
    display: flex;
    align-items: center;
    margin-bottom: 24rpx;
    padding-bottom: 20rpx;
    border-bottom: 1rpx dashed rgba(0, 0, 0, 0.08);

    .card-avatar {
      width: 88rpx;
      height: 88rpx;
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
      box-shadow: 0 4rpx 16rpx rgba(0, 0, 0, 0.15);

      .avatar-letter {
        font-size: 40rpx;
        font-weight: 700;
        color: #fff;
      }
    }

    .card-title-group {
      flex: 1;
      margin-left: 20rpx;

      .card-title {
        font-size: 36rpx;
        font-weight: 700;
        color: $text-primary;
        display: block;
      }

      .card-subtitle {
        font-size: 24rpx;
        color: $text-muted;
        margin-top: 4rpx;
      }
    }

    .card-status {
      display: flex;
      align-items: center;
      gap: 8rpx;
      padding: 8rpx 16rpx;
      background: rgba(76, 175, 80, 0.1);
      border-radius: 20rpx;

      .status-pulse {
        width: 16rpx;
        height: 16rpx;
        border-radius: 50%;
        background: #4CAF50;
        animation: pulse 2s infinite;
      }

      .status-text {
        font-size: 22rpx;
        color: #4CAF50;
        font-weight: 500;
      }
    }
  }

  .card-body {
    .info-row {
      display: flex;
      align-items: center;
      padding: 16rpx 0;

      .info-label {
        font-size: 26rpx;
        color: $text-secondary;
        width: 180rpx;
      }

      .info-value {
        flex: 1;
        font-size: 26rpx;
        color: $text-primary;
        font-weight: 500;

        &.agent-value {
          color: $primary-orange;
        }
      }
    }
  }

  .card-footer {
    margin-top: 20rpx;
    padding-top: 20rpx;
    border-top: 1rpx dashed rgba(0, 0, 0, 0.08);

    .footer-hint {
      font-size: 24rpx;
      color: $text-muted;
      text-align: center;
      display: block;
    }
  }
}

// ============== 空项目卡片 ==============
.empty-project-card {
  background: $bg-card;
  border-radius: 28rpx;
  padding: 60rpx 40rpx;
  margin-bottom: 32rpx;
  text-align: center;
  box-shadow: 0 8rpx 32rpx rgba(0, 0, 0, 0.06);

  .empty-icon {
    font-size: 80rpx;
    display: block;
    margin-bottom: 24rpx;
  }

  .empty-title {
    font-size: 32rpx;
    font-weight: 600;
    color: $text-primary;
    display: block;
    margin-bottom: 16rpx;
  }

  .empty-desc {
    font-size: 26rpx;
    color: $text-muted;
    display: block;
    margin-bottom: 32rpx;
    line-height: 1.6;
  }

  .create-btn {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    padding: 20rpx 48rpx;
    background: linear-gradient(135deg, $primary-orange, $primary-orange-light);
    border-radius: 40rpx;
    border: none;
    color: #fff;
    font-size: 28rpx;
    font-weight: 500;
    box-shadow: 0 8rpx 24rpx rgba(255, 107, 53, 0.3);

    &::after {
      border: none;
    }
  }
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

      .action-icon {
        font-size: 24rpx;
      }

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
  0%, 80%, 100% {
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

// ============== 智能体悬浮球 ==============
.agent-fab {
  position: fixed;
  right: 32rpx;
  bottom: calc(180rpx + env(safe-area-inset-bottom));
  width: 100rpx;
  height: 100rpx;
  border-radius: 50%;
  background: linear-gradient(135deg, #667EEA, #764BA2);
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 8rpx 32rpx rgba(102, 126, 234, 0.4);
  z-index: 99;
  animation: fabFloat 3s ease-in-out infinite;

  .fab-icon {
    font-size: 48rpx;
  }

  &:active {
    transform: scale(0.95);
  }
}

@keyframes fabFloat {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-8rpx); }
}

// ============== 底部输入栏 ==============
.input-bar {
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(20px);
  padding: 20rpx 24rpx;
  padding-bottom: calc(20rpx + env(safe-area-inset-bottom));
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

    .clear-icon {
      font-size: 36rpx;
    }

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

    .send-icon {
      font-size: 36rpx;
    }

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

// ============== 模态框通用样式 ==============
.agent-modal,
.model-modal {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: flex-end;
  justify-content: center;
  z-index: 200;
  animation: fadeIn 0.2s ease;

  .modal-content {
    width: 100%;
    max-height: 80vh;
    background: #fff;
    border-radius: 32rpx 32rpx 0 0;
    animation: slideUp 0.3s ease;
    overflow: hidden;
  }

  .modal-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 32rpx;
    border-bottom: 1rpx solid $border-light;

    .modal-title {
      font-size: 34rpx;
      font-weight: 600;
      color: $text-primary;
    }

    .modal-close {
      width: 56rpx;
      height: 56rpx;
      display: flex;
      align-items: center;
      justify-content: center;
      background: #F5F7FA;
      border-radius: 50%;
      font-size: 28rpx;
      color: $text-muted;
    }
  }
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

@keyframes slideUp {
  from { transform: translateY(100%); }
  to { transform: translateY(0); }
}

// ============== 智能体列表 ==============
.agent-list {
  padding: 16rpx 24rpx;
  max-height: 60vh;
  overflow-y: auto;

  .agent-item {
    display: flex;
    align-items: center;
    padding: 24rpx;
    border-radius: 20rpx;
    margin-bottom: 16rpx;
    background: #F8FAFF;
    border: 2rpx solid transparent;
    transition: all 0.2s ease;

    &.active {
      background: linear-gradient(135deg, rgba(79, 172, 254, 0.1), rgba(0, 242, 254, 0.1));
      border-color: $accent-blue;
    }

    &:active {
      transform: scale(0.98);
    }

    .agent-icon-wrap {
      width: 80rpx;
      height: 80rpx;
      border-radius: 50%;
      background: linear-gradient(135deg, #667EEA, #764BA2);
      display: flex;
      align-items: center;
      justify-content: center;

      .agent-icon {
        font-size: 40rpx;
      }
    }

    .agent-info {
      flex: 1;
      margin-left: 20rpx;

      .agent-name {
        font-size: 30rpx;
        font-weight: 600;
        color: $text-primary;
        display: block;
      }

      .agent-desc {
        font-size: 24rpx;
        color: $text-muted;
        margin-top: 6rpx;
        display: block;
      }
    }

    .agent-check {
      width: 48rpx;
      height: 48rpx;
      border-radius: 50%;
      background: $accent-blue;
      color: #fff;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 28rpx;
      font-weight: 600;
    }
  }
}

// ============== 模型列表 ==============
.model-list {
  padding: 16rpx 24rpx;

  .model-item {
    display: flex;
    align-items: center;
    padding: 28rpx 24rpx;
    border-radius: 20rpx;
    margin-bottom: 16rpx;
    background: #F8FAFF;
    border: 2rpx solid transparent;
    transition: all 0.2s ease;

    &.active {
      background: linear-gradient(135deg, rgba(79, 172, 254, 0.1), rgba(0, 242, 254, 0.1));
      border-color: $accent-blue;
    }

    &:active {
      transform: scale(0.98);
    }

    .model-item-icon {
      font-size: 48rpx;
      margin-right: 20rpx;
    }

    .model-item-info {
      flex: 1;

      .model-item-name {
        font-size: 30rpx;
        font-weight: 600;
        color: $text-primary;
        display: block;
      }

      .model-item-desc {
        font-size: 24rpx;
        color: $text-muted;
        margin-top: 4rpx;
        display: block;
      }
    }

    .model-check {
      width: 48rpx;
      height: 48rpx;
      border-radius: 50%;
      background: $accent-blue;
      color: #fff;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 28rpx;
      font-weight: 600;
    }
  }
}
</style>


