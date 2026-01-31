/**
 * 项目数据转换工具函数
 * 
 * 负责在不同数据格式之间转换：
 * - 数据库模型（嵌套结构） ↔ 表单数据（扁平结构）
 * - 表单数据 ↔ API 请求数据
 */

import type { ProjectModel, PersonaSettingsModel, ProjectFormData } from '@/types/project'
import type { ProjectCreateRequest, ProjectUpdateRequest } from '@/api/project'

/**
 * 默认人设配置值
 */
const DEFAULT_PERSONA_SETTINGS: PersonaSettingsModel = {
  tone: '专业亲和',
  catchphrase: '',
  target_audience: '',
  introduction: '',
  keywords: [],
  industry_understanding: '',
  unique_views: '',
  target_pains: '',
  benchmark_accounts: [],
  content_style: '',
  taboos: []
}

/**
 * 将数据库模型转换为表单数据
 * 从嵌套的 persona_settings 结构转换为扁平的表单结构
 * 
 * 使用场景：编辑项目时，从 Project 模型同步数据到表单
 */
export function modelToFormData(project: ProjectModel | null): ProjectFormData {
  if (!project) {
    return getDefaultFormData()
  }

  const personaSettings = project.persona_settings || DEFAULT_PERSONA_SETTINGS

  return {
    // 项目基本信息
    name: project.name || '',
    industry: project.industry || '通用',
    
    // 人设配置（从嵌套结构提取为扁平结构）
    tone: personaSettings.tone || DEFAULT_PERSONA_SETTINGS.tone,
    catchphrase: personaSettings.catchphrase || DEFAULT_PERSONA_SETTINGS.catchphrase,
    target_audience: personaSettings.target_audience || DEFAULT_PERSONA_SETTINGS.target_audience,
    introduction: personaSettings.introduction || DEFAULT_PERSONA_SETTINGS.introduction,
    keywords: personaSettings.keywords || [...DEFAULT_PERSONA_SETTINGS.keywords],
    
    // 扩展字段
    industry_understanding: personaSettings.industry_understanding || DEFAULT_PERSONA_SETTINGS.industry_understanding,
    unique_views: personaSettings.unique_views || DEFAULT_PERSONA_SETTINGS.unique_views,
    target_pains: personaSettings.target_pains || DEFAULT_PERSONA_SETTINGS.target_pains,
    
    // 其他字段
    benchmark_accounts: personaSettings.benchmark_accounts || [...DEFAULT_PERSONA_SETTINGS.benchmark_accounts],
    content_style: personaSettings.content_style || DEFAULT_PERSONA_SETTINGS.content_style,
    taboos: personaSettings.taboos || [...DEFAULT_PERSONA_SETTINGS.taboos]
  }
}

/**
 * 将表单数据转换为创建项目请求
 * 扁平格式，后端会自动合并到 persona_settings
 * 
 * 使用场景：创建项目时，将表单数据转换为 API 请求格式
 */
export function formDataToCreateRequest(formData: ProjectFormData): ProjectCreateRequest {
  const request: ProjectCreateRequest = {
    name: formData.name.trim(),
    industry: formData.industry || undefined
  }

  // 只添加非空的人设字段（扁平格式，后端会自动合并到 persona_settings）
  if (formData.tone?.trim()) request.tone = formData.tone.trim()
  if (formData.catchphrase?.trim()) request.catchphrase = formData.catchphrase.trim()
  if (formData.target_audience?.trim()) request.target_audience = formData.target_audience.trim()
  if (formData.introduction?.trim()) request.introduction = formData.introduction.trim()
  if (formData.keywords && formData.keywords.length > 0) {
    request.keywords = formData.keywords.filter(k => k && k.trim())
  }
  
  // 扩展字段
  if (formData.industry_understanding?.trim()) {
    request.industry_understanding = formData.industry_understanding.trim()
  }
  if (formData.unique_views?.trim()) {
    request.unique_views = formData.unique_views.trim()
  }
  if (formData.target_pains?.trim()) {
    request.target_pains = formData.target_pains.trim()
  }
  
  // 其他字段
  if (formData.benchmark_accounts && formData.benchmark_accounts.length > 0) {
    request.benchmark_accounts = formData.benchmark_accounts.filter(a => a && a.trim())
  }
  if (formData.content_style?.trim()) {
    request.content_style = formData.content_style.trim()
  }
  if (formData.taboos && formData.taboos.length > 0) {
    request.taboos = formData.taboos.filter(t => t && t.trim())
  }

  return request
}

/**
 * 将表单数据转换为更新项目请求
 * 同时发送嵌套的 persona_settings 对象和扁平字段，确保数据同步更新
 * 
 * 使用场景：更新项目时，将表单数据转换为 API 请求格式
 */
export function formDataToUpdateRequest(formData: ProjectFormData): ProjectUpdateRequest {
  const request: ProjectUpdateRequest = {}

  // 项目基本信息
  if (formData.name?.trim()) request.name = formData.name.trim()
  if (formData.industry) request.industry = formData.industry

  // 构建完整的人设配置对象（嵌套格式）
  const personaSettings: PersonaSettingsModel = {
    tone: formData.tone?.trim() || '专业亲和',
    catchphrase: formData.catchphrase?.trim() || '',
    target_audience: formData.target_audience?.trim() || '',
    introduction: formData.introduction?.trim() || '',
    keywords: formData.keywords && formData.keywords.length > 0 
      ? formData.keywords.filter(k => k && k.trim()) 
      : [],
    industry_understanding: formData.industry_understanding?.trim() || '',
    unique_views: formData.unique_views?.trim() || '',
    target_pains: formData.target_pains?.trim() || '',
    benchmark_accounts: formData.benchmark_accounts && formData.benchmark_accounts.length > 0
      ? formData.benchmark_accounts.filter(a => a && a.trim())
      : [],
    content_style: formData.content_style?.trim() || '',
    taboos: formData.taboos && formData.taboos.length > 0
      ? formData.taboos.filter(t => t && t.trim())
      : []
  }
  
  // 同时发送嵌套格式的 persona_settings 对象
  request.persona_settings = personaSettings

  // 同时发送扁平格式字段（后端会合并处理，确保兼容性）
  if (formData.tone?.trim()) request.tone = formData.tone.trim()
  if (formData.catchphrase?.trim()) request.catchphrase = formData.catchphrase.trim()
  if (formData.target_audience?.trim()) request.target_audience = formData.target_audience.trim()
  if (formData.introduction?.trim()) request.introduction = formData.introduction.trim()
  if (formData.keywords && formData.keywords.length > 0) {
    request.keywords = formData.keywords.filter(k => k && k.trim())
  }
  
  // 扩展字段
  if (formData.industry_understanding?.trim()) {
    request.industry_understanding = formData.industry_understanding.trim()
  }
  if (formData.unique_views?.trim()) {
    request.unique_views = formData.unique_views.trim()
  }
  if (formData.target_pains?.trim()) {
    request.target_pains = formData.target_pains.trim()
  }
  
  // 其他字段
  if (formData.benchmark_accounts && formData.benchmark_accounts.length > 0) {
    request.benchmark_accounts = formData.benchmark_accounts.filter(a => a && a.trim())
  }
  if (formData.content_style?.trim()) {
    request.content_style = formData.content_style.trim()
  }
  if (formData.taboos && formData.taboos.length > 0) {
    request.taboos = formData.taboos.filter(t => t && t.trim())
  }

  return request
}

/**
 * 获取默认的表单数据
 */
export function getDefaultFormData(): ProjectFormData {
  return {
    name: '',
    industry: '通用',
    tone: DEFAULT_PERSONA_SETTINGS.tone,
    catchphrase: DEFAULT_PERSONA_SETTINGS.catchphrase,
    target_audience: DEFAULT_PERSONA_SETTINGS.target_audience,
    introduction: DEFAULT_PERSONA_SETTINGS.introduction,
    keywords: [...DEFAULT_PERSONA_SETTINGS.keywords],
    industry_understanding: DEFAULT_PERSONA_SETTINGS.industry_understanding,
    unique_views: DEFAULT_PERSONA_SETTINGS.unique_views,
    target_pains: DEFAULT_PERSONA_SETTINGS.target_pains,
    benchmark_accounts: [...DEFAULT_PERSONA_SETTINGS.benchmark_accounts],
    content_style: DEFAULT_PERSONA_SETTINGS.content_style,
    taboos: [...DEFAULT_PERSONA_SETTINGS.taboos]
  }
}

