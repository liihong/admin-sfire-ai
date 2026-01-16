/**
 * Project API - 项目相关接口
 */
import { request } from '@/utils/request'

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

// 获取项目列表响应
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
  context?: Record<string, any>
}

// IP信息采集对话响应
export interface IPCollectResponse {
  reply: string
  next_step?: number
  collected_info?: Record<string, any>
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
    [key: string]: any
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
  
  throw new Error((response as any).msg || '采集失败')
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

// ============== 项目 CRUD 操作 ==============

/**
 * 获取项目列表
 */
export async function fetchProjects(): Promise<FetchProjectsResponse> {
  const response = await request<any>({
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

  throw new Error((response as any).msg || '获取项目列表失败')
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
  const response = await request<any>({
    url: `/api/v1/client/projects/${projectId}`,
    method: 'DELETE'
  })

  // 后端返回格式: {code: 200, data: {...}, msg: "..."}
  if (response.code === 200) {
    return true
  }

  throw new Error((response as any).msg || '删除项目失败')
}



