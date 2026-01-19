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
        <view class="back-btn" @tap="goBack" v-if="!isInTabBar">
          <view class="icon-arrow-left"></view>
        </view>
        <text class="nav-title">操盘控制台</text>
      </view>
      <view class="nav-right">
        <view class="settings-btn" @tap="showPersonaDrawer = true">
          <view class="icon-settings"></view>
        </view>
      </view>
    </view>

    <!-- 主内容区 -->
    <scroll-view class="main-scroll" scroll-y>
      <!-- Phase 2: IP Cockpit Widget -->
      <view class="ip-cockpit-card" @tap="showPersonaDrawer = true">
        <view class="cockpit-content">
          <view class="cockpit-left">
            <view class="avatar-wrapper">
              <view class="avatar" :style="{ background: activeProject?.avatar_color || '#FF8800' }">
                <text class="avatar-letter">{{ activeProject?.avatar_letter || '项' }}</text>
              </view>
              <view class="avatar-badge"></view>
            </view>
            <view class="project-info">
              <text class="project-name">{{ activeProject?.name || '选择项目' }}</text>
              <view class="persona-tags">
                <view class="persona-tag" v-if="activeProject?.industry">
                  <view class="icon-target"></view>
                  <text class="tag-text">{{ activeProject.industry }}</text>
                </view>
                <view class="persona-tag" v-if="activeProject?.persona_settings?.tone">
                  <view class="icon-chat"></view>
                  <text class="tag-text">{{ activeProject.persona_settings.tone }}</text>
                </view>
              </view>
              <!-- Health Score Bar -->
              <view class="health-score">
                <view class="health-label">
                  <text class="label-text">IP活跃度</text>
                  <text class="score-value">85%</text>
                </view>
                <view class="health-progress">
                  <view class="progress-bar" style="width: 85%"></view>
                </view>
              </view>
            </view>
          </view>
          <view class="cockpit-right">
            <view class="switch-project-btn" @tap.stop="goToProjectList">
              <view class="icon-swap"></view>
              <text class="switch-text">切换项目</text>
            </view>
          </view>
        </view>
        <view class="cockpit-decoration">
          <view class="deco-grid"></view>
        </view>
      </view>

      <!-- Phase 3: Inspiration & Quick Actions (The Spark Zone) -->
      <view class="spark-zone">
        <!-- 灵感胶囊 -->
        <view class="idea-capsule">
          <view class="capsule-icon">
            <view class="icon-mic"></view>
          </view>
          <input 
            class="capsule-input"
            placeholder="记录此刻的闪念，语音转文字..."
            @focus="handleIdeaFocus"
          />
          <view class="capsule-action" @tap="handleVoiceInput">
            <view class="icon-voice"></view>
          </view>
        </view>

        <!-- 快捷创作场景 -->
        <scroll-view class="scenario-chips" scroll-x>
          <view class="chip-item" v-for="(scenario, idx) in quickScenarios" :key="idx" @tap="handleQuickScenario(scenario)">
            <view class="chip-icon" :class="scenario.iconClass">
              <view :class="scenario.icon"></view>
            </view>
            <text class="chip-text">{{ scenario.label }}</text>
          </view>
        </scroll-view>
      </view>

      <!-- Phase 4: Smart Creation Center -->
      <view class="creation-workshop-card" @tap="handleNavigate('/pages/copywriting/index')">
        <view class="workshop-header">
          <view class="workshop-icon-wrapper">
            <view class="icon-pen"></view>
          </view>
          <view class="workshop-badge">核心功能</view>
        </view>
        <view class="workshop-body">
          <text class="workshop-title">智能创作工坊</text>
          <text class="workshop-desc">深度融合 IP 人设，一键生成口播、脚本、分镜。</text>
        </view>
        <view class="workshop-visual">
          <view class="visual-grid">
            <view class="grid-item"></view>
            <view class="grid-item"></view>
            <view class="grid-item"></view>
            <view class="grid-item"></view>
          </view>
        </view>
        <view class="workshop-action">
          <view class="action-btn">
            <text class="btn-text">开始创作</text>
            <view class="icon-arrow-right"></view>
          </view>
        </view>
      </view>

      <!-- Phase 5: Intelligence & Tools (The Radar Zone) -->
      <view class="intelligence-zone">
        <!-- Left Column -->
        <view class="intel-left">
          <!-- 实时热点雷达 -->
          <view class="intel-card hotspot-radar">
            <view class="card-header">
              <view class="card-icon-wrapper icon-radar">
                <view class="icon-fire"></view>
              </view>
              <text class="card-title">实时热点雷达</text>
            </view>
            <view class="hotspot-list">
              <view 
                class="hotspot-item" 
                v-for="(hotspot, idx) in mockHotspots" 
                :key="idx"
                @tap="handleHotspotClick(hotspot)"
              >
                <view class="hotspot-rank">{{ idx + 1 }}</view>
                <view class="hotspot-content">
                  <text class="hotspot-text">{{ hotspot.title }}</text>
                  <text class="hotspot-meta">{{ hotspot.time }}</text>
                </view>
                <view class="hotspot-action">
                  <text class="action-link">蹭热点</text>
                </view>
              </view>
            </view>
          </view>

          <!-- 对标账号分析 -->
          <view class="intel-card benchmark-analysis">
            <view class="card-header">
              <view class="card-icon-wrapper icon-chart">
                <view class="icon-bar-chart"></view>
              </view>
              <text class="card-title">对标账号分析</text>
            </view>
            <view class="benchmark-chart">
              <view class="sparkline">
                <view class="sparkline-line"></view>
                <view class="sparkline-dots">
                  <view class="dot" v-for="i in 5" :key="i" :style="{ left: (i-1) * 20 + '%', bottom: [30, 50, 40, 70, 60][i-1] + '%' }"></view>
                </view>
              </view>
              <view class="chart-label">
                <text class="label-text">增长趋势</text>
                <text class="trend-text">↑ 12.5%</text>
              </view>
            </view>
          </view>
        </view>

        <!-- Right Column (Coming Soon) -->
        <view class="intel-right">
          <!-- 数字人定制 -->
          <view class="intel-card locked-card digital-human">
            <view class="locked-overlay">
              <view class="lock-icon">
                <view class="icon-lock"></view>
              </view>
              <text class="locked-text">敬请期待</text>
            </view>
            <view class="card-icon-wrapper icon-desaturated">
              <view class="icon-user"></view>
            </view>
            <text class="card-title">数字人定制</text>
            <text class="card-desc">打造专属数字形象</text>
          </view>

          <!-- 数据看板 -->
          <view class="intel-card locked-card data-dashboard">
            <view class="locked-overlay">
              <view class="lock-icon">
                <view class="icon-lock"></view>
              </view>
              <text class="locked-text">敬请期待</text>
            </view>
            <view class="card-icon-wrapper icon-desaturated">
              <view class="icon-dashboard"></view>
            </view>
            <text class="card-title">数据看板</text>
            <text class="card-desc">全方位数据洞察</text>
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

// Props
const props = defineProps<{
  isInTabBar?: boolean // 是否在 tabBar 页面中
}>()

// Emits
const emit = defineEmits<{
  switchToList: [] // 切换到列表时触发
}>()

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

// 快捷创作场景
const quickScenarios = [
  { label: '拍个Vlog', icon: 'icon-video', iconClass: 'icon-video-wrapper' },
  { label: '蹭热点', icon: 'icon-fire', iconClass: 'icon-fire-wrapper' },
  { label: '帮我润色', icon: 'icon-magic', iconClass: 'icon-magic-wrapper' },
  { label: '转第三人称', icon: 'icon-user', iconClass: 'icon-user-wrapper' }
]

// Mock热点数据
const mockHotspots = [
  { title: '小米汽车发布', time: '2小时前' },
  { title: '董宇辉新号', time: '5小时前' },
  { title: '职场35岁危机', time: '1天前' }
]

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
  // 获取 URL 参数（仅在非 tabBar 页面中）
  if (!props.isInTabBar) {
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
    
    // 如果是编辑模式，打开抽屉
    if (editMode) {
      showPersonaDrawer.value = true
    }
  }
  
  // 回填表单数据
  syncFormFromProject()
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
  // 如果在 tabBar 页面中，触发事件让父组件切换视图
  if (props.isInTabBar) {
    emit('switchToList')
  } else {
    // 不在 tabBar 页面中，正常跳转
    uni.navigateTo({ url: '/pages/project/list' })
  }
}

function handleNavigate(route: string) {
  if (!route) {
    uni.showToast({ title: '功能即将上线', icon: 'none' })
    return
  }
  uni.navigateTo({ url: route })
}

function handleIdeaFocus() {
  // 处理灵感输入框聚焦
}

function handleVoiceInput() {
  uni.showToast({ title: '语音输入功能开发中', icon: 'none' })
}

function handleQuickScenario(scenario: any) {
  if (scenario.label === '蹭热点') {
    // 可以跳转到热点页面
    return
  }
  uni.showToast({ title: `${scenario.label}功能开发中`, icon: 'none' })
}

function handleHotspotClick(hotspot: any) {
  uni.showToast({ title: `正在分析：${hotspot.title}`, icon: 'none' })
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
// CSS变量 - 品牌色
$brand-orange: #FF8800;
$brand-orange-alt: #F37021;
$brand-orange-light: rgba(255, 136, 0, 0.1);
$bg-light: #F5F7FA;

.dashboard-page {
  min-height: 100vh;
  background: $bg-light;
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
      background: radial-gradient(circle, rgba(255, 136, 0, 0.08) 0%, transparent 70%);
      top: -150rpx;
      right: -100rpx;
    }
    
    &.c2 {
      width: 300rpx;
      height: 300rpx;
      background: radial-gradient(circle, rgba(59, 130, 246, 0.06) 0%, transparent 70%);
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
  background: linear-gradient(180deg, $bg-light 0%, rgba(245, 247, 250, 0.9) 100%);
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
    }
    
    .nav-title {
      font-size: 36rpx;
      font-weight: 600;
      color: #1a1a2e;
    }
  }
  
  .nav-right {
    .settings-btn {
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
    }
  }
}

// 主滚动区域
.main-scroll {
  height: calc(100vh - 150rpx);
  padding: 0 24rpx;
}

// Phase 2: IP Cockpit Widget
.ip-cockpit-card {
  background: linear-gradient(135deg, rgba(255, 136, 0, 0.05) 0%, rgba(59, 130, 246, 0.05) 100%);
  border-radius: 24rpx;
  padding: 32rpx;
  margin-bottom: 24rpx;
  position: relative;
  overflow: hidden;
  box-shadow: 0 4rpx 24rpx rgba(0, 0, 0, 0.06);
  backdrop-filter: blur(10px);
  border: 1rpx solid rgba(255, 255, 255, 0.8);
  
  &:active {
    transform: scale(0.98);
  }
  
  .cockpit-content {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    position: relative;
    z-index: 2;
  }
  
  .cockpit-left {
    display: flex;
    gap: 20rpx;
    flex: 1;
    
    .avatar-wrapper {
      position: relative;
      flex-shrink: 0;
      
      .avatar {
        width: 120rpx;
        height: 120rpx;
        border-radius: 24rpx;
        border: 3rpx solid #fff;
        box-shadow: 0 4rpx 16rpx rgba(0, 0, 0, 0.1);
        display: flex;
        align-items: center;
        justify-content: center;
        
        .avatar-letter {
          font-size: 48rpx;
          font-weight: 700;
          color: #fff;
        }
      }
      
      .avatar-badge {
        position: absolute;
        bottom: -4rpx;
        right: -4rpx;
        width: 32rpx;
        height: 32rpx;
        background: $brand-orange;
        border-radius: 50%;
        border: 3rpx solid #fff;
      }
    }
    
    .project-info {
      flex: 1;
      
      .project-name {
        font-size: 44rpx;
        font-weight: 700;
        color: #1a1a2e;
        margin-bottom: 16rpx;
        display: block;
      }
      
      .persona-tags {
        display: flex;
        gap: 12rpx;
        flex-wrap: wrap;
        margin-bottom: 20rpx;
        
        .persona-tag {
          display: flex;
          align-items: center;
          gap: 8rpx;
          padding: 10rpx 20rpx;
          background: rgba(255, 255, 255, 0.9);
          border-radius: 24rpx;
          box-shadow: 0 2rpx 8rpx rgba(0, 0, 0, 0.04);
          
          .tag-text {
            font-size: 24rpx;
            color: #475569;
            font-weight: 500;
          }
        }
      }
      
      .health-score {
        .health-label {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 8rpx;
          
          .label-text {
            font-size: 24rpx;
            color: #64748B;
          }
          
          .score-value {
            font-size: 28rpx;
            font-weight: 600;
            color: $brand-orange;
          }
        }
        
        .health-progress {
          height: 8rpx;
          background: rgba(0, 0, 0, 0.06);
          border-radius: 4rpx;
          overflow: hidden;
          
          .progress-bar {
            height: 100%;
            background: linear-gradient(90deg, $brand-orange 0%, $brand-orange-alt 100%);
            border-radius: 4rpx;
            transition: width 0.3s ease;
          }
        }
      }
    }
  }
  
  .cockpit-right {
    .switch-project-btn {
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 8rpx;
      padding: 16rpx;
      background: rgba(255, 255, 255, 0.9);
      border-radius: 20rpx;
      box-shadow: 0 4rpx 16rpx rgba(0, 0, 0, 0.08);
      
      &:active {
        transform: scale(0.95);
      }
      
      .switch-text {
        font-size: 22rpx;
        color: #666;
      }
    }
  }
  
  .cockpit-decoration {
    position: absolute;
    top: 0;
    right: 0;
    bottom: 0;
    width: 200rpx;
    pointer-events: none;
    opacity: 0.3;
    
    .deco-grid {
      width: 100%;
      height: 100%;
      background-image: 
        linear-gradient(rgba(255, 136, 0, 0.1) 1rpx, transparent 1rpx),
        linear-gradient(90deg, rgba(255, 136, 0, 0.1) 1rpx, transparent 1rpx);
      background-size: 20rpx 20rpx;
    }
  }
}

// Phase 3: Inspiration & Quick Actions (The Spark Zone)
.spark-zone {
  margin-bottom: 24rpx;
  
  .idea-capsule {
    display: flex;
    align-items: center;
    gap: 16rpx;
    padding: 24rpx;
    background: #fff;
    border-radius: 20rpx;
    box-shadow: 0 4rpx 20rpx rgba(0, 0, 0, 0.05);
    margin-bottom: 16rpx;
    
    .capsule-icon {
      width: 48rpx;
      height: 48rpx;
      display: flex;
      align-items: center;
      justify-content: center;
      background: $brand-orange-light;
      border-radius: 12rpx;
      flex-shrink: 0;
    }
    
    .capsule-input {
      flex: 1;
      height: 48rpx;
      font-size: 28rpx;
      color: #333;
    }
    
    .capsule-action {
      width: 48rpx;
      height: 48rpx;
      display: flex;
      align-items: center;
      justify-content: center;
      background: $brand-orange-light;
      border-radius: 12rpx;
      flex-shrink: 0;
      
      &:active {
        transform: scale(0.95);
      }
    }
  }
  
  .scenario-chips {
    white-space: nowrap;
    
    .chip-item {
      display: inline-flex;
      align-items: center;
      gap: 12rpx;
      padding: 16rpx 24rpx;
      background: #fff;
      border-radius: 32rpx;
      box-shadow: 0 2rpx 12rpx rgba(0, 0, 0, 0.05);
      margin-right: 16rpx;
      
      &:active {
        transform: scale(0.95);
        background: $brand-orange-light;
      }
      
      .chip-icon {
        width: 32rpx;
        height: 32rpx;
        display: flex;
        align-items: center;
        justify-content: center;
      }
      
      .chip-text {
        font-size: 26rpx;
        color: #333;
        font-weight: 500;
      }
    }
  }
}

// Phase 4: Smart Creation Center
.creation-workshop-card {
  background: #fff;
  border-radius: 24rpx;
  padding: 32rpx;
  margin-bottom: 24rpx;
  box-shadow: 0 4rpx 24rpx rgba(0, 0, 0, 0.08);
  position: relative;
  overflow: hidden;
  
  &:active {
    transform: scale(0.98);
  }
  
  .workshop-header {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    margin-bottom: 24rpx;
    
    .workshop-icon-wrapper {
      width: 80rpx;
      height: 80rpx;
      background: linear-gradient(135deg, $brand-orange 0%, $brand-orange-alt 100%);
      border-radius: 20rpx;
      display: flex;
      align-items: center;
      justify-content: center;
      box-shadow: 0 8rpx 24rpx rgba(255, 136, 0, 0.3);
    }
    
    .workshop-badge {
      padding: 8rpx 16rpx;
      background: linear-gradient(135deg, rgba(255, 136, 0, 0.1) 0%, rgba(255, 136, 0, 0.15) 100%);
      border-radius: 16rpx;
      font-size: 22rpx;
      color: $brand-orange;
      font-weight: 600;
    }
  }
  
  .workshop-body {
    margin-bottom: 32rpx;
    
    .workshop-title {
      font-size: 40rpx;
      font-weight: 700;
      color: #1a1a2e;
      display: block;
      margin-bottom: 12rpx;
    }
    
    .workshop-desc {
      font-size: 26rpx;
      color: #64748B;
      line-height: 1.6;
      display: block;
    }
  }
  
  .workshop-visual {
    height: 160rpx;
    margin-bottom: 32rpx;
    background: linear-gradient(135deg, rgba(255, 136, 0, 0.05) 0%, rgba(59, 130, 246, 0.05) 100%);
    border-radius: 16rpx;
    display: flex;
    align-items: center;
    justify-content: center;
    position: relative;
    overflow: hidden;
    
    .visual-grid {
      display: grid;
      grid-template-columns: repeat(2, 1fr);
      grid-template-rows: repeat(2, 1fr);
      gap: 12rpx;
      width: 200rpx;
      height: 120rpx;
      
      .grid-item {
        background: rgba(255, 136, 0, 0.15);
        border-radius: 8rpx;
        border: 1rpx solid rgba(255, 136, 0, 0.2);
      }
    }
  }
  
  .workshop-action {
    .action-btn {
      width: 100%;
      height: 96rpx;
      background: linear-gradient(135deg, $brand-orange 0%, $brand-orange-alt 100%);
      border-radius: 48rpx;
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 12rpx;
      box-shadow: 0 8rpx 24rpx rgba(255, 136, 0, 0.4);
      
      &:active {
        transform: scale(0.98);
      }
      
      .btn-text {
        font-size: 32rpx;
        font-weight: 600;
        color: #fff;
      }
    }
  }
}

// Phase 5: Intelligence & Tools (The Radar Zone)
.intelligence-zone {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16rpx;
  margin-bottom: 24rpx;
  
  .intel-left {
    display: flex;
    flex-direction: column;
    gap: 16rpx;
  }
  
  .intel-right {
    display: flex;
    flex-direction: column;
    gap: 16rpx;
  }
  
  .intel-card {
    background: #fff;
    border-radius: 20rpx;
    padding: 24rpx;
    box-shadow: 0 4rpx 20rpx rgba(0, 0, 0, 0.05);
    position: relative;
    
    &.locked-card {
      opacity: 0.6;
      filter: grayscale(0.3);
    }
    
    .card-header {
      display: flex;
      align-items: center;
      gap: 12rpx;
      margin-bottom: 20rpx;
      
      .card-icon-wrapper {
        width: 56rpx;
        height: 56rpx;
        border-radius: 14rpx;
        display: flex;
        align-items: center;
        justify-content: center;
        
        &.icon-radar {
          background: linear-gradient(135deg, #EF4444 0%, #F87171 100%);
        }
        
        &.icon-chart {
          background: linear-gradient(135deg, #10B981 0%, #34D399 100%);
        }
        
        &.icon-desaturated {
          background: linear-gradient(135deg, #94A3B8 0%, #CBD5E1 100%);
        }
      }
      
      .card-title {
        font-size: 28rpx;
        font-weight: 600;
        color: #1a1a2e;
      }
    }
    
    .card-desc {
      font-size: 24rpx;
      color: #94A3B8;
      margin-top: 8rpx;
    }
    
    .locked-overlay {
      position: absolute;
      top: 0;
      left: 0;
      right: 0;
      bottom: 0;
      background: rgba(255, 255, 255, 0.9);
      border-radius: 20rpx;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      gap: 12rpx;
      z-index: 10;
      
      .lock-icon {
        width: 48rpx;
        height: 48rpx;
        display: flex;
        align-items: center;
        justify-content: center;
        background: rgba(0, 0, 0, 0.05);
        border-radius: 50%;
      }
      
      .locked-text {
        font-size: 24rpx;
        color: #94A3B8;
        font-weight: 500;
      }
    }
  }
  
  .hotspot-list {
    .hotspot-item {
      display: flex;
      align-items: center;
      gap: 12rpx;
      padding: 16rpx 0;
      border-bottom: 1rpx solid #f0f0f0;
      
      &:last-child {
        border-bottom: none;
      }
      
      &:active {
        opacity: 0.7;
      }
      
      .hotspot-rank {
        width: 40rpx;
        height: 40rpx;
        display: flex;
        align-items: center;
        justify-content: center;
        background: $brand-orange-light;
        border-radius: 8rpx;
        font-size: 24rpx;
        font-weight: 600;
        color: $brand-orange;
        flex-shrink: 0;
      }
      
      .hotspot-content {
        flex: 1;
        
        .hotspot-text {
          font-size: 26rpx;
          color: #1a1a2e;
          display: block;
          margin-bottom: 4rpx;
        }
        
        .hotspot-meta {
          font-size: 22rpx;
          color: #94A3B8;
        }
      }
      
      .hotspot-action {
        .action-link {
          font-size: 24rpx;
          color: $brand-orange;
          font-weight: 500;
        }
      }
    }
  }
  
  .benchmark-chart {
    .sparkline {
      height: 80rpx;
      position: relative;
      margin-bottom: 12rpx;
      
      .sparkline-line {
        position: absolute;
        bottom: 0;
        left: 0;
        right: 0;
        height: 2rpx;
        background: linear-gradient(90deg, transparent 0%, $brand-orange 50%, transparent 100%);
      }
      
      .sparkline-dots {
        position: relative;
        width: 100%;
        height: 100%;
        
        .dot {
          position: absolute;
          width: 8rpx;
          height: 8rpx;
          background: $brand-orange;
          border-radius: 50%;
          transform: translate(-50%, 50%);
        }
      }
    }
    
    .chart-label {
      display: flex;
      justify-content: space-between;
      align-items: center;
      
      .label-text {
        font-size: 24rpx;
        color: #64748B;
      }
      
      .trend-text {
        font-size: 26rpx;
        font-weight: 600;
        color: #10B981;
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
      background: linear-gradient(135deg, $brand-orange 0%, $brand-orange-alt 100%);
      border-radius: 48rpx;
      display: flex;
      align-items: center;
      justify-content: center;
      box-shadow: 0 8rpx 24rpx rgba(255, 136, 0, 0.4);
      
      &.loading {
        background: rgba(255, 136, 0, 0.6);
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

// ========== CSS Icons (替代 Emoji) ==========
// 箭头左
.icon-arrow-left {
  width: 24rpx;
  height: 24rpx;
  border-left: 3rpx solid #333;
  border-bottom: 3rpx solid #333;
  transform: rotate(45deg);
}

// 设置齿轮
.icon-settings {
  width: 28rpx;
  height: 28rpx;
  position: relative;
  
  &::before, &::after {
    content: '';
    position: absolute;
    width: 100%;
    height: 100%;
    border: 3rpx solid #333;
    border-radius: 50%;
  }
  
  &::before {
    border-style: solid;
    border-color: transparent transparent transparent #333;
    transform: rotate(45deg);
  }
  
  &::after {
    border-style: dashed;
    border-color: #333 transparent transparent transparent;
    transform: rotate(-45deg);
  }
}

// 交换/切换
.icon-swap {
  width: 28rpx;
  height: 28rpx;
  position: relative;
  
  &::before, &::after {
    content: '';
    position: absolute;
    width: 12rpx;
    height: 12rpx;
    border: 2rpx solid #333;
    border-top: none;
    border-right: none;
  }
  
  &::before {
    top: 4rpx;
    left: 4rpx;
    transform: rotate(45deg);
  }
  
  &::after {
    bottom: 4rpx;
    right: 4rpx;
    transform: rotate(225deg);
  }
}

// 目标/定位
.icon-target {
  width: 20rpx;
  height: 20rpx;
  border: 2rpx solid #475569;
  border-radius: 50%;
  position: relative;
  
  &::before {
    content: '';
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    width: 6rpx;
    height: 6rpx;
    background: #475569;
    border-radius: 50%;
  }
}

// 聊天
.icon-chat {
  width: 20rpx;
  height: 20rpx;
  border: 2rpx solid #475569;
  border-radius: 4rpx;
  position: relative;
  
  &::after {
    content: '';
    position: absolute;
    bottom: -4rpx;
    left: 6rpx;
    width: 0;
    height: 0;
    border-left: 4rpx solid transparent;
    border-right: 4rpx solid transparent;
    border-top: 4rpx solid #475569;
  }
}

// 麦克风
.icon-mic {
  width: 24rpx;
  height: 24rpx;
  border: 2rpx solid $brand-orange;
  border-radius: 12rpx 12rpx 0 0;
  position: relative;
  
  &::after {
    content: '';
    position: absolute;
    bottom: -8rpx;
    left: 50%;
    transform: translateX(-50%);
    width: 2rpx;
    height: 8rpx;
    background: $brand-orange;
  }
}

// 语音
.icon-voice {
  width: 24rpx;
  height: 24rpx;
  border: 2rpx solid $brand-orange;
  border-radius: 50%;
  position: relative;
  
  &::before {
    content: '';
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    width: 8rpx;
    height: 8rpx;
    background: $brand-orange;
    border-radius: 50%;
  }
}

// 视频
.icon-video {
  width: 24rpx;
  height: 24rpx;
  border: 2rpx solid $brand-orange;
  border-radius: 4rpx;
  position: relative;
  
  &::after {
    content: '';
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-30%, -50%);
    width: 0;
    height: 0;
    border-left: 8rpx solid $brand-orange;
    border-top: 5rpx solid transparent;
    border-bottom: 5rpx solid transparent;
  }
}

// 火焰/热点
.icon-fire {
  width: 20rpx;
  height: 24rpx;
  background: linear-gradient(135deg, #EF4444 0%, #F97316 100%);
  border-radius: 50% 50% 50% 50% / 60% 60% 40% 40%;
  position: relative;
  
  &::before {
    content: '';
    position: absolute;
    top: -4rpx;
    left: 50%;
    transform: translateX(-50%);
    width: 12rpx;
    height: 12rpx;
    background: linear-gradient(135deg, #F97316 0%, #FBBF24 100%);
    border-radius: 50% 50% 50% 50% / 60% 60% 40% 40%;
  }
}

// 魔法棒
.icon-magic {
  width: 24rpx;
  height: 24rpx;
  position: relative;
  
  &::before {
    content: '';
    position: absolute;
    top: 0;
    left: 8rpx;
    width: 2rpx;
    height: 16rpx;
    background: $brand-orange;
    transform: rotate(45deg);
  }
  
  &::after {
    content: '★';
    position: absolute;
    top: 12rpx;
    left: 2rpx;
    font-size: 12rpx;
    color: $brand-orange;
  }
}

// 用户
.icon-user {
  width: 20rpx;
  height: 20rpx;
  border: 2rpx solid #94A3B8;
  border-radius: 50%;
  position: relative;
  
  &::after {
    content: '';
    position: absolute;
    bottom: -8rpx;
    left: 50%;
    transform: translateX(-50%);
    width: 12rpx;
    height: 8rpx;
    border: 2rpx solid #94A3B8;
    border-top: none;
    border-radius: 0 0 8rpx 8rpx;
  }
}

// 笔/编辑
.icon-pen {
  width: 24rpx;
  height: 24rpx;
  position: relative;
  
  &::before {
    content: '';
    position: absolute;
    top: 16rpx;
    left: 4rpx;
    width: 12rpx;
    height: 2rpx;
    background: $brand-orange;
    transform: rotate(45deg);
  }
  
  &::after {
    content: '';
    position: absolute;
    top: 0;
    left: 8rpx;
    width: 2rpx;
    height: 16rpx;
    background: $brand-orange;
    transform: rotate(-45deg);
  }
}

// 箭头右
.icon-arrow-right {
  width: 24rpx;
  height: 24rpx;
  border-right: 3rpx solid #fff;
  border-top: 3rpx solid #fff;
  transform: rotate(45deg);
}

// 锁定
.icon-lock {
  width: 24rpx;
  height: 24rpx;
  border: 2rpx solid #94A3B8;
  border-radius: 4rpx;
  position: relative;
  
  &::before {
    content: '';
    position: absolute;
    top: -8rpx;
    left: 50%;
    transform: translateX(-50%);
    width: 12rpx;
    height: 8rpx;
    border: 2rpx solid #94A3B8;
    border-bottom: none;
    border-radius: 4rpx 4rpx 0 0;
  }
}

// 仪表盘
.icon-dashboard {
  width: 24rpx;
  height: 24rpx;
  border: 2rpx solid #94A3B8;
  border-radius: 4rpx;
  position: relative;
  
  &::before {
    content: '';
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    width: 2rpx;
    height: 12rpx;
    background: #94A3B8;
  }
  
  &::after {
    content: '';
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%) rotate(90deg);
    width: 2rpx;
    height: 12rpx;
    background: #94A3B8;
  }
}

// 柱状图
.icon-bar-chart {
  width: 24rpx;
  height: 24rpx;
  display: flex;
  align-items: flex-end;
  gap: 3rpx;
  
  &::before, &::after {
    content: '';
    width: 6rpx;
    background: #10B981;
    border-radius: 2rpx 2rpx 0 0;
  }
  
  &::before {
    height: 60%;
  }
  
  &::after {
    height: 100%;
  }
}

</style>
