/**
 * Project API - 项目相关接口
 * 
 * 只保留 API 调用函数和请求/响应类型
 * 业务类型定义在 types/project.ts 中
 */
import { request } from '@/utils/request'
import type { Project, PersonaSettings } from '@/types/project'

// ============== API 请求/响应类型 ==============

/**
 * 创建项目请求（扁平格式，后端会自动合并到 persona_settings）
 */
export interface ProjectCreateRequest {
  name: string
  industry?: string
  // 人设字段（扁平格式，后端会自动合并到 persona_settings）
  tone?: string
  catchphrase?: string
  target_audience?: string
  introduction?: string
  keywords?: string[]
  industry_understanding?: string
  unique_views?: string
  target_pains?: string
  benchmark_accounts?: string[]
  content_style?: string
  taboos?: string[]
}

/**
 * 更新项目请求（扁平格式，后端会自动合并到 persona_settings）
 */
export interface ProjectUpdateRequest {
  name?: string
  industry?: string
  avatar_letter?: string
  avatar_color?: string
  // 人设字段（扁平格式，后端会自动合并到 persona_settings）
  tone?: string
  catchphrase?: string
  target_audience?: string
  introduction?: string
  keywords?: string[]
  industry_understanding?: string
  unique_views?: string
  target_pains?: string
  benchmark_accounts?: string[]
  content_style?: string
  taboos?: string[]
}

/**
 * 获取项目列表响应
 */
export interface FetchProjectsResponse {
  success: boolean
  projects: Project[]
  active_project_id?: string | number
}

// IP信息采集对话请求
export interface IPCollectRequest {
  messages: Array<{
    role: 'user' | 'assistant'
    content: string
  }>
  step?: number
  context?: Record<string, unknown>
}

// IP信息采集对话响应
export interface IPCollectResponse {
  reply: string
  next_step?: number
  collected_info?: Record<string, unknown>
  is_complete: boolean
}

// IP信息压缩请求
export interface IPCompressRequest {
  raw_info: {
    name?: string
    industry?: string
    introduction?: string
    tone?: string
    target_audience?: string
    catchphrase?: string
    keywords?: string[]
    [key: string]: unknown
  }
}

// IP信息压缩响应
export interface IPCompressResponse {
  compressed_info: {
    name: string
    industry: string
    introduction: string
    tone: string
    target_audience: string
    catchphrase: string
    keywords: string[]
  }
}

// IP定位报告生成请求
export interface IPReportRequest {
  name: string
  industry: string
  introduction?: string
  tone?: string
  target_audience?: string
  target_pains?: string
  keywords?: string[]
  industry_understanding?: string
  unique_views?: string
  catchphrase?: string
}

// IP定位报告内容
export interface IPReportContentMoat {
  insight: string  // 反共识洞察
  emotional_hook: string  // 情感钩子
}

export interface IPReportLanguageFingerprint {
  tone_modeling: string  // 语感建模
  atmosphere: string  // 标志性氛围
}

export interface IPReportBusinessPotential {
  viral_potential: string  // 爆款潜质
  red_lines: string  // 人设红线
}

export interface IPReportData {
  name: string
  persona_tags: string[]  // 人格标签
  core_archetype: string  // 核心原型
  one_line_intro: string  // 一句话简介
  content_moat: IPReportContentMoat
  language_fingerprint: IPReportLanguageFingerprint
  business_potential: IPReportBusinessPotential
  expert_message: string  // 专家寄语
}

// IP定位报告响应
export interface IPReportResponse {
  report: IPReportData
  score: number  // IP数字化程度评分（0-100）
  score_reason: string  // 评分理由
}

// IPCollectFormData 类型定义已移至 types/project.ts
// 这里重新导出以保持向后兼容
export type { IPCollectFormData } from '@/types/project'

/**
 * AI智能填写 - IP信息采集对话
 */
export async function aiCollectIPInfo(
  requestParams: IPCollectRequest
): Promise<IPCollectResponse> {
  const response = await request<IPCollectResponse>({
    url: '/api/v1/client/projects/ai-collect',
    method: 'POST',
    data: requestParams
  })
  
  // 后端返回格式: {code: 200, data: IPCollectResponse, msg: "..."}
  if (response.code === 200 && response.data) {
    return response.data as IPCollectResponse
  }
  
  throw new Error(response.msg || '采集失败')
}

/**
 * AI智能填写 - IP信息压缩
 */
export async function compressIPInfo(
  requestParams: IPCompressRequest
): Promise<IPCompressResponse> {
  const response = await request<IPCompressResponse>({
    url: '/api/v1/client/projects/ai-compress',
    method: 'POST',
    data: requestParams
  })

  // 后端返回格式: {code: 200, data: IPCompressResponse, msg: "..."}
  if (response.code === 200 && response.data) {
    return response.data as IPCompressResponse
  }

  throw new Error((response as any).msg || '压缩失败')
}

/**
 * 生成IP定位报告
 */
export async function generateIPReport(
  requestParams: IPReportRequest
): Promise<IPReportResponse> {
  const response = await request<IPReportResponse>({
    url: '/api/v1/client/projects/generate-ip-report',
    method: 'POST',
    data: requestParams
  })

  // 后端返回格式: {code: 200, data: IPReportResponse, msg: "..."}
  if (response.code === 200 && response.data) {
    return response.data
  }

  throw new Error((response as any).msg || 'IP定位报告生成失败')
}

// ============== 项目 CRUD 操作 ==============

/**
 * 获取项目列表
 */
export async function fetchProjects(): Promise<FetchProjectsResponse> {
  interface ProjectsResponseData {
    projects: Project[]
    active_project_id?: string | number
  }

  const response = await request<ProjectsResponseData>({
    url: '/api/v1/client/projects',
    method: 'GET'
  })

  // 后端返回格式: {code: 200, data: {projects: [...], active_project_id: ...}, msg: "..."}
  if (response.code === 200 && response.data) {
    const apiData = response.data
    return {
      success: true,
      projects: apiData.projects || [],
      active_project_id: apiData.active_project_id
    }
  }

  throw new Error(response.msg || '获取项目列表失败')
}

/**
 * 创建新项目
 */
export async function createProject(data: ProjectCreateRequest): Promise<Project> {
  const response = await request<Project>({
    url: '/api/v1/client/projects',
    method: 'POST',
    data
  })

  // 后端返回格式: {code: 200, data: {...}, msg: "..."}
  if (response.code === 200 && response.data) {
    return response.data as Project
  }

  throw new Error((response as any).msg || '创建项目失败')
}

/**
 * 更新项目
 */
export async function updateProject(projectId: string, data: ProjectUpdateRequest): Promise<Project> {
  const response = await request<Project>({
    url: `/api/v1/client/projects/${projectId}`,
    method: 'PUT',
    data
  })
  // 后端返回格式: {code: 200, data: {...}, msg: "..."}
  if (response.code === 200 && response.data) {
    return response.data as Project
  }

  throw new Error((response as any).msg || '更新项目失败')
}

/**
 * 删除项目
 */
export async function deleteProject(projectId: string): Promise<boolean> {
  const response = await request<unknown>({
    url: `/api/v1/client/projects/${projectId}`,
    method: 'DELETE'
  })

  // 后端返回格式: {code: 200, data: {...}, msg: "..."}
  if (response.code === 200) {
    return true
  }

  throw new Error(response.msg || '删除项目失败')
}

// ============== 字典选项 ==============

export interface DictOption {
  label: string
  value: string
}

export interface ProjectOptionsResponse {
  success: boolean
  industries: DictOption[]
  tones: DictOption[]
}

/**
 * 获取项目配置选项（行业赛道和语气风格）
 */
export async function getProjectOptions(): Promise<ProjectOptionsResponse> {
  const response = await request<ProjectOptionsResponse>({
    url: '/api/v1/client/projects/options',
    method: 'GET'
  })

  // 后端返回格式: {code: 200, data: {success, industries, tones}, msg: "..."}
  if (response.code === 200 && response.data) {
    return response.data as ProjectOptionsResponse
  }

  throw new Error((response as any).msg || '获取选项失败')
}













