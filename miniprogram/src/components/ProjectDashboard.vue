<template>
  <view class="dashboard-page">
    <!-- 顶部用户信息栏 -->
    <view class="top-bar">
      <view class="user-info-left">
        <view class="user-dot"></view>
        <text class="user-name">{{ activeProject?.name || userName || '创作者' }}</text>
      </view>
      <view class="user-info-right">
        <view class="points-icon">💎</view>
        <text class="user-points">{{ userPoints || 1280 }} 点数</text>
      </view>
    </view>

    <!-- 主内容区 -->
    <scroll-view class="main-scroll" scroll-y>
      <!-- 当前活跃人设卡片 -->
      <view class="persona-card" @tap="showPersonaDrawer = true">
        <view class="persona-card-content">
          <view class="persona-left">
            <view class="persona-icon-wrapper">
              <view class="icon-circle">
                <AgentIcon iconName="Star" :size="48" />
              </view>
              <view class="active-dot"></view>
            </view>
            <view class="persona-info">
              <text class="persona-label">当前活跃人设</text>
              <text class="persona-name">{{ activeProject?.name || '选择人设' }}</text>
              <text class="persona-desc">{{ activeProject?.persona_settings?.tone || DEFAULT_PERSONA_SETTINGS.tone
              }}·智囊型</text>
            </view>
          </view>
          <view class="persona-toggle">
            <u-icon name="setting" color="#6C757D" size="32"></u-icon>
          </view>
        </view>
      </view>

      <!-- 灵感输入区 -->
      <view class="input-section">
        <view class="input-card">
          <input class="inspiration-input" placeholder="记录此刻灵感瞬间..." placeholder-class="input-placeholder" />
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
      <view class="section-header section-header-accent">
        <text class="section-title section-title-accent">今天拍点啥</text>
      </view>
      <view class="category-grid">
        <view class="category-item" @tap="handleCategoryClick('story')">
          <view class="category-icon-wrapper">
            <AgentIcon iconName="Reading" :size="64" />
          </view>
          <text class="category-label">讲故事</text>
        </view>
        <view class="category-item" @tap="handleCategoryClick('opinion')">
          <view class="category-icon-wrapper">
            <AgentIcon iconName="ChatDotRound" :size="64" />
          </view>
          <text class="category-label">聊观点</text>
        </view>
        <view class="category-item" @tap="handleCategoryClick('process')">
          <view class="category-icon-wrapper">
            <AgentIcon iconName="Film" :size="64" />
          </view>
          <text class="category-label">晒过程</text>
        </view>
        <view class="category-item" @tap="handleCategoryClick('knowledge')">
          <view class="category-icon-wrapper">
            <AgentIcon iconName="Document" :size="64" />
          </view>
          <text class="category-label">教知识</text>
        </view>
        <view class="category-item" @tap="handleCategoryClick('hotspot')">
          <view class="category-icon-wrapper">
            <AgentIcon iconName="TrendCharts" :size="64" />
          </view>
          <text class="category-label">蹭热点</text>
        </view>
      </view>

      <!-- 快捷指令库 -->
      <view class="section-header">
        <text class="section-title">快捷指令库</text>
      </view>
      <view class="quick-command-grid">
        <view class="command-card" @tap="handleNavigate('/pages/copywriting/index')">
          <view class="command-icon-wrapper">
            <AgentIcon iconName="User" :size="48" />
          </view>
          <view class="command-content">
            <text class="command-title">我在起号</text>
            <text class="command-desc">需要人设故事</text>
          </view>
        </view>
        <view class="command-card" @tap="handleNavigate('')">
          <view class="command-icon-wrapper">
            <AgentIcon iconName="Platform" :size="48" />
          </view>
          <view class="command-content">
            <text class="command-title">我在同城</text>
            <text class="command-desc">需要泛流话题</text>
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

// ========== 顶部用户信息栏 ==========
.top-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 24rpx 32rpx 20rpx;
    background: #FFFFFF;
    position: relative;
    z-index: 10;
    box-shadow: 0 2rpx 12rpx rgba(0, 0, 0, 0.04);
  
    .user-info-left {
      display: flex;
      align-items: center;
    gap: 12rpx;
    .user-dot {
        width: 10rpx;
        height: 10rpx;
        border-radius: 50%;
        background: linear-gradient(135deg, #FF9500 0%, #FFB84D 100%);
        box-shadow: 0 0 8rpx rgba(255, 149, 0, 0.4);
        animation: pulse 2s ease-in-out infinite;
      }
        .user-name {
          font-size: 32rpx;
      font-weight: 600;
      color: #1A1A1A;
        letter-spacing: -0.5rpx;
    }
  }
  
    .user-info-right {
      display: flex;
      align-items: center;
      gap: 8rpx;
    padding: 10rpx 20rpx;
      background: linear-gradient(135deg, #F8F9FA 0%, #F1F3F5 100%);
      border-radius: 24rpx;
      border: 1rpx solid rgba(0, 0, 0, 0.05);
    .points-icon {
        font-size: 24rpx;
      opacity: 0.8;
    
        .user-points {
          font-size: 24rpx;
      color: #495057;
        font-weight: 500;
    }
  }
}

// ========== 主滚动区域 ==========
.main-scroll {
  height: calc(100vh - 100rpx);
    padding: 0 32rpx 32rpx;
    position: relative;
    z-index: 1;
}

// ========== 分区标题 ==========
.section-header {
  padding: 32rpx 0 16rpx;

  .section-title {
    font-size: 28rpx;
    font-weight: 500;
    color: #6C757D;
  }

  &.section-header-accent {
    padding: 32rpx 0 20rpx;

    .section-title-accent {
      font-size: 32rpx;
      font-weight: 700;
      background: linear-gradient(135deg, #FF9500 0%, #FFB84D 100%);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      background-clip: text;
    }
  }
}

// ========== 人设卡片 ==========
.persona-card {
  background: #FFFFFF;
  border-radius: 24rpx;
  padding: 32rpx;
  margin-bottom: 32rpx;
    box-shadow:
      0 4rpx 20rpx rgba(0, 0, 0, 0.06),
      0 1rpx 3rpx rgba(0, 0, 0, 0.04);
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    border: 1rpx solid rgba(0, 0, 0, 0.04);
  
  &:active {
    transform: scale(0.98);
    box-shadow:
        0 2rpx 12rpx rgba(0, 0, 0, 0.08),
        0 1rpx 2rpx rgba(0, 0, 0, 0.06);
  }
  
    .persona-card-content {
    display: flex;
    align-items: center;
    justify-content: space-between;
  }
  
    .persona-left {
      display: flex;
      align-items: center;
      gap: 20rpx;
    
    .persona-icon-wrapper {
        position: relative;
      display: flex;
      align-items: center;
        justify-content: center;
      
      .icon-circle {
          width: 96rpx;
          height: 96rpx;
          border-radius: 50%;
          background: linear-gradient(135deg, #F0F4FF 0%, #E8F0FE 100%);
        display: flex;
        align-items: center;
        justify-content: center;
          border: 2rpx solid rgba(59, 130, 246, 0.1);
          box-shadow:
            0 4rpx 16rpx rgba(59, 130, 246, 0.08),
            inset 0 1rpx 0 rgba(255, 255, 255, 0.8);
          position: relative;
        
        :deep(.agent-icon) {
            filter: drop-shadow(0 2rpx 8rpx rgba(59, 130, 246, 0.2));
        }
      }
            .active-dot {
              position: absolute;
              top: -2rpx;
              right: -2rpx;
              width: 20rpx;
              height: 20rpx;
              background: linear-gradient(135deg, #10B981 0%, #34D399 100%);
              border-radius: 50%;
              border: 3rpx solid #FFFFFF;
              box-shadow:
                0 0 12rpx rgba(16, 185, 129, 0.5),
                0 2rpx 8rpx rgba(0, 0, 0, 0.15);
              animation: pulse-dot 2s ease-in-out infinite;
      }
        .persona-info {
          display: flex;
          flex-direction: column;
      gap: 8rpx;
      .persona-label {
          font-size: 24rpx;
          color: #94A3B8;
          font-weight: 400;
        }
            .persona-name {
              font-size: 36rpx;
              font-weight: 700;
              color: #1A1A1A;
              line-height: 1.2;
              letter-spacing: -0.5rpx;
            }
            .persona-desc {
              font-size: 26rpx;
              color: #64748B;
        line-height: 1.2;
        }
    }
  }
  
    .persona-toggle {
      width: 56rpx;
      height: 56rpx;
      display: flex;
      align-items: center;
      justify-content: center;
      background: #F8F9FA;
      border-radius: 50%;
    border: 1rpx solid rgba(0, 0, 0, 0.05);
      transition: all 0.3s ease;
    &:active {
        background: #F1F3F5;
        transform: rotate(90deg) scale(0.95);
      }
    }
    }
// ========== 灵感输入区 ==========
.input-section {
  margin-bottom: 32rpx;

  .input-card {
    display: flex;
    align-items: center;
    justify-content: space-between;
    background: #FFFFFF;
    border-radius: 20rpx;
    padding: 20rpx 24rpx;
    margin-bottom: 12rpx;
    border: 1rpx solid rgba(0, 0, 0, 0.06);
    box-shadow: 0 2rpx 8rpx rgba(0, 0, 0, 0.04);
    transition: all 0.3s ease;

    &:focus-within {
      border-color: rgba(59, 130, 246, 0.3);
      box-shadow:
        0 4rpx 16rpx rgba(59, 130, 246, 0.12),
        0 0 0 4rpx rgba(59, 130, 246, 0.05);
      
            .inspiration-input {
              flex: 1;
              font-size: 28rpx;
              color: #1A1A1A;
              background: transparent;
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
            transition: all 0.3s ease;
          &.mic-icon {
              background: #F8F9FA;
            &:active {
                background: #F1F3F5;
                transform: scale(0.9);
              }
                    }
                    &.send-btn {
                      background: linear-gradient(135deg, #FF9500 0%, #FFB84D 100%);
                      box-shadow:
                        0 4rpx 16rpx rgba(255, 149, 0, 0.3),
                        0 0 0 0 rgba(255, 149, 0, 0.2);
            &:active {
                transform: scale(0.9);
                box-shadow: 0 2rpx 8rpx rgba(255, 149, 0, 0.25);
              }
                    }
                }
                }
        }
        .input-hint {
          font-size: 22rpx;
          color: #94A3B8;
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
      padding: 20rpx 12rpx;
      border-radius: 20rpx;
      background: #FFFFFF;
      border: 1rpx solid rgba(0, 0, 0, 0.06);
      box-shadow: 0 2rpx 8rpx rgba(0, 0, 0, 0.04);
      transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
      position: relative;
      overflow: hidden;
    
    &::before {
        content: '';
        position: absolute;
        inset: 0;
        background: linear-gradient(135deg, rgba(255, 149, 0, 0.05), rgba(59, 130, 246, 0.05));
        opacity: 0;
        transition: opacity 0.3s ease;
    }
    
        &:active {
          transform: translateY(-2rpx) scale(0.97);
          box-shadow: 0 4rpx 16rpx rgba(0, 0, 0, 0.08);
      &::before {
          opacity: 1;
        }
      }
        .category-icon-wrapper {
          position: relative;
      z-index: 1;
        width: 88rpx;
        height: 88rpx;
        border-radius: 20rpx;
        background: linear-gradient(135deg, #F8F9FA 0%, #F1F3F5 100%);
        display: flex;
      align-items: center;
        justify-content: center;
        border: 1rpx solid rgba(0, 0, 0, 0.04);
        transition: all 0.3s ease;
      :deep(.agent-icon) {
          filter: drop-shadow(0 2rpx 6rpx rgba(0, 0, 0, 0.1));
          transition: all 0.3s ease;
        }
      }
    
        &:active .category-icon-wrapper {
          background: linear-gradient(135deg, #FFF5E6 0%, #FFE8CC 100%);
          border-color: rgba(255, 149, 0, 0.2);
          transform: scale(1.05);
      :deep(.agent-icon) {
          filter: drop-shadow(0 4rpx 12rpx rgba(255, 149, 0, 0.3));
        }
      }
        .category-label {
          font-size: 24rpx;
          font-weight: 500;
          color: #495057;
          text-align: center;
          position: relative;
      z-index: 1;
    
    }
    }
// ========== 快捷指令网格 ==========
.quick-command-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16rpx;
  margin-bottom: 32rpx;
  .command-card {
      background: #FFFFFF;
      border-radius: 20rpx;
      padding: 24rpx;
      display: flex;
      align-items: center;
    gap: 16rpx;
      border: 1rpx solid rgba(0, 0, 0, 0.06);
      box-shadow: 0 2rpx 8rpx rgba(0, 0, 0, 0.04);
      transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
      position: relative;
      overflow: hidden;
    &::before {
        content: '';
        position: absolute;
        inset: 0;
        background: linear-gradient(135deg, rgba(255, 149, 0, 0.03), rgba(59, 130, 246, 0.03));
        opacity: 0;
        transition: opacity 0.3s ease;
      }
    
        &:active {
          transform: translateY(-2rpx) scale(0.98);
          box-shadow: 0 4rpx 16rpx rgba(0, 0, 0, 0.08);
          border-color: rgba(59, 130, 246, 0.2);
      &::before {
          opacity: 1;
        }
      }
        .command-icon-wrapper {
          position: relative;
          z-index: 1;
          width: 72rpx;
          height: 72rpx;
          border-radius: 16rpx;
          background: linear-gradient(135deg, #F0F4FF 0%, #E8F0FE 100%);
          display: flex;
          align-items: center;
      justify-content: center;
        border: 1rpx solid rgba(59, 130, 246, 0.1);
        flex-shrink: 0;
        transition: all 0.3s ease;
      
      :deep(.agent-icon) {
          filter: drop-shadow(0 2rpx 6rpx rgba(59, 130, 246, 0.2));
      }
    }
        &:active .command-icon-wrapper {
          background: linear-gradient(135deg, #E8F0FE 0%, #DBEAFE 100%);
          transform: scale(1.05) rotate(5deg);
          border-color: rgba(59, 130, 246, 0.3);
        }
        .command-content {
          flex: 1;
          display: flex;
      flex-direction: column;
        gap: 4rpx;
        min-width: 0;
        position: relative;
        z-index: 1;
      .command-title {
          font-size: 28rpx;
        font-weight: 600;
          color: #1A1A1A;
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

// ========== 底部安全区 ==========
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

// ========== 设置区块 ==========
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

// ========== 设置项 ==========
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

// ========== 语气选项 ==========
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

// ========== 关键词 ==========
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

// ========== 动画 ==========
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
@keyframes pulse {

  0%,
  100% {
    opacity: 1;
    transform: scale(1);
  }

  50% {
    opacity: 0.8;
    transform: scale(1.05);
  }
}

@keyframes pulse-dot {

  0%,
  100% {
    box-shadow:
      0 0 12rpx rgba(16, 185, 129, 0.5),
      0 2rpx 8rpx rgba(0, 0, 0, 0.15);
  }

  50% {
    box-shadow:
      0 0 20rpx rgba(16, 185, 129, 0.7),
      0 2rpx 8rpx rgba(0, 0, 0, 0.15);
  }
}
</style>
