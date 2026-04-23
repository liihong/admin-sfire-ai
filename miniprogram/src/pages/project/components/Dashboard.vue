<template>
  <view class="dashboard-page">
    <!-- 顶部用户信息栏 -->
    <TopBar
      :project-name="activeProject?.name"
      :user-name="userName"
      :user-points="userPoints"
      @switch-project="handleSwitchProject"
    />

    <!-- 主内容区 -->
    <scroll-view class="main-scroll" scroll-y :refresher-enabled="true" :refresher-triggered="refreshing"
      @refresherrefresh="handleRefresh">
      <!-- 当前活跃人设卡片 -->
      <PersonaCard
        :project="activeProject"
        @click="navigateToPersona"
      />

      <!-- 今天拍点啥 - 分类网格 -->
     <BaseSection>今天拍点啥</BaseSection>
     <CategoryGrid :categories="categoryList" @click="handleCategoryClick" />

      <!-- 快捷指令库 -->
     <BaseSection>快捷指令库</BaseSection>
     <QuickCommandGrid :entries="commandList" @click="handleNavigate" />

     <!-- 工具箱 -->
     <BaseSection>工具箱</BaseSection>
     <ToolLibrary :tools="toolList" />

    <!-- 历史对话 -->
      <ConversationHistory ref="conversationHistoryRef" @click="handleConversationClick" />
      <!-- 底部安全区 -->
      <view class="bottom-safe-area"></view>
    </scroll-view>

   <!-- 灵感捕捉悬浮按钮 -->
    <FloatingActionButton @click="showInspirationCard = true" />

    <!-- 灵感捕捉卡片 -->
    <InspirationCard :visible="showInspirationCard" v-model="inspirationText"
      @update:visible="showInspirationCard = $event" @send="handleInspirationSend" @mic-click="handleMicClick" />
  </view>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useProjectStore } from '@/stores/project'
import { useQuickEntryStore } from '@/stores/quickEntry'
import { useAgentStore } from '@/stores/agent'
import { useProject } from '@/composables/useProject'
import { useNavigation } from '@/composables/useNavigation'
import { createInspiration } from '@/api/inspiration'
import TopBar from './dashboard/TopBar.vue'
import PersonaCard from './dashboard/PersonaCard.vue'
import CategoryGrid from './dashboard/CategoryGrid.vue'
import QuickCommandGrid from './dashboard/QuickCommandGrid.vue'
import FloatingActionButton from './FloatingActionButton.vue'
import InspirationCard from '@/components/inspiration/InspirationCard.vue'
import ConversationHistory from './dashboard/ConversationHistory.vue'
import BaseSection from '@/components/base/BaseSection.vue'
import ToolLibrary from './dashboard/ToolLibrary.vue'
import type { Conversation } from '@/api/conversation'

// Emits
const emit = defineEmits<{
  'switch-project': []
}>()

// Store
const projectStore = useProjectStore()
const quickEntryStore = useQuickEntryStore()
const agentStore = useAgentStore()
const activeProject = computed(() => projectStore.activeProject)

// Composables
const { initProject } = useProject({ autoLoad: false })
const { navigateTo } = useNavigation()

// 状态
const refreshing = ref(false)
const conversationHistoryRef = ref<InstanceType<typeof ConversationHistory> | null>(null)
const showInspirationCard = ref(false)
const inspirationText = ref('')
const userName = ref('创作者')
const userPoints = ref(1280)

// 快捷入口数据由 project index 的 watch 触发 loadQuickEntryList，从 store 读取
const categoryList = computed(() => quickEntryStore.categoryList)
const commandList = computed(() => quickEntryStore.commandList)

// 工具箱：只放已存在的页面，避免跳转到未实现页面
const toolList = computed(() => [
  {
    key: 'copywriting-library',
    label: '文案库',
    icon: 'edit',
    color: '#FF6B35',
    type: 'page',
    target: '/pages/copywriting/library/index',
  },
  {
    key: 'text-extract',
    label: '文案提取',
    icon: 'edit',
    color: '#3B82F6',
    type: 'page',
    target: '/pages/tools/text-extract/index',
  },
])

// 初始化
onMounted(async () => {
  // 获取 URL 参数
  const pages = getCurrentPages()
  const currentPage = pages[pages.length - 1] as any
  const urlParams = currentPage?.options || {}
  const editMode = urlParams.edit === 'true'
  const projectId = urlParams.id

  await initProject(projectId).catch(err => {
    console.error('[Dashboard] initProject failed:', err)
  })

  // 编辑模式：进入创建/调研页回填数据，用于微调人设
  if (editMode && projectId) {
    uni.navigateTo({
      url: `/pages/project/create/index?mode=edit&id=${projectId}`
    })
  }
})

// 处理灵感发送
async function handleInspirationSend(text: string, tags: string[]) {
  try {
    await createInspiration({
      content: text,
      tags,
      project_id: activeProject.value?.id ? parseInt(activeProject.value.id) : undefined,
    })
    
    uni.showToast({ title: '灵感已保存', icon: 'success' })
    inspirationText.value = ''
    showInspirationCard.value = false
    
    // 可选：跳转到灵感列表页
    // uni.navigateTo({ url: '/pages/inspiration/index' })
  } catch (error: any) {
    uni.showToast({
      title: error.message || '保存失败',
      icon: 'none',
    })
  }
}

// 处理麦克风点击
function handleMicClick() {
  // 实现语音输入逻辑（功能待实现）
  uni.showToast({ title: '语音功能即将上线', icon: 'none' })
}

/**
 * 微调人设：进入 IP 调研流程页并回填当前项目数据
 */
function navigateToPersona() {
  const id = activeProject.value?.id
  if (id == null || id === '') {
    uni.showToast({ title: '请先选择项目', icon: 'none' })
    return
  }
  uni.navigateTo({
    url: `/pages/project/create/index?mode=edit&id=${String(id)}`
  })
}

// 处理导航
function handleNavigate(route: string) {
  navigateTo(route)
}

/**
 * 处理分类点击事件
 * @param category 分类项数据
 */
function handleCategoryClick(category: {
  key: string
  label: string
  icon: string
  color: string
  id?: number
  action_type?: 'agent' | 'skill' | 'prompt' | 'url'
  action_value?: string
  instructions?: string | null
}) {

  // 规范化 action_type，去除空格并转为小写，便于判断
  const actionType = category.action_type?.trim().toLowerCase()

  // 如果 action_type 为 agent，跳转到 AI 对话页面
  if (actionType === 'agent') {
    if (!category.action_value) {
      uni.showToast({
        title: '智能体ID不能为空',
        icon: 'none'
      })
      return
    }

    // 同步设置当前智能体展示标题（用于对话页标题展示）
    agentStore.setActiveAgent({
      id: String(category.action_value),
      name: category.label,
      label: category.label,
      icon: '',
      description: ''
    })

    // 设置选中的快捷指令到 store（含 instructions，用于 copywriting 页面的默认指令提示语）
    quickEntryStore.setActiveQuickEntry({
      id: category.id ?? 0,
      unique_key: category.key,
      type: 'category',
      title: category.label,
      subtitle: null,
      instructions: category.instructions ?? null,
      icon_class: category.icon,
      bg_color: category.color,
      action_type: 'agent',
      action_value: category.action_value,
      tag: 'none',
      priority: 0,
      status: 1,
      created_at: null,
      updated_at: null
    })

    // 构建跳转参数
    const params: Record<string, string> = {
      agentId: category.action_value
    }

    // 构建查询字符串
    const queryString = Object.entries(params)
      .map(([key, value]) => `${key}=${encodeURIComponent(value)}`)
      .join('&')

    // 跳转到 AI 对话页面
    uni.navigateTo({
      url: `/pages/copywriting/index?${queryString}`,
      fail: () => {
        uni.showToast({
          title: '页面跳转失败',
          icon: 'none'
        })
      }
    })
    return
  }

  // 如果 action_type 为 url，跳转到对应的 URL 页面
  if (actionType === 'url') {
    if (!category.action_value) {
      uni.showToast({
        title: 'URL 地址不能为空',
        icon: 'none'
      })
      return
    }

    // 规范化 URL 路径，转换为小程序标准格式：/pages/xxx/index
    let targetUrl = category.action_value.trim()

    // 如果已经是完整路径（以 /pages 开头），直接使用
    if (targetUrl.startsWith('/pages/')) {
      // 如果路径不以 /index 结尾，且不是文件路径（没有扩展名），自动添加 /index
      if (!targetUrl.endsWith('/index') && !targetUrl.includes('.')) {
        targetUrl = targetUrl + '/index'
      }
    } else {
      // 如果不是完整路径，转换为标准格式
      // 移除开头的 /（如果有）
      if (targetUrl.startsWith('/')) {
        targetUrl = targetUrl.substring(1)
      }

      // 如果路径包含 /，说明是类似 hotspot/index 的格式
      // 否则是单个路径名，如 hotspot
      const pathParts = targetUrl.split('/')
      const pageName = pathParts[0]

      // 构建标准路径：/pages/{pageName}/index
      targetUrl = `/pages/${pageName}/index`
    }

    // 跳转到对应的 URL 页面
    uni.navigateTo({
      url: targetUrl,
      fail: () => {
        uni.showToast({
          title: '页面跳转失败',
          icon: 'none'
        })
      }
    })
    return
  }

  // 其他 action_type 的处理（skill、prompt 等，功能待实现）
  uni.showToast({
    title: `功能开发中：${category.label}`,
    icon: 'none'
  })
}

/**
 * 下拉刷新：重新加载历史对话 + 快捷入口
 */
async function handleRefresh() {
  refreshing.value = true
  try {
    await Promise.all([
      conversationHistoryRef.value?.loadConversations(),
      quickEntryStore.loadQuickEntryList(true) // 强制刷新快捷入口
    ])
  } finally {
    refreshing.value = false
  }
}

// 处理历史对话点击
function handleConversationClick(conversation: Conversation) {
  // 构建跳转参数
  const params: Record<string, string> = {
    conversationId: String(conversation.id),
  }

  // 如果有智能体ID，传递智能体ID
  if (conversation.agent_id) {
    params.agentId = String(conversation.agent_id)
  }

  // 构建查询字符串
  const queryString = Object.entries(params)
    .map(([key, value]) => `${key}=${encodeURIComponent(value)}`)
    .join('&')

  // 跳转到对话详情页面
  uni.navigateTo({
    url: `/pages/copywriting/index?${queryString}`,
    fail: () => {
      uni.showToast({
        title: '页面跳转失败',
        icon: 'none'
      })
    }
  })
}

/**
 * 处理切换项目事件
 */
function handleSwitchProject() {
  emit('switch-project')
}

/**
 * 刷新历史对话（供父组件在 onShow 时调用）
 */
function refreshConversationHistory() {
  conversationHistoryRef.value?.loadConversations()
}

defineExpose({
  refreshConversationHistory,
})
</script>

<style lang="scss" scoped>
@import '@/styles/_variables.scss';
@import '@/styles/_animations.scss';

// ========== 基础样式 ==========
.dashboard-page {
  min-height: 100vh;
  background: linear-gradient(180deg, #FAFBFC 0%, #F5F7FA 100%);
  position: relative;
  top: -15rpx;
  // 优雅的背景装饰
  &::before {
    content: '';
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background:
      radial-gradient(circle at 20% 20%, rgba(255, 149, 0, 0.03) 0%, transparent 50%),
      radial-gradient(circle at 80% 80%, rgba(59, 130, 246, 0.03) 0%, transparent 50%);
    pointer-events: none;
    z-index: 0;
  }
}

// ========== 主滚动区域 ==========
.main-scroll {
  height: calc(100vh - 100rpx);
  padding: 30rpx $spacing-lg $spacing-lg;
  position: relative;
  z-index: 1;
}

// ========== 底部安全区 ==========
.bottom-safe-area {
  height: calc(40rpx + env(safe-area-inset-bottom));
}
</style>
