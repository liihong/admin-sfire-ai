/**
 * Project Store - 多项目与激活项目
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { Project, PersonaSettings } from '@/types/project'
import type { ProjectCreateRequest, ProjectUpdateRequest, IPCollectFormData } from '@/api/project'
import { storage } from '@/utils/storage'

export type { Project, PersonaSettings } from '@/types/project'
export type { ProjectCreateRequest, ProjectUpdateRequest, IPCollectFormData } from '@/api/project'

const ACTIVE_PROJECT_ID_KEY = 'active_project_id'
const IP_COLLECT_FORM_DATA_KEY = 'ip_collect_form_data'

export const DEFAULT_PERSONA_SETTINGS: PersonaSettings = {
  ip_name: '',
  ip_age: '',
  ip_city: '',
  ip_industry: '',
  ip_identityTag: '',
  ip_experience: '',
  cl_mainProducts: '',
  cl_targetPopulation: '',
  cl_painPoints: '',
  cl_advantages: '',
  cl_feedback: '',
  style_tones: '专业亲和',
  style_mantra: '',
  keywords: []
}

export const DEFAULT_INDUSTRY = '通用'

export const INDUSTRY_OPTIONS = [
  '通用', '医疗健康', '教育培训', '金融理财', '科技互联网', '电商零售', '餐饮美食',
  '旅游出行', '房产家居', '美妆护肤', '母婴育儿', '体育健身', '娱乐影视', '游戏动漫',
  '法律咨询', '职场成长', '情感心理', '三农乡村', '其他'
]

export const TONE_OPTIONS = [
  '专业亲和', '幽默风趣', '严肃正式', '温暖治愈', '犀利直接', '娓娓道来', '激情澎湃', '冷静理性'
]

function normalizeProject(project: Project): Project {
  const ps = project.persona_settings
  if (!ps) {
    project.persona_settings = {
      ...DEFAULT_PERSONA_SETTINGS,
      ip_name: project.name || '',
      ip_industry: project.industry || DEFAULT_INDUSTRY
    }
    return project
  }
  project.persona_settings = {
    ...DEFAULT_PERSONA_SETTINGS,
    ...ps,
    ip_name: ps.ip_name || project.name || '',
    ip_industry: ps.ip_industry || project.industry || DEFAULT_INDUSTRY,
    keywords: Array.isArray(ps.keywords) ? [...ps.keywords] : []
  }
  return project
}

export const useProjectStore = defineStore('project', () => {
  const projectList = ref<Project[]>([])
  const activeProject = ref<Project | null>(null)
  const isLoading = ref(false)
  const needRefresh = ref(false)
  const needRefreshConversation = ref(false)
  const isManuallyCleared = ref(false)
  const ipCollectFormData = ref<IPCollectFormData | null>(null)

  const hasActiveProject = computed(() => !!activeProject.value)
  const projectCount = computed(() => projectList.value.length)
  const hasMultipleProjects = computed(() => projectList.value.length > 1)
  const currentPersonaSettings = computed(
    () => activeProject.value?.persona_settings || DEFAULT_PERSONA_SETTINGS
  )

  function getActiveProjectIdFromStorage(): string | null {
    return storage.get<string>(ACTIVE_PROJECT_ID_KEY) || null
  }

  function saveActiveProjectIdToStorage(projectId: string) {
    storage.set(ACTIVE_PROJECT_ID_KEY, projectId)
  }

  function clearActiveProjectIdFromStorage() {
    storage.remove(ACTIVE_PROJECT_ID_KEY)
  }

  function setProjectList(projects: Project[], activeProjectId?: string | number) {
    projectList.value = projects.map(p => normalizeProject(p))

    if (isManuallyCleared.value) {
      isManuallyCleared.value = false
      return
    }

    if (activeProjectId !== undefined && activeProjectId !== null && activeProjectId !== '') {
      const aid = String(activeProjectId)
      const active = projectList.value.find(p => String(p.id) === aid)
      if (active) {
        activeProject.value = active
        saveActiveProjectIdToStorage(String(active.id))
      }
      return
    }

    const storedId = getActiveProjectIdFromStorage()
    if (storedId) {
      const active = projectList.value.find(p => String(p.id) === storedId)
      if (active) {
        activeProject.value = active
      } else {
        clearActiveProjectIdFromStorage()
      }
    }

    if (!activeProject.value && projectList.value.length === 1) {
      const only = projectList.value[0]
      activeProject.value = only
      saveActiveProjectIdToStorage(String(only.id))
    }
  }

  function upsertProject(project: Project) {
    const normalized = normalizeProject(project)
    const index = projectList.value.findIndex(p => String(p.id) === String(normalized.id))
    if (index >= 0) {
      projectList.value[index] = normalized
    } else {
      projectList.value.push(normalized)
    }
  }

  function removeProject(projectId: string) {
    const index = projectList.value.findIndex(p => String(p.id) === projectId)
    if (index >= 0) {
      projectList.value.splice(index, 1)
      if (activeProject.value && String(activeProject.value.id) === projectId) {
        activeProject.value = null
        clearActiveProjectIdFromStorage()
      }
    }
  }

  function setActiveProjectLocal(project: Project) {
    const normalized = normalizeProject(project)
    activeProject.value = normalized
    saveActiveProjectIdToStorage(String(normalized.id))
  }

  function clearActiveProject() {
    activeProject.value = null
    clearActiveProjectIdFromStorage()
    isManuallyCleared.value = true
  }

  function clearProjects() {
    projectList.value = []
    activeProject.value = null
    clearActiveProjectIdFromStorage()
  }

  function setLoading(loading: boolean) {
    isLoading.value = loading
  }

  function setNeedRefresh(need: boolean) {
    needRefresh.value = need
  }

  function checkAndClearRefresh(): boolean {
    if (needRefresh.value) {
      needRefresh.value = false
      return true
    }
    return false
  }

  function setNeedRefreshConversation(need: boolean) {
    needRefreshConversation.value = need
  }

  function checkAndClearConversationRefresh(): boolean {
    if (needRefreshConversation.value) {
      needRefreshConversation.value = false
      return true
    }
    return false
  }

  function getPersonaSystemPrompt(): string {
    if (!activeProject.value) return ''
    const persona = activeProject.value.persona_settings
    const parts: string[] = []
    parts.push(`你现在扮演的是「${activeProject.value.name}」这个IP形象。`)
    if (persona.ip_experience) parts.push(`经历介绍：${persona.ip_experience}`)
    if (persona.style_tones) parts.push(`语气风格：${persona.style_tones}`)
    if (persona.style_mantra) parts.push(`个人口头禅：${persona.style_mantra}`)
    if (persona.cl_targetPopulation) parts.push(`目标人群：${persona.cl_targetPopulation}`)
    if (persona.keywords?.length) parts.push(`关键词：${persona.keywords.join('、')}`)
    return parts.join('\n')
  }

  function saveIPCollectFormData(data: IPCollectFormData) {
    ipCollectFormData.value = data
    storage.set(IP_COLLECT_FORM_DATA_KEY, data)
  }

  function loadIPCollectFormData(): IPCollectFormData | null {
    const stored = storage.get<IPCollectFormData>(IP_COLLECT_FORM_DATA_KEY)
    if (stored) {
      ipCollectFormData.value = stored
      return stored
    }
    ipCollectFormData.value = null
    return null
  }

  function hasIPCollectFormData(): boolean {
    return storage.has(IP_COLLECT_FORM_DATA_KEY)
  }

  function clearIPCollectFormData() {
    ipCollectFormData.value = null
    storage.remove(IP_COLLECT_FORM_DATA_KEY)
  }

  return {
    projectList,
    activeProject,
    isLoading,
    needRefresh,
    needRefreshConversation,
    isManuallyCleared,
    ipCollectFormData,
    hasActiveProject,
    projectCount,
    hasMultipleProjects,
    currentPersonaSettings,
    getActiveProjectIdFromStorage,
    saveActiveProjectIdToStorage,
    clearActiveProjectIdFromStorage,
    setProjectList,
    upsertProject,
    removeProject,
    setActiveProjectLocal,
    clearActiveProject,
    clearProjects,
    setLoading,
    setNeedRefresh,
    checkAndClearRefresh,
    setNeedRefreshConversation,
    checkAndClearConversationRefresh,
    getPersonaSystemPrompt,
    saveIPCollectFormData,
    loadIPCollectFormData,
    hasIPCollectFormData,
    clearIPCollectFormData
  }
})
