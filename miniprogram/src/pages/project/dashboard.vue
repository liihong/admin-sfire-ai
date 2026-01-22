<template>
  <view class="dashboard-page">
    <!-- 顶部用户信息栏 -->
    <view class="top-bar">
      <view class="user-info">
        <text class="user-name">{{ userName || '创作者' }}</text>
        <text class="user-points">{{ userPoints || 0 }} 点数</text>
      </view>
    </view>

    <!-- 主内容区 -->
    <scroll-view class="main-scroll" scroll-y>
      <!-- 当前活跃人设卡片 -->
      <view class="persona-card" @tap="showPersonaDrawer = true">
        <view class="persona-card-content">
          <view class="persona-left">
            <view class="persona-icon-wrapper">
              <AgentIcon iconName="Star" :size="64" />
              <view class="active-dot"></view>
            </view>
            <view class="persona-info">
              <text class="persona-name">{{ activeProject?.name || '选择人设' }}</text>
              <text class="persona-desc">{{ activeProject?.persona_settings?.tone || DEFAULT_PERSONA_SETTINGS.tone }}·智囊型</text>
            </view>
          </view>
          <view class="persona-toggle">
            <u-icon name="reload" color="#ADB5BD" size="32"></u-icon>
          </view>
        </view>
      </view>

      <!-- 灵感输入区 -->
      <view class="input-section">
        <view class="input-card">
          <input
            class="inspiration-input"
            placeholder="记录此刻灵感瞬间..."
            placeholder-class="input-placeholder"
          />
          <view class="input-actions">
            <view class="action-icon mic-icon">
              <u-icon name="mic" color="#6C757D" size="40"></u-icon>
            </view>
            <view class="action-icon send-btn">
              <u-icon name="arrow-right" color="#FFFFFF" size="32"></u-icon>
            </view>
          </view>
        </view>
        <text class="input-hint">每一个灵感瞬间都将成为你的优秀选题</text>
      </view>

      <!-- 今天拍点啥 - 分类网格 -->
      <view class="section-header">
        <text class="section-title">今天拍点啥</text>
      </view>
      <view class="category-grid">
        <view class="category-item" @tap="handleCategoryClick('story')">
          <AgentIcon iconName="Reading" :size="88" />
          <text class="category-label">讲故事</text>
        </view>
        <view class="category-item" @tap="handleCategoryClick('opinion')">
          <AgentIcon iconName="ChatDotRound" :size="88" />
          <text class="category-label">聊观点</text>
        </view>
        <view class="category-item" @tap="handleCategoryClick('process')">
          <AgentIcon iconName="Film" :size="88" />
          <text class="category-label">晒过程</text>
        </view>
        <view class="category-item" @tap="handleCategoryClick('knowledge')">
          <AgentIcon iconName="Document" :size="88" />
          <text class="category-label">教知识</text>
        </view>
        <view class="category-item" @tap="handleCategoryClick('hotspot')">
          <AgentIcon iconName="TrendCharts" :size="88" />
          <text class="category-label">蹭热点</text>
        </view>
      </view>

      <!-- 快捷指令库 -->
      <view class="section-header">
        <text class="section-title">快捷指令库</text>
      </view>
      <view class="quick-command-grid">
        <view class="command-card" @tap="handleNavigate('/pages/copywriting/index')">
          <AgentIcon iconName="User" :size="56" />
          <view class="command-content">
            <text class="command-title">我在起号</text>
            <text class="command-desc">需要人设故事</text>
          </view>
        </view>
        <view class="command-card" @tap="handleNavigate('')">
          <AgentIcon iconName="Platform" :size="56" />
          <view class="command-content">
            <text class="command-title">我在同城</text>
            <text class="command-desc">需要泛流话题</text>
          </view>
        </view>
      </view>

      <!-- 原有功能入口 (简化版) -->
      <view class="section-header">
        <text class="section-title">更多功能</text>
      </view>
      <view class="feature-grid">
        <view class="feature-item" @tap="handleNavigate('/pages/copywriting/index')">
          <AgentIcon iconName="EditPen" :size="64" />
          <text class="feature-title">智能文案创作</text>
          <text class="feature-desc">AI 驱动的高质量内容生成</text>
        </view>
        <view class="feature-item" @tap="handleNavigate('')">
          <AgentIcon iconName="MagicStick" :size="64" />
          <text class="feature-title">数字人定制</text>
          <view class="feature-status">
            <text class="status-text">即将上线</text>
          </view>
        </view>
        <view class="feature-item" @tap="handleNavigate('')">
          <AgentIcon iconName="Star" :size="64" />
          <text class="feature-title">爆款选题</text>
          <view class="feature-status">
            <text class="status-text">即将上线</text>
          </view>
        </view>
        <view class="feature-item" @tap="handleNavigate('')">
          <AgentIcon iconName="DataBoard" :size="64" />
          <text class="feature-title">数据看板</text>
          <view class="feature-status">
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
import { useProjectStore, INDUSTRY_OPTIONS, TONE_OPTIONS, DEFAULT_PERSONA_SETTINGS, type PersonaSettings } from '@/stores/project'
import { fetchProjects, updateProject } from '@/api/project'
import AgentIcon from '@/components/AgentIcon.vue'

// Store
const projectStore = useProjectStore()
const activeProject = computed(() => projectStore.activeProject)

// 状态
const showPersonaDrawer = ref(false)
const isSaving = ref(false)
const newKeyword = ref('')
const newTaboo = ref('')
const userName = ref('创作者')
const userPoints = ref(1280)

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
  // 获取 URL 参数
  const pages = getCurrentPages()
  const currentPage = pages[pages.length - 1] as any
  const urlParams = currentPage?.options || {}
  const editMode = urlParams.edit === 'true'
  const projectId = urlParams.id

  // 如果需要编辑特定项目，先加载项目列表
  if (projectId || !activeProject.value) {
    try {
      const response = await fetchProjects()
      projectStore.setProjectList(response.projects, response.active_project_id)

      // 如果 URL 中指定了项目 ID，设置为激活项目
      if (projectId) {
        const targetProject = response.projects.find(p => String(p.id) === String(projectId))
        if (targetProject) {
          projectStore.setActiveProjectLocal(targetProject)
        } else {
          uni.showToast({ title: '项目不存在', icon: 'none' })
          uni.navigateBack()
          return
        }
      } else if (!projectStore.hasActiveProject) {
        // 如果没有指定项目 ID 且没有激活项目
        if (projectStore.projectCount === 0) {
          uni.redirectTo({ url: '/pages/project/list' })
          return
        }
        if (projectStore.projectCount > 0) {
          const firstProject = projectStore.projectList[0]
          projectStore.setActiveProjectLocal(firstProject)
        }
      }
    } catch (error) {
      console.error('Failed to fetch projects:', error)
      if (projectStore.projectCount === 0) {
        uni.redirectTo({ url: '/pages/project/list' })
        return
      }
    }
  }
  
  // 回填表单数据
  syncFormFromProject()
  
  // 如果是编辑模式，打开抽屉
  if (editMode) {
    showPersonaDrawer.value = true
  }
})

watch(activeProject, () => {
  syncFormFromProject()
})

function syncFormFromProject() {
  if (activeProject.value) {
    editForm.name = activeProject.value.name || ''
    editForm.industry = activeProject.value.industry || '通用'
    // 使用默认值合并，确保所有字段都有值
    const personaSettings = activeProject.value.persona_settings || {}
    editForm.persona = {
      tone: personaSettings.tone || DEFAULT_PERSONA_SETTINGS.tone,
      catchphrase: personaSettings.catchphrase || DEFAULT_PERSONA_SETTINGS.catchphrase,
      target_audience: personaSettings.target_audience || DEFAULT_PERSONA_SETTINGS.target_audience,
      benchmark_accounts: personaSettings.benchmark_accounts || [...DEFAULT_PERSONA_SETTINGS.benchmark_accounts],
      content_style: personaSettings.content_style || DEFAULT_PERSONA_SETTINGS.content_style,
      taboos: personaSettings.taboos || [...DEFAULT_PERSONA_SETTINGS.taboos],
      keywords: personaSettings.keywords || [...DEFAULT_PERSONA_SETTINGS.keywords],
      introduction: personaSettings.introduction || DEFAULT_PERSONA_SETTINGS.introduction
    }
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

function handleCategoryClick(category: string) {
  const categoryMap: Record<string, string> = {
    story: '讲故事',
    opinion: '聊观点',
    process: '晒过程',
    knowledge: '教知识',
    hotspot: '蹭热点'
  }
  uni.showToast({ title: `已选择：${categoryMap[category] || category}`, icon: 'none' })
  // TODO: 导航到对应的分类页面
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
    const result = await updateProject(activeProject.value.id, {
      name: editForm.name,
      industry: editForm.industry,
      persona_settings: editForm.persona
    })
    
    // 更新 store 状态
    projectStore.upsertProject(result)
    // 如果更新的是当前激活的项目，更新激活项目状态
    if (activeProject.value.id === result.id) {
      projectStore.setActiveProjectLocal(result)
    }

    uni.showToast({ title: '保存成功', icon: 'success' })
    showPersonaDrawer.value = false
  } catch (error) {
    console.error('Failed to update project:', error)
    uni.showToast({ title: '保存失败', icon: 'none' })
  } finally {
    isSaving.value = false
  }
}
</script>

<style lang="scss" scoped>
// ========== 基础样式 ==========
.dashboard-page {
  min-height: 100vh;
  background: #FFFFFF;
}

// 顶部用户信息栏
.top-bar {
  display: flex;
  justify-content: flex-end;
  align-items: center;
  padding: 24rpx 32rpx 16rpx;
  background: #FFFFFF;

  .user-info {
    display: flex;
    align-items: center;
    gap: 16rpx;

    .user-name {
      font-size: 32rpx;
      font-weight: 600;
      color: #212529;
    }

    .user-points {
      font-size: 24rpx;
      color: #6C757D;
    }
  }
}

// 主滚动区域
.main-scroll {
  height: calc(100vh - 100rpx);
  padding: 0 32rpx 32rpx;
}

// ========== 分区标题 ==========
.section-header {
  padding: 32rpx 0 16rpx;

  .section-title {
    font-size: 28rpx;
    font-weight: 500;
    color: #6C757D;
  }
}

// ========== 人设卡片 ==========
.persona-card {
  background: #F8F9FA;
  border-radius: 24rpx;
  padding: 24rpx;
  margin-bottom: 24rpx;
  transition: all 0.2s ease;

  &:active {
    transform: scale(0.98);
    background: #E9ECEF;
  }

  .persona-card-content {
    display: flex;
    align-items: center;
    justify-content: space-between;
  }

  .persona-left {
    display: flex;
    align-items: center;
    gap: 16rpx;

    .persona-icon-wrapper {
      position: relative;
      display: flex;
      align-items: center;
      justify-content: center;

      :deep(.agent-icon) {
        border-radius: 12rpx;
      }

      .active-dot {
        position: absolute;
        bottom: -4rpx;
        right: -4rpx;
        width: 20rpx;
        height: 20rpx;
        background: #28A745;
        border-radius: 50%;
        border: 4rpx solid #F8F9FA;
        box-shadow: 0 2rpx 8rpx rgba(40, 167, 69, 0.3);
      }
    }

    .persona-info {
      display: flex;
      flex-direction: column;
      gap: 6rpx;

      .persona-name {
        font-size: 32rpx;
        font-weight: 600;
        color: #212529;
        line-height: 1.2;
      }

      .persona-desc {
        font-size: 24rpx;
        color: #6C757D;
        line-height: 1.2;
      }
    }
  }

  .persona-toggle {
    width: 48rpx;
    height: 48rpx;
    display: flex;
    align-items: center;
    justify-content: center;
  }
}

// ========== 灵感输入区 ==========
.input-section {
  margin-bottom: 32rpx;

  .input-card {
    display: flex;
    align-items: center;
    justify-content: space-between;
    background: #F8F9FA;
    border-radius: 16rpx;
    padding: 20rpx 24rpx;
    margin-bottom: 12rpx;
    transition: all 0.2s ease;

    &:focus-within {
      background: #E9ECEF;
    }

    .inspiration-input {
      flex: 1;
      font-size: 28rpx;
      color: #212529;
    }

    .input-placeholder {
      color: #ADB5BD;
    }

    .input-actions {
      display: flex;
      align-items: center;
      gap: 12rpx;

      .action-icon {
        width: 48rpx;
        height: 48rpx;
        display: flex;
        align-items: center;
        justify-content: center;
        border-radius: 50%;
        transition: all 0.2s ease;

        &.mic-icon {
          &:active {
            background: #E9ECEF;
          }
        }

        &.send-btn {
          background: #FF9500;
          box-shadow: 0 4rpx 12rpx rgba(255, 149, 0, 0.3);

          &:active {
            transform: scale(0.92);
            box-shadow: 0 2rpx 8rpx rgba(255, 149, 0, 0.3);
          }
        }
      }
    }
  }

  .input-hint {
    font-size: 22rpx;
    color: #ADB5BD;
    display: block;
    padding-left: 8rpx;
  }
}

// ========== 分类网格 ==========
.category-grid {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 16rpx;
  margin-bottom: 32rpx;

  .category-item {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 12rpx;
    transition: transform 0.2s ease;

    &:active {
      transform: scale(0.92);
    }
  }

  .category-label {
    font-size: 22rpx;
    color: #6C757D;
    text-align: center;
  }
}

// ========== 快捷指令网格 ==========
.quick-command-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16rpx;
  margin-bottom: 32rpx;

  .command-card {
    background: #F8F9FA;
    border-radius: 20rpx;
    padding: 24rpx;
    display: flex;
    align-items: center;
    gap: 16rpx;
    transition: all 0.2s ease;

    &:active {
      transform: scale(0.98);
      background: #E9ECEF;
    }

    .command-content {
      flex: 1;
      display: flex;
      flex-direction: column;
      gap: 4rpx;
      min-width: 0;

      .command-title {
        font-size: 28rpx;
        font-weight: 600;
        color: #212529;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
      }

      .command-desc {
        font-size: 22rpx;
        color: #6C757D;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
      }
    }
  }
}

// ========== 更多功能网格 ==========
.feature-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16rpx;
  margin-bottom: 32rpx;

  .feature-item {
    background: #F8F9FA;
    border-radius: 20rpx;
    padding: 28rpx 24rpx;
    display: flex;
    flex-direction: column;
    align-items: center;
    text-align: center;
    gap: 12rpx;
    transition: all 0.2s ease;

    &:active {
      transform: scale(0.98);
      background: #E9ECEF;
    }

    .feature-title {
      font-size: 26rpx;
      font-weight: 500;
      color: #212529;
    }

    .feature-desc {
      font-size: 22rpx;
      color: #6C757D;
      line-height: 1.3;
    }

    .feature-status {
      .status-text {
        font-size: 20rpx;
        color: #F59E0B;
      }
    }
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
