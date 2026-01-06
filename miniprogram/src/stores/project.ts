/**
 * Project Store - 项目（IP）状态管理
 * 
 * 使用 Pinia 管理多项目切换和当前激活项目
 * 支持本地持久化存储
 */

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { get, post, put, del } from '@/utils/request'

// ============== 类型定义 ==============

// 人设配置类型
export interface PersonaSettings {
  tone: string
  catchphrase: string
  target_audience: string
  benchmark_accounts: string[]
  content_style: string
  taboos: string[]
  keywords: string[]
  introduction: string
}

// 项目类型
export interface Project {
  id: string
  user_id: string
  name: string
  industry: string
  avatar_letter: string
  avatar_color: string
  persona_settings: PersonaSettings
  created_at: string
  updated_at: string
  is_active: boolean
}

// 创建项目请求
export interface ProjectCreateRequest {
  name: string
  industry?: string
  persona_settings?: Partial<PersonaSettings>
}

// 更新项目请求
export interface ProjectUpdateRequest {
  name?: string
  industry?: string
  persona_settings?: Partial<PersonaSettings>
}

// 缓存 key
const ACTIVE_PROJECT_KEY = 'sfire_ai_active_project'
const PROJECT_LIST_KEY = 'sfire_ai_project_list'

// 默认人设配置
export const DEFAULT_PERSONA_SETTINGS: PersonaSettings = {
  tone: '专业亲和',
  catchphrase: '',
  target_audience: '',
  benchmark_accounts: [],
  content_style: '',
  taboos: [],
  keywords: [],
  introduction: ''
}

/**
 * Project Store
 */
export const useProjectStore = defineStore('project', () => {
  // ============== State ==============
  
  // 项目列表
  const projectList = ref<Project[]>([])
  
  // 当前激活的项目
  const activeProject = ref<Project | null>(null)
  
  // 加载状态
  const isLoading = ref(false)
  
  // 是否已初始化
  const isInitialized = ref(false)
  
  // ============== Getters ==============
  
  // 是否有激活的项目
  const hasActiveProject = computed(() => !!activeProject.value)
  
  // 项目数量
  const projectCount = computed(() => projectList.value.length)
  
  // 是否有多个项目
  const hasMultipleProjects = computed(() => projectList.value.length > 1)
  
  // 获取当前项目的人设配置
  const currentPersonaSettings = computed(() => {
    return activeProject.value?.persona_settings || DEFAULT_PERSONA_SETTINGS
  })
  
  // ============== Actions ==============
  
  /**
   * 初始化 - 从本地存储加载数据
   */
  function initialize() {
    if (isInitialized.value) return
    
    try {
      // 加载项目列表
      const storedList = uni.getStorageSync(PROJECT_LIST_KEY)
      // #region agent log
      fetch('http://127.0.0.1:7244/ingest/3bdcb60a-ce08-411e-9085-4a67fcb85719', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ location: 'project.ts:114', message: 'initialize 读取缓存', data: { hasStoredList: !!storedList }, timestamp: Date.now(), sessionId: 'debug-session', runId: 'run2', hypothesisId: 'H4' }) }).catch(() => { })
      // #endregion
      if (storedList) {
        projectList.value = JSON.parse(storedList)
      }
      
      // 加载激活项目
      const storedActive = uni.getStorageSync(ACTIVE_PROJECT_KEY)
      // #region agent log
      fetch('http://127.0.0.1:7244/ingest/3bdcb60a-ce08-411e-9085-4a67fcb85719', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ location: 'project.ts:122', message: 'initialize 读取激活项目', data: { hasStoredActive: !!storedActive }, timestamp: Date.now(), sessionId: 'debug-session', runId: 'run2', hypothesisId: 'H4' }) }).catch(() => { })
      // #endregion
      if (storedActive) {
        activeProject.value = JSON.parse(storedActive)
      }
      
      isInitialized.value = true
    } catch (error) {
      console.error('Failed to load project data:', error)
    }
  }
  
  /**
   * 保存到本地存储
   */
  function saveToStorage() {
    try {
      // #region agent log
      fetch('http://127.0.0.1:7244/ingest/3bdcb60a-ce08-411e-9085-4a67fcb85719', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ location: 'project.ts:135', message: 'saveToStorage 写入前', data: { projectListLength: projectList.value.length, hasActive: !!activeProject.value }, timestamp: Date.now(), sessionId: 'debug-session', runId: 'run2', hypothesisId: 'H1' }) }).catch(() => { })
      // #endregion
      uni.setStorageSync(PROJECT_LIST_KEY, JSON.stringify(projectList.value))
      if (activeProject.value) {
        uni.setStorageSync(ACTIVE_PROJECT_KEY, JSON.stringify(activeProject.value))
      } else {
        uni.removeStorageSync(ACTIVE_PROJECT_KEY)
      }
      // #region agent log
      fetch('http://127.0.0.1:7244/ingest/3bdcb60a-ce08-411e-9085-4a67fcb85719', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ location: 'project.ts:141', message: 'saveToStorage 写入后', data: { projectListLength: projectList.value.length, activeId: activeProject.value?.id || null }, timestamp: Date.now(), sessionId: 'debug-session', runId: 'run2', hypothesisId: 'H1' }) }).catch(() => { })
      // #endregion
    } catch (error) {
      console.error('Failed to save project data:', error)
    }
  }
  
  /**
   * 获取项目列表
   */
  async function fetchProjects(): Promise<boolean> {
    isLoading.value = true
    
    try {
      const response = await get<{
        success: boolean
        projects: Project[]
        active_project_id: string | null
      }>('/api/v1/client/projects')
      
      // #region agent log
      fetch('http://127.0.0.1:7244/ingest/3bdcb60a-ce08-411e-9085-4a67fcb85719', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ location: 'project.ts:160', message: 'fetchProjects 响应', data: { success: response.success, hasData: !!response.data, projectsLength: response.data?.projects?.length || 0, activeId: response.data?.active_project_id || null }, timestamp: Date.now(), sessionId: 'debug-session', runId: 'run2', hypothesisId: 'H2' }) }).catch(() => { })
      // #endregion

      if (response.success && response.data) {
        projectList.value = response.data.projects || []
        // #region agent log
        fetch('http://127.0.0.1:7244/ingest/3bdcb60a-ce08-411e-9085-4a67fcb85719', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ location: 'project.ts:164', message: 'fetchProjects 设置列表后', data: { projectListLength: projectList.value.length, firstProject: projectList.value[0]?.id || null }, timestamp: Date.now(), sessionId: 'debug-session', runId: 'run2', hypothesisId: 'H1' }) }).catch(() => { })
        // #endregion
        
        // 如果有激活项目 ID，找到并设置
        if (response.data.active_project_id) {
          const active = projectList.value.find(
            p => p.id === response.data!.active_project_id
          )
          if (active) {
            activeProject.value = active
          }
        } else if (projectList.value.length === 1) {
          // 如果只有一个项目，自动激活
          activeProject.value = projectList.value[0]
        }
        
        saveToStorage()
        return true
      }
      
      return false
    } catch (error) {
      console.error('Failed to fetch projects:', error)
      return false
    } finally {
      isLoading.value = false
    }
  }
  
  /**
   * 创建新项目
   */
  async function createProject(data: ProjectCreateRequest): Promise<Project | null> {
    isLoading.value = true
    
    try {
      const response = await post<{
        success: boolean
        project: Project
      }>('/api/v1/client/projects', data)
      
      if (response.success && response.data?.project) {
        const newProject = response.data.project
        projectList.value.unshift(newProject)
        
        // 如果是第一个项目，自动激活
        if (projectList.value.length === 1) {
          await setActiveProject(newProject)
        }
        
        saveToStorage()
        return newProject
      }
      
      return null
    } catch (error) {
      console.error('Failed to create project:', error)
      return null
    } finally {
      isLoading.value = false
    }
  }
  
  /**
   * 更新项目
   */
  async function updateProject(projectId: string, data: ProjectUpdateRequest): Promise<Project | null> {
    isLoading.value = true
    
    try {
      const response = await put<{
        success: boolean
        project: Project
      }>(`/api/v1/client/projects/${projectId}`, data)
      
      if (response.success && response.data?.project) {
        const updatedProject = response.data.project
        
        // 更新列表中的项目
        const index = projectList.value.findIndex(p => p.id === projectId)
        if (index !== -1) {
          projectList.value[index] = updatedProject
        }
        
        // 如果是当前激活项目，同步更新
        if (activeProject.value?.id === projectId) {
          activeProject.value = updatedProject
        }
        
        saveToStorage()
        return updatedProject
      }
      
      return null
    } catch (error) {
      console.error('Failed to update project:', error)
      return null
    } finally {
      isLoading.value = false
    }
  }
  
  /**
   * 删除项目
   */
  async function deleteProject(projectId: string): Promise<boolean> {
    isLoading.value = true
    
    try {
      const response = await del<{ success: boolean }>(`/api/v1/client/projects/${projectId}`)
      
      if (response.success) {
        // 从列表中移除
        projectList.value = projectList.value.filter(p => p.id !== projectId)
        
        // 如果删除的是当前激活项目
        if (activeProject.value?.id === projectId) {
          activeProject.value = projectList.value[0] || null
        }
        
        saveToStorage()
        return true
      }
      
      return false
    } catch (error) {
      console.error('Failed to delete project:', error)
      return false
    } finally {
      isLoading.value = false
    }
  }
  
  /**
   * 设置激活项目
   */
  async function setActiveProject(project: Project): Promise<boolean> {
    try {
      // 先更新本地状态
      activeProject.value = project
      saveToStorage()
      
      // 同步到后端
      const response = await post<{ success: boolean }>('/api/v1/client/projects/switch', {
        project_id: project.id
      })
      
      return response.success
    } catch (error) {
      console.error('Failed to switch project:', error)
      // 即使后端失败，本地状态已更新
      return true
    }
  }
  
  /**
   * 清除所有项目数据
   */
  function clearProjects() {
    projectList.value = []
    activeProject.value = null
    try {
      uni.removeStorageSync(PROJECT_LIST_KEY)
      uni.removeStorageSync(ACTIVE_PROJECT_KEY)
    } catch (error) {
      console.error('Failed to clear project data:', error)
    }
  }
  
  /**
   * 生成带有人设上下文的系统提示词
   */
  function getPersonaSystemPrompt(): string {
    if (!activeProject.value) return ''
    
    const persona = activeProject.value.persona_settings
    const parts: string[] = []
    
    parts.push(`你现在扮演的是"${activeProject.value.name}"这个IP形象。`)
    
    if (persona.introduction) {
      parts.push(`IP简介：${persona.introduction}`)
    }
    
    if (persona.tone) {
      parts.push(`语气风格：${persona.tone}`)
    }
    
    if (persona.catchphrase) {
      parts.push(`口头禅：${persona.catchphrase}`)
    }
    
    if (persona.target_audience) {
      parts.push(`目标受众：${persona.target_audience}`)
    }
    
    if (persona.content_style) {
      parts.push(`内容风格：${persona.content_style}`)
    }
    
    if (persona.keywords && persona.keywords.length > 0) {
      parts.push(`常用关键词：${persona.keywords.join('、')}`)
    }
    
    if (persona.taboos && persona.taboos.length > 0) {
      parts.push(`内容禁忌（请避免提及）：${persona.taboos.join('、')}`)
    }
    
    return parts.join('\n')
  }
  
  // 初始化
  initialize()
  
  return {
    // State
    projectList,
    activeProject,
    isLoading,
    isInitialized,
    
    // Getters
    hasActiveProject,
    projectCount,
    hasMultipleProjects,
    currentPersonaSettings,
    
    // Actions
    initialize,
    fetchProjects,
    createProject,
    updateProject,
    deleteProject,
    setActiveProject,
    clearProjects,
    getPersonaSystemPrompt,
    saveToStorage
  }
})

// ============== 行业和语气选项 ==============

export const INDUSTRY_OPTIONS = [
  '通用',
  '医疗健康',
  '教育培训',
  '金融理财',
  '科技互联网',
  '电商零售',
  '餐饮美食',
  '旅游出行',
  '房产家居',
  '美妆护肤',
  '母婴育儿',
  '体育健身',
  '娱乐影视',
  '游戏动漫',
  '法律咨询',
  '职场成长',
  '情感心理',
  '三农乡村',
  '其他'
]

export const TONE_OPTIONS = [
  '专业亲和',
  '幽默风趣',
  '严肃正式',
  '温暖治愈',
  '犀利直接',
  '娓娓道来',
  '激情澎湃',
  '冷静理性'
]


