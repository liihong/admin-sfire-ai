/**
 * Project Store - 项目（IP）状态管理
 * 
 * 使用 Pinia 管理多项目切换和当前激活项目
 * 激活的项目ID会持久化到本地存储
 */

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { Project, PersonaSettings, ProjectCreateRequest, ProjectUpdateRequest } from '@/api/project'

// ============== 类型导出（向后兼容） ==============
export type { Project, PersonaSettings, ProjectCreateRequest, ProjectUpdateRequest }

// localStorage key
const ACTIVE_PROJECT_ID_KEY = 'active_project_id'

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

  // ============== Helpers ==============

  /**
   * 兼容后端返回的扁平人设字段，确保每个项目都有 persona_settings
   */
  function normalizeProject(project: Project): Project {
    // 已经有 persona_settings 的直接返回
    if (project.persona_settings) return project

    const anyProject = project as any

    project.persona_settings = {
      tone: anyProject.tone || DEFAULT_PERSONA_SETTINGS.tone,
      catchphrase: anyProject.catchphrase || DEFAULT_PERSONA_SETTINGS.catchphrase,
      target_audience: anyProject.target_audience || DEFAULT_PERSONA_SETTINGS.target_audience,
      benchmark_accounts: anyProject.benchmark_accounts || [...DEFAULT_PERSONA_SETTINGS.benchmark_accounts],
      content_style: anyProject.content_style || DEFAULT_PERSONA_SETTINGS.content_style,
      taboos: anyProject.taboos || [...DEFAULT_PERSONA_SETTINGS.taboos],
      keywords: anyProject.keywords || [...DEFAULT_PERSONA_SETTINGS.keywords],
      introduction: anyProject.introduction || DEFAULT_PERSONA_SETTINGS.introduction
    }

    return project
  }

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
   * 从 localStorage 读取激活的项目ID
   */
  function getActiveProjectIdFromStorage(): string | null {
    try {
      const projectId = uni.getStorageSync(ACTIVE_PROJECT_ID_KEY)
      return projectId || null
    } catch (error) {
      console.error('Failed to get active project id from storage:', error)
      return null
    }
  }

  /**
   * 保存激活的项目ID到 localStorage
   */
  function saveActiveProjectIdToStorage(projectId: string) {
    try {
      uni.setStorageSync(ACTIVE_PROJECT_ID_KEY, projectId)
    } catch (error) {
      console.error('Failed to save active project id to storage:', error)
    }
  }

  /**
   * 清除 localStorage 中的激活项目ID
   */
  function clearActiveProjectIdFromStorage() {
    try {
      uni.removeStorageSync(ACTIVE_PROJECT_ID_KEY)
    } catch (error) {
      console.error('Failed to clear active project id from storage:', error)
    }
  }

  /**
   * 设置项目列表（由 API 调用后更新）
   */
  function setProjectList(projects: Project[], activeProjectId?: string | number) {
    // 统一归一化项目结构
    projectList.value = projects.map(p => normalizeProject(p))

  // 如果有激活项目 ID，找到并设置
    if (activeProjectId) {
      const active = projectList.value.find(
        p => p.id === String(activeProjectId)
      )
      if (active) {
        activeProject.value = active
        saveActiveProjectIdToStorage(active.id)
      }
    } else {
      // 如果没有传入 activeProjectId，尝试从 localStorage 读取
      const storedProjectId = getActiveProjectIdFromStorage()
      if (storedProjectId) {
        const active = projectList.value.find(
          p => p.id === storedProjectId
        )
        if (active) {
          activeProject.value = active
        } else {
          // 如果存储的项目ID不存在于列表中，清除存储
          clearActiveProjectIdFromStorage()
        }
      }
      
      // 如果还是没有激活项目，且只有一个项目，自动激活
      if (!activeProject.value && projectList.value.length === 1) {
        activeProject.value = projectList.value[0]
        saveActiveProjectIdToStorage(projectList.value[0].id)
      }
    }
  }

  /**
   * 添加或更新项目到列表
   */
  function upsertProject(project: Project) {
    const normalized = normalizeProject(project)
    const index = projectList.value.findIndex(p => p.id === normalized.id)
    if (index >= 0) {
      projectList.value[index] = normalized
    } else {
      projectList.value.push(normalized)
    }
  }

  /**
   * 从列表中移除项目
   */
  function removeProject(projectId: string) {
    const index = projectList.value.findIndex(p => p.id === projectId)
    if (index >= 0) {
      projectList.value.splice(index, 1)
      // 如果删除的是当前激活的项目，清空激活状态
      if (activeProject.value?.id === projectId) {
        activeProject.value = null
        clearActiveProjectIdFromStorage()
      }
    }
  }

  /**
   * 设置激活项目（更新本地状态并保存到 localStorage）
   */
  function setActiveProjectLocal(project: Project) {
    const normalized = normalizeProject(project)
    activeProject.value = normalized
    saveActiveProjectIdToStorage(normalized.id)
  }

  /**
   * 清除所有项目数据（清空内存状态和本地存储）
   */
  function clearProjects() {
    projectList.value = []
    activeProject.value = null
    clearActiveProjectIdFromStorage()
  }

  /**
   * 设置加载状态
   */
  function setLoading(loading: boolean) {
    isLoading.value = loading
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

  return {
    // State
    projectList,
    activeProject,
    isLoading,
    
    // Getters
    hasActiveProject,
    projectCount,
    hasMultipleProjects,
    currentPersonaSettings,
    
    // Actions
    setProjectList,
    upsertProject,
    removeProject,
    setActiveProjectLocal,
    clearProjects,
    setLoading,
    getPersonaSystemPrompt
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


