<template>
  <view class="dashboard-page">
    <!-- 顶部用户信息栏 -->
    <TopBar
      :project-name="activeProject?.name"
      :user-name="userName"
      :user-points="userPoints"
    />

    <!-- 主内容区 -->
    <scroll-view class="main-scroll" scroll-y>
      <!-- 当前活跃人设卡片 -->
      <PersonaCard
:project="activeProject"
        @click="showPersonaDrawer = true"
      />

      <!-- 今天拍点啥 - 分类网格 -->
      <BaseSection accent>今天拍点啥</BaseSection>
      <CategoryGrid @click="handleCategoryClick" />

      <!-- 快捷指令库 -->
      <BaseSection accent>快捷指令库</BaseSection>
      <QuickCommandGrid @click="handleNavigate" />

    <!-- 工具库 -->
      <BaseSection accent>工具库</BaseSection>
      <ToolLibrary @click="handleToolClick" />
      <!-- 底部安全区 -->
      <view class="bottom-safe-area"></view>
    </scroll-view>

    <!-- 人设编辑抽屉 -->
    <PersonaDrawer
      :visible="showPersonaDrawer"
      :project="activeProject"
      @update:visible="showPersonaDrawer = $event"
      @saved="handlePersonaSaved"
    />
   <!-- 灵感捕捉悬浮按钮 -->
    <FloatingActionButton @click="showInspirationCard = true" />

    <!-- 灵感捕捉卡片 -->
    <InspirationCard :visible="showInspirationCard" v-model="inspirationText"
      @update:visible="showInspirationCard = $event" @send="handleInspirationSend" @mic-click="handleMicClick" />
  </view>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useProjectStore, DEFAULT_PERSONA_SETTINGS } from '@/stores/project'
import { useProject } from '@/composables/useProject'
import { useNavigation } from '@/composables/useNavigation'
import { createInspiration } from '@/api/inspiration'
import TopBar from './TopBar.vue'
import PersonaCard from './PersonaCard.vue'
import CategoryGrid from './CategoryGrid.vue'
import QuickCommandGrid from './QuickCommandGrid.vue'
import PersonaDrawer from './PersonaDrawer.vue'
import FloatingActionButton from './FloatingActionButton.vue'
import InspirationCard from './InspirationCard.vue'
import ToolLibrary from './ToolLibrary.vue'
import BaseSection from '@/components/base/BaseSection.vue'

// Store
const projectStore = useProjectStore()
const activeProject = computed(() => projectStore.activeProject)

// Composables
const { initProject } = useProject({ autoLoad: false })
const { navigateTo, handleCategoryClick } = useNavigation()

// 状态
const showPersonaDrawer = ref(false)
const showInspirationCard = ref(false)
const inspirationText = ref('')
const userName = ref('创作者')
const userPoints = ref(1280)

// 初始化
onMounted(async () => {
  // 获取 URL 参数
  const pages = getCurrentPages()
  const currentPage = pages[pages.length - 1] as any
  const urlParams = currentPage?.options || {}
  const editMode = urlParams.edit === 'true'
  const projectId = urlParams.id

  // 初始化项目
  await initProject(projectId)

  // 如果是编辑模式，打开抽屉
  if (editMode) {
    showPersonaDrawer.value = true
  }
})

// 处理灵感发送
async function handleInspirationSend(text: string, tags: string[]) {
  try {
    await createInspiration({
      content: text,
      tags,
      project_id: activeProject.value?.id,
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
  console.log('点击麦克风')
  // TODO: 实现语音输入逻辑
  uni.showToast({ title: '语音功能即将上线', icon: 'none' })
}

// 处理人设保存
function handlePersonaSaved() {
  // 人设保存后的回调
  console.log('人设已保存')
}

// 处理导航
function handleNavigate(route: string) {
  navigateTo(route)
}

// 处理工具点击
function handleToolClick(tool: any) {
  console.log('点击工具:', tool)
  // ToolLibrary 组件内部已经处理了跳转逻辑
}
</script>

<style lang="scss" scoped>
@import '@/styles/_variables.scss';
@import '@/styles/_animations.scss';

// ========== 基础样式 ==========
.dashboard-page {
  min-height: 100vh;
  background: linear-gradient(180deg, #FAFBFC 0%, #F5F7FA 100%);
  position: relative;
  
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
