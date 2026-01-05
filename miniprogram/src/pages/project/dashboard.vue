<template>
  <view class="dashboard-page">
    <!-- 背景装饰 -->
    <view class="bg-decoration">
      <view class="deco-circle c1"></view>
      <view class="deco-circle c2"></view>
    </view>

    <!-- 顶部导航栏 -->
    <view class="nav-bar">
      <view class="nav-left">
        <view class="back-btn" @tap="goBack">
          <text class="back-icon">←</text>
        </view>
        <text class="nav-title">操盘控制台</text>
      </view>
      <view class="nav-right">
        <view class="switch-btn" @tap="goToProjectList">
          <text class="switch-icon">🔄</text>
          <text class="switch-text">切换</text>
        </view>
      </view>
    </view>

    <!-- 主内容区 -->
    <scroll-view class="main-scroll" scroll-y>
      <!-- 项目信息卡片 (通栏) -->
      <view class="project-card" @tap="showPersonaDrawer = true">
        <view class="project-card-content">
          <view class="project-info">
            <view class="project-label">当前项目</view>
            <view class="project-name">{{ activeProject?.name || '选择项目' }}</view>
            <view class="project-tags">
              <view class="tag industry-tag" v-if="activeProject?.industry">
                <text class="tag-icon">🎯</text>
                <text class="tag-text">{{ activeProject.industry }}</text>
              </view>
              <view class="tag tone-tag" v-if="activeProject?.persona_settings?.tone">
                <text class="tag-icon">💬</text>
                <text class="tag-text">{{ activeProject.persona_settings.tone }}</text>
              </view>
            </view>
          </view>
          <view class="project-action">
            <view class="action-icon-3d">
              <view class="icon-face front">⚙️</view>
              <view class="icon-face shadow"></view>
            </view>
            <text class="action-hint">编辑人设</text>
          </view>
        </view>
        <view class="project-card-decoration">
          <view class="deco-dot d1"></view>
          <view class="deco-dot d2"></view>
          <view class="deco-dot d3"></view>
        </view>
      </view>

      <!-- Bento Grid 功能区 -->
      <view class="bento-grid">
        <!-- 左侧大卡片：智能文案创作 (跨2行) -->
        <view class="bento-card card-large card-copywriting" @tap="handleNavigate('/pages/copywriting/index')">
          <view class="card-header">
            <view class="card-icon-wrapper gradient-blue">
              <text class="card-icon">📝</text>
            </view>
            <view class="card-badge">核心功能</view>
          </view>
          <view class="card-body">
            <text class="card-title">智能文案创作</text>
            <text class="card-desc">AI 驱动的高质量内容生成，支持多种风格和场景</text>
          </view>
          <view class="card-illustration">
            <view class="illust-line l1"></view>
            <view class="illust-line l2"></view>
            <view class="illust-line l3"></view>
            <view class="illust-cursor"></view>
          </view>
          <view class="card-arrow">
            <text class="arrow-icon">→</text>
          </view>
        </view>

        <!-- 右上小卡片：数字人定制 -->
        <view class="bento-card card-small card-digital" @tap="handleNavigate('')">
          <view class="card-icon-wrapper gradient-purple">
            <text class="card-icon">🧑‍💻</text>
          </view>
          <text class="card-title">数字人定制</text>
          <text class="card-desc">打造专属数字形象</text>
          <view class="card-status">
            <text class="status-dot"></text>
            <text class="status-text">即将上线</text>
          </view>
        </view>

        <!-- 右下小卡片：爆款选题 -->
        <view class="bento-card card-small card-topics" @tap="handleNavigate('')">
          <view class="card-icon-wrapper gradient-orange">
            <text class="card-icon">💡</text>
          </view>
          <text class="card-title">爆款选题</text>
          <text class="card-desc">热点追踪与选题策划</text>
          <view class="card-status">
            <text class="status-dot"></text>
            <text class="status-text">即将上线</text>
          </view>
        </view>

        <!-- 底部通栏卡片：对标账号分析 -->
        <view class="bento-card card-wide card-benchmark" @tap="handleNavigate('')">
          <view class="card-left">
            <view class="card-icon-wrapper gradient-green">
              <text class="card-icon">📊</text>
            </view>
            <view class="card-text">
              <text class="card-title">对标账号分析</text>
              <text class="card-desc">竞品研究与策略优化</text>
            </view>
          </view>
          <view class="card-right">
            <view class="mini-chart">
              <view class="chart-bar" style="height: 40%"></view>
              <view class="chart-bar" style="height: 70%"></view>
              <view class="chart-bar" style="height: 55%"></view>
              <view class="chart-bar" style="height: 85%"></view>
              <view class="chart-bar" style="height: 60%"></view>
            </view>
            <view class="card-status">
              <text class="status-dot"></text>
              <text class="status-text">即将上线</text>
            </view>
          </view>
        </view>

        <!-- 额外功能卡片行 -->
        <view class="bento-card card-half card-hotspot" @tap="handleNavigate('')">
          <view class="card-icon-wrapper gradient-red">
            <text class="card-icon">🔥</text>
          </view>
          <text class="card-title">热点追踪</text>
          <view class="card-status inline">
            <text class="status-text">即将上线</text>
          </view>
        </view>

        <view class="bento-card card-half card-data" @tap="handleNavigate('')">
          <view class="card-icon-wrapper gradient-cyan">
            <text class="card-icon">📈</text>
          </view>
          <text class="card-title">数据看板</text>
          <view class="card-status inline">
            <text class="status-text">即将上线</text>
          </view>
        </view>
      </view>

      <!-- 底部安全区 -->
      <view class="bottom-safe-area"></view>
    </scroll-view>

    <!-- 人设编辑抽屉 -->
    <view class="drawer-overlay" v-if="showPersonaDrawer" @tap="showPersonaDrawer = false">
      <view class="drawer-content" @tap.stop>
        <view class="drawer-handle"></view>
        
        <view class="drawer-header">
          <text class="drawer-title">IP 人设配置</text>
          <view class="drawer-close" @tap="showPersonaDrawer = false">
            <text class="close-icon">×</text>
          </view>
        </view>

        <scroll-view class="drawer-body" scroll-y>
          <!-- 项目基本信息 -->
          <view class="setting-section">
            <text class="section-title">基本信息</text>
            
            <view class="setting-item">
              <text class="item-label">项目名称</text>
              <input 
                class="item-input"
                v-model="editForm.name"
                placeholder="如：李医生科普IP"
              />
            </view>
            
            <view class="setting-item">
              <text class="item-label">所属赛道</text>
              <picker 
                mode="selector" 
                :range="industryOptions" 
                :value="industryOptions.indexOf(editForm.industry)"
                @change="editForm.industry = industryOptions[$event.detail.value]"
              >
                <view class="picker-display">
                  <text class="picker-value">{{ editForm.industry }}</text>
                  <text class="picker-arrow">▼</text>
                </view>
              </picker>
            </view>
          </view>

          <!-- 人设配置 -->
          <view class="setting-section">
            <text class="section-title">人设配置</text>
            
            <view class="setting-item">
              <text class="item-label">语气风格</text>
              <view class="tone-options">
                <view 
                  v-for="tone in toneOptions"
                  :key="tone"
                  class="tone-tag"
                  :class="{ selected: editForm.persona.tone === tone }"
                  @tap="editForm.persona.tone = tone"
                >
                  <text class="tag-text">{{ tone }}</text>
                </view>
              </view>
            </view>
            
            <view class="setting-item">
              <text class="item-label">口头禅</text>
              <input 
                class="item-input"
                v-model="editForm.persona.catchphrase"
                placeholder="如：记得三连支持一下~"
              />
            </view>
            
            <view class="setting-item">
              <text class="item-label">目标受众</text>
              <input 
                class="item-input"
                v-model="editForm.persona.target_audience"
                placeholder="如：25-40岁关注健康的职场人群"
              />
            </view>
            
            <view class="setting-item">
              <text class="item-label">内容风格</text>
              <textarea 
                class="item-textarea"
                v-model="editForm.persona.content_style"
                placeholder="描述你的内容特点和风格..."
                :maxlength="200"
              />
            </view>
            
            <view class="setting-item">
              <text class="item-label">IP 简介</text>
              <textarea 
                class="item-textarea"
                v-model="editForm.persona.introduction"
                placeholder="简单介绍这个IP的定位和特色..."
                :maxlength="300"
              />
            </view>
            
            <view class="setting-item">
              <text class="item-label">常用关键词</text>
              <view class="keywords-wrapper">
                <view 
                  v-for="(keyword, idx) in editForm.persona.keywords" 
                  :key="idx"
                  class="keyword-tag"
                >
                  <text class="keyword-text">{{ keyword }}</text>
                  <text class="keyword-remove" @tap="removeKeyword(idx)">×</text>
                </view>
                <input 
                  class="keyword-input"
                  v-model="newKeyword"
                  placeholder="+ 添加关键词"
                  @confirm="addKeyword"
                />
              </view>
            </view>
            
            <view class="setting-item">
              <text class="item-label">内容禁忌</text>
              <view class="keywords-wrapper">
                <view 
                  v-for="(taboo, idx) in editForm.persona.taboos" 
                  :key="idx"
                  class="keyword-tag taboo-tag"
                >
                  <text class="keyword-text">{{ taboo }}</text>
                  <text class="keyword-remove" @tap="removeTaboo(idx)">×</text>
                </view>
                <input 
                  class="keyword-input"
                  v-model="newTaboo"
                  placeholder="+ 添加禁忌词"
                  @confirm="addTaboo"
                />
              </view>
            </view>
          </view>

          <view class="drawer-spacer"></view>
        </scroll-view>

        <view class="drawer-footer">
          <view class="save-btn" :class="{ loading: isSaving }" @tap="savePersonaSettings">
            <text class="btn-text" v-if="!isSaving">保存设置</text>
            <view class="loading-spinner" v-else></view>
          </view>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, computed, reactive, onMounted, watch } from 'vue'
import { useProjectStore, INDUSTRY_OPTIONS, TONE_OPTIONS, type PersonaSettings } from '@/stores/project'

// Store
const projectStore = useProjectStore()
const activeProject = computed(() => projectStore.activeProject)

// 状态
const showPersonaDrawer = ref(false)
const isSaving = ref(false)
const newKeyword = ref('')
const newTaboo = ref('')

// 选项
const industryOptions = INDUSTRY_OPTIONS
const toneOptions = TONE_OPTIONS

// 编辑表单
const editForm = reactive({
  name: '',
  industry: '通用',
  persona: {
    tone: '专业亲和',
    catchphrase: '',
    target_audience: '',
    benchmark_accounts: [] as string[],
    content_style: '',
    taboos: [] as string[],
    keywords: [] as string[],
    introduction: ''
  } as PersonaSettings
})

// 初始化
onMounted(async () => {
  if (!activeProject.value) {
    await projectStore.fetchProjects()
    if (!projectStore.hasActiveProject && projectStore.projectCount === 0) {
      uni.redirectTo({ url: '/pages/project/list' })
      return
    }
    if (!projectStore.hasActiveProject && projectStore.projectCount > 0) {
      await projectStore.setActiveProject(projectStore.projectList[0])
    }
  }
  
  syncFormFromProject()
  
  const pages = getCurrentPages()
  const currentPage = pages[pages.length - 1] as any
  if (currentPage?.options?.edit === 'true') {
    showPersonaDrawer.value = true
  }
})

watch(activeProject, () => {
  syncFormFromProject()
})

function syncFormFromProject() {
  if (activeProject.value) {
    editForm.name = activeProject.value.name
    editForm.industry = activeProject.value.industry || '通用'
    editForm.persona = { ...activeProject.value.persona_settings }
  }
}

function goBack() {
  uni.navigateBack({
    fail: () => {
      uni.switchTab({ url: '/pages/index/index' })
    }
  })
}

function goToProjectList() {
  uni.navigateTo({ url: '/pages/project/list' })
}

function handleNavigate(route: string) {
  if (!route) {
    uni.showToast({ title: '功能即将上线', icon: 'none' })
    return
  }
  uni.navigateTo({ url: route })
}

function addKeyword() {
  const keyword = newKeyword.value.trim()
  if (keyword && !editForm.persona.keywords.includes(keyword)) {
    editForm.persona.keywords.push(keyword)
    newKeyword.value = ''
  }
}

function removeKeyword(index: number) {
  editForm.persona.keywords.splice(index, 1)
}

function addTaboo() {
  const taboo = newTaboo.value.trim()
  if (taboo && !editForm.persona.taboos.includes(taboo)) {
    editForm.persona.taboos.push(taboo)
    newTaboo.value = ''
  }
}

function removeTaboo(index: number) {
  editForm.persona.taboos.splice(index, 1)
}

async function savePersonaSettings() {
  if (!activeProject.value || isSaving.value) return
  
  isSaving.value = true
  
  try {
    const result = await projectStore.updateProject(activeProject.value.id, {
      name: editForm.name,
      industry: editForm.industry,
      persona_settings: editForm.persona
    })
    
    if (result) {
      uni.showToast({ title: '保存成功', icon: 'success' })
      showPersonaDrawer.value = false
    } else {
      uni.showToast({ title: '保存失败', icon: 'none' })
    }
  } catch (error) {
    uni.showToast({ title: '保存失败', icon: 'none' })
  } finally {
    isSaving.value = false
  }
}
</script>

<style lang="scss" scoped>
.dashboard-page {
  min-height: 100vh;
  background: #F5F7FA;
  position: relative;
}

// 背景装饰
.bg-decoration {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  height: 500rpx;
  pointer-events: none;
  overflow: hidden;
  
  .deco-circle {
    position: absolute;
    border-radius: 50%;
    
    &.c1 {
      width: 400rpx;
      height: 400rpx;
      background: radial-gradient(circle, rgba(59, 130, 246, 0.08) 0%, transparent 70%);
      top: -150rpx;
      right: -100rpx;
    }
    
    &.c2 {
      width: 300rpx;
      height: 300rpx;
      background: radial-gradient(circle, rgba(249, 115, 22, 0.06) 0%, transparent 70%);
      top: 100rpx;
      left: -80rpx;
    }
  }
}

// 顶部导航栏
.nav-bar {
  position: sticky;
  top: 0;
  z-index: 100;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 60rpx 32rpx 24rpx;
  background: linear-gradient(180deg, #F5F7FA 0%, rgba(245, 247, 250, 0.9) 100%);
  backdrop-filter: blur(10px);
  
  .nav-left {
    display: flex;
    align-items: center;
    gap: 16rpx;
    
    .back-btn {
      width: 64rpx;
      height: 64rpx;
      background: #fff;
      border-radius: 16rpx;
      display: flex;
      align-items: center;
      justify-content: center;
      box-shadow: 0 2rpx 12rpx rgba(0, 0, 0, 0.06);
      
      &:active {
        transform: scale(0.95);
      }
      
      .back-icon {
        font-size: 32rpx;
        color: #333;
      }
    }
    
    .nav-title {
      font-size: 36rpx;
      font-weight: 600;
      color: #1a1a2e;
    }
  }
  
  .nav-right {
    .switch-btn {
      display: flex;
      align-items: center;
      gap: 8rpx;
      padding: 14rpx 24rpx;
      background: #fff;
      border-radius: 32rpx;
      box-shadow: 0 2rpx 12rpx rgba(0, 0, 0, 0.06);
      
      &:active {
        transform: scale(0.95);
      }
      
      .switch-icon {
        font-size: 24rpx;
      }
      
      .switch-text {
        font-size: 24rpx;
        color: #666;
      }
    }
  }
}

// 主滚动区域
.main-scroll {
  height: calc(100vh - 150rpx);
  padding: 0 24rpx;
}

// 项目信息卡片
.project-card {
  background: linear-gradient(135deg, #EFF6FF 0%, #DBEAFE 100%);
  border-radius: 24rpx;
  padding: 32rpx;
  margin-bottom: 24rpx;
  position: relative;
  overflow: hidden;
  box-shadow: 0 4rpx 24rpx rgba(59, 130, 246, 0.1);
  
  &:active {
    transform: scale(0.98);
  }
  
  .project-card-content {
    display: flex;
    justify-content: space-between;
    align-items: center;
    position: relative;
    z-index: 2;
  }
  
  .project-info {
    flex: 1;
    
    .project-label {
      font-size: 24rpx;
      color: #64748B;
      margin-bottom: 8rpx;
    }
    
    .project-name {
      font-size: 40rpx;
      font-weight: 700;
      color: #1E40AF;
      margin-bottom: 16rpx;
    }
    
    .project-tags {
      display: flex;
      gap: 12rpx;
      flex-wrap: wrap;
      
      .tag {
        display: flex;
        align-items: center;
        gap: 6rpx;
        padding: 8rpx 16rpx;
        background: rgba(255, 255, 255, 0.7);
        border-radius: 20rpx;
        
        .tag-icon {
          font-size: 20rpx;
        }
        
        .tag-text {
          font-size: 22rpx;
          color: #475569;
        }
      }
    }
  }
  
  .project-action {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 8rpx;
    
    .action-icon-3d {
      position: relative;
      width: 80rpx;
      height: 80rpx;
      
      .icon-face {
        position: absolute;
        width: 100%;
        height: 100%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 40rpx;
        
        &.front {
          background: #fff;
          border-radius: 20rpx;
          box-shadow: 0 4rpx 16rpx rgba(0, 0, 0, 0.1);
          z-index: 2;
        }
        
        &.shadow {
          background: rgba(59, 130, 246, 0.2);
          border-radius: 20rpx;
          top: 8rpx;
          left: 8rpx;
          z-index: 1;
        }
      }
    }
    
    .action-hint {
      font-size: 20rpx;
      color: #64748B;
    }
  }
  
  .project-card-decoration {
    position: absolute;
    top: 0;
    right: 0;
    bottom: 0;
    width: 200rpx;
    pointer-events: none;
    
    .deco-dot {
      position: absolute;
      border-radius: 50%;
      background: rgba(59, 130, 246, 0.1);
      
      &.d1 {
        width: 120rpx;
        height: 120rpx;
        top: -40rpx;
        right: -40rpx;
      }
      
      &.d2 {
        width: 60rpx;
        height: 60rpx;
        top: 60rpx;
        right: 80rpx;
      }
      
      &.d3 {
        width: 40rpx;
        height: 40rpx;
        bottom: 20rpx;
        right: 40rpx;
      }
    }
  }
}

// Bento Grid 布局
.bento-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16rpx;
  margin-bottom: 24rpx;
}

// 通用卡片样式
.bento-card {
  background: #fff;
  border-radius: 20rpx;
  padding: 24rpx;
  box-shadow: 0 4rpx 20rpx rgba(0, 0, 0, 0.05);
  transition: transform 0.2s ease, box-shadow 0.2s ease;
  
  &:active {
    transform: scale(0.98);
    box-shadow: 0 2rpx 12rpx rgba(0, 0, 0, 0.08);
  }
  
  .card-icon-wrapper {
    width: 72rpx;
    height: 72rpx;
    border-radius: 18rpx;
    display: flex;
    align-items: center;
    justify-content: center;
    margin-bottom: 16rpx;
    
    &.gradient-blue {
      background: linear-gradient(135deg, #3B82F6 0%, #60A5FA 100%);
    }
    
    &.gradient-purple {
      background: linear-gradient(135deg, #8B5CF6 0%, #A78BFA 100%);
    }
    
    &.gradient-orange {
      background: linear-gradient(135deg, #F97316 0%, #FB923C 100%);
    }
    
    &.gradient-green {
      background: linear-gradient(135deg, #10B981 0%, #34D399 100%);
    }
    
    &.gradient-red {
      background: linear-gradient(135deg, #EF4444 0%, #F87171 100%);
    }
    
    &.gradient-cyan {
      background: linear-gradient(135deg, #06B6D4 0%, #22D3EE 100%);
    }
    
    .card-icon {
      font-size: 36rpx;
    }
  }
  
  .card-title {
    font-size: 30rpx;
    font-weight: 600;
    color: #1a1a2e;
    display: block;
    margin-bottom: 8rpx;
  }
  
  .card-desc {
    font-size: 24rpx;
    color: #94A3B8;
    display: block;
    line-height: 1.4;
  }
  
  .card-status {
    display: flex;
    align-items: center;
    gap: 8rpx;
    margin-top: 12rpx;
    
    &.inline {
      margin-top: 8rpx;
    }
    
    .status-dot {
      width: 12rpx;
      height: 12rpx;
      border-radius: 50%;
      background: #F59E0B;
    }
    
    .status-text {
      font-size: 20rpx;
      color: #F59E0B;
    }
  }
}

// 大卡片 (跨两行)
.card-large {
  grid-row: span 2;
  display: flex;
  flex-direction: column;
  position: relative;
  overflow: hidden;
  
  .card-header {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    
    .card-badge {
      padding: 6rpx 14rpx;
      background: linear-gradient(135deg, #EEF2FF 0%, #E0E7FF 100%);
      border-radius: 16rpx;
      font-size: 20rpx;
      color: #6366F1;
      font-weight: 500;
    }
  }
  
  .card-body {
    flex: 1;
    padding-top: 16rpx;
    
    .card-title {
      font-size: 36rpx;
      margin-bottom: 12rpx;
    }
    
    .card-desc {
      font-size: 26rpx;
      line-height: 1.5;
    }
  }
  
  .card-illustration {
    position: relative;
    height: 120rpx;
    margin: 20rpx 0;
    padding: 16rpx;
    background: #F8FAFC;
    border-radius: 12rpx;
    
    .illust-line {
      height: 16rpx;
      background: linear-gradient(90deg, #E2E8F0 0%, #CBD5E1 100%);
      border-radius: 8rpx;
      margin-bottom: 12rpx;
      
      &.l1 { width: 80%; }
      &.l2 { width: 60%; }
      &.l3 { width: 40%; }
    }
    
    .illust-cursor {
      position: absolute;
      right: 24rpx;
      bottom: 24rpx;
      width: 4rpx;
      height: 24rpx;
      background: #3B82F6;
      border-radius: 2rpx;
      animation: blink 1s infinite;
    }
  }
  
  .card-arrow {
    display: flex;
    justify-content: flex-end;
    
    .arrow-icon {
      width: 56rpx;
      height: 56rpx;
      background: linear-gradient(135deg, #3B82F6 0%, #60A5FA 100%);
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 28rpx;
      color: #fff;
    }
  }
}

// 小卡片
.card-small {
  min-height: 200rpx;
}

// 宽卡片 (通栏)
.card-wide {
  grid-column: span 2;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 28rpx 32rpx;
  
  .card-left {
    display: flex;
    align-items: center;
    gap: 20rpx;
    
    .card-icon-wrapper {
      margin-bottom: 0;
    }
    
    .card-text {
      .card-title {
        margin-bottom: 4rpx;
      }
    }
  }
  
  .card-right {
    display: flex;
    align-items: center;
    gap: 20rpx;
    
    .mini-chart {
      display: flex;
      align-items: flex-end;
      gap: 6rpx;
      height: 60rpx;
      
      .chart-bar {
        width: 12rpx;
        background: linear-gradient(180deg, #10B981 0%, #34D399 100%);
        border-radius: 6rpx 6rpx 0 0;
        opacity: 0.6;
      }
    }
  }
}

// 半宽卡片
.card-half {
  display: flex;
  align-items: center;
  gap: 16rpx;
  padding: 20rpx 24rpx;
  
  .card-icon-wrapper {
    width: 56rpx;
    height: 56rpx;
    margin-bottom: 0;
    flex-shrink: 0;
    
    .card-icon {
      font-size: 28rpx;
    }
  }
  
  .card-title {
    flex: 1;
    margin-bottom: 0;
    font-size: 28rpx;
  }
  
  .card-status {
    margin-top: 0;
  }
}

// 底部安全区
.bottom-safe-area {
  height: calc(40rpx + env(safe-area-inset-bottom));
}

// ========== 抽屉样式 ==========
.drawer-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  backdrop-filter: blur(4px);
  z-index: 1000;
  animation: fadeIn 0.2s ease;
}

.drawer-content {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  max-height: 85vh;
  background: #fff;
  border-radius: 32rpx 32rpx 0 0;
  display: flex;
  flex-direction: column;
  animation: slideUp 0.3s ease;
  
  .drawer-handle {
    width: 80rpx;
    height: 8rpx;
    background: #e0e0e0;
    border-radius: 4rpx;
    margin: 20rpx auto;
  }
  
  .drawer-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 16rpx 32rpx 24rpx;
    border-bottom: 1rpx solid #f0f0f0;
    
    .drawer-title {
      font-size: 36rpx;
      font-weight: 600;
      color: #1a1a2e;
    }
    
    .drawer-close {
      width: 56rpx;
      height: 56rpx;
      background: #f5f5f5;
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
      
      .close-icon {
        font-size: 40rpx;
        color: #999;
        line-height: 1;
      }
    }
  }
  
  .drawer-body {
    flex: 1;
    overflow-y: auto;
    padding: 24rpx 32rpx;
  }
  
  .drawer-spacer {
    height: 32rpx;
  }
  
  .drawer-footer {
    padding: 24rpx 32rpx;
    padding-bottom: calc(24rpx + env(safe-area-inset-bottom));
    border-top: 1rpx solid #f0f0f0;
    
    .save-btn {
      height: 96rpx;
      background: linear-gradient(135deg, #3B82F6 0%, #60A5FA 100%);
      border-radius: 48rpx;
      display: flex;
      align-items: center;
      justify-content: center;
      box-shadow: 0 8rpx 24rpx rgba(59, 130, 246, 0.3);
      
      &.loading {
        background: #a0c8f0;
      }
      
      &:active:not(.loading) {
        transform: scale(0.98);
      }
      
      .btn-text {
        font-size: 32rpx;
        font-weight: 600;
        color: #fff;
      }
      
      .loading-spinner {
        width: 36rpx;
        height: 36rpx;
        border: 3rpx solid rgba(255, 255, 255, 0.3);
        border-top-color: #fff;
        border-radius: 50%;
        animation: spin 0.8s linear infinite;
      }
    }
  }
}

// 设置区块
.setting-section {
  margin-bottom: 32rpx;
  
  .section-title {
    font-size: 28rpx;
    font-weight: 600;
    color: #1a1a2e;
    margin-bottom: 20rpx;
    display: block;
  }
}

// 设置项
.setting-item {
  margin-bottom: 24rpx;
  
  .item-label {
    font-size: 26rpx;
    color: #666;
    margin-bottom: 12rpx;
    display: block;
  }
  
  .item-input {
    width: 100%;
    height: 88rpx;
    background: #F5F7FA;
    border-radius: 16rpx;
    padding: 0 24rpx;
    font-size: 28rpx;
    color: #333;
  }
  
  .item-textarea {
    width: 100%;
    min-height: 160rpx;
    background: #F5F7FA;
    border-radius: 16rpx;
    padding: 20rpx 24rpx;
    font-size: 28rpx;
    color: #333;
    line-height: 1.6;
  }
  
  .picker-display {
    display: flex;
    align-items: center;
    justify-content: space-between;
    height: 88rpx;
    background: #F5F7FA;
    border-radius: 16rpx;
    padding: 0 24rpx;
    
    .picker-value {
      font-size: 28rpx;
      color: #333;
    }
    
    .picker-arrow {
      font-size: 20rpx;
      color: #999;
    }
  }
}

// 语气选项
.tone-options {
  display: flex;
  flex-wrap: wrap;
  gap: 16rpx;
  
  .tone-tag {
    padding: 16rpx 24rpx;
    background: #F5F7FA;
    border-radius: 32rpx;
    border: 2rpx solid transparent;
    transition: all 0.2s ease;
    
    &.selected {
      background: linear-gradient(135deg, #EEF2FF 0%, #E0E7FF 100%);
      border-color: #3B82F6;
      
      .tag-text {
        color: #3B82F6;
        font-weight: 500;
      }
    }
    
    .tag-text {
      font-size: 26rpx;
      color: #666;
    }
  }
}

// 关键词
.keywords-wrapper {
  display: flex;
  flex-wrap: wrap;
  gap: 12rpx;
  padding: 16rpx;
  background: #F5F7FA;
  border-radius: 16rpx;
  min-height: 100rpx;
  
  .keyword-tag {
    display: flex;
    align-items: center;
    gap: 8rpx;
    padding: 12rpx 20rpx;
    background: linear-gradient(135deg, #EEF2FF 0%, #E0E7FF 100%);
    border-radius: 24rpx;
    
    &.taboo-tag {
      background: linear-gradient(135deg, #FEF2F2 0%, #FEE2E2 100%);
      
      .keyword-text {
        color: #EF4444;
      }
      
      .keyword-remove {
        color: #EF4444;
      }
    }
    
    .keyword-text {
      font-size: 24rpx;
      color: #3B82F6;
    }
    
    .keyword-remove {
      font-size: 28rpx;
      color: #3B82F6;
      line-height: 1;
    }
  }
  
  .keyword-input {
    flex: 1;
    min-width: 200rpx;
    height: 56rpx;
    font-size: 26rpx;
    color: #333;
  }
}

// 动画
@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

@keyframes slideUp {
  from {
    opacity: 0;
    transform: translateY(100%);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

@keyframes blink {
  0%, 50% { opacity: 1; }
  51%, 100% { opacity: 0; }
}
</style>
