/**
 * Inspiration API - 灵感相关接口
 */
import { request } from '@/utils/request'

/**
 * 灵感数据类型
 */
export interface Inspiration {
  id: number
  user_id: number
  project_id?: number
  content: string
  tags: string[]
  status: 'active' | 'archived' | 'deleted'
  is_pinned: boolean
  generated_content?: string
  generated_at?: string
  created_at: string
  updated_at?: string
  project_name?: string
}

/**
 * 创建灵感请求参数
 */
export interface CreateInspirationRequest {
  content: string
  tags?: string[]
  project_id?: number
}

/**
 * 更新灵感请求参数
 */
export interface UpdateInspirationRequest {
  content?: string
  tags?: string[]
  project_id?: number
  status?: 'active' | 'archived' | 'deleted'
}

/**
 * 查询灵感列表参数
 */
export interface GetInspirationListParams {
  pageNum?: number
  pageSize?: number
  status?: 'active' | 'archived' | 'deleted'
  project_id?: number
  tag?: string
  keyword?: string
  is_pinned?: boolean
  sort_by?: string
  sort_order?: 'asc' | 'desc'
}

/**
 * 生成口播文案请求参数
 */
export interface GenerateScriptRequest {
  inspiration_id: number
  agent_type?: string
  model_type?: string
  temperature?: number
  max_tokens?: number
}

/**
 * 生成口播文案响应
 */
export interface GenerateScriptResponse {
  success: boolean
  content: string
  inspiration_id: number
  agent_type: string
  model_type: string
  input_tokens?: number
  output_tokens?: number
  cost?: number
}

/**
 * 分页响应
 */
export interface PageResponse<T> {
  code: number
  data: {
    list: T[]
    pageNum: number
    pageSize: number
    total: number
  }
  msg: string
}

/**
 * 创建灵感
 */
export async function createInspiration(data: CreateInspirationRequest): Promise<Inspiration> {
  const response = await request<{ code: number; data: Inspiration; msg: string }>({
    url: '/api/v1/client/inspirations',
    method: 'POST',
    data,
  })

  if (response.code === 200 && response.data) {
    return response.data
  }

  throw new Error(response.msg || '创建灵感失败')
}

/**
 * 获取灵感列表
 */
export async function getInspirationList(
  params: GetInspirationListParams = {}
): Promise<PageResponse<Inspiration>> {
  const response = await request<PageResponse<Inspiration>>({
    url: '/api/v1/client/inspirations',
    method: 'GET',
    data: params,
  })

  if (response.code === 200) {
    return response
  }

  throw new Error(response.msg || '获取灵感列表失败')
}

/**
 * 获取灵感详情
 */
export async function getInspirationDetail(inspirationId: number): Promise<Inspiration> {
  const response = await request<{ code: number; data: Inspiration; msg: string }>({
    url: `/api/v1/client/inspirations/${inspirationId}`,
    method: 'GET',
  })

  if (response.code === 200 && response.data) {
    return response.data
  }

  throw new Error(response.msg || '获取灵感详情失败')
}

/**
 * 更新灵感
 */
export async function updateInspiration(
  inspirationId: number,
  data: UpdateInspirationRequest
): Promise<Inspiration> {
  const response = await request<{ code: number; data: Inspiration; msg: string }>({
    url: `/api/v1/client/inspirations/${inspirationId}`,
    method: 'PUT',
    data,
  })

  if (response.code === 200 && response.data) {
    return response.data
  }

  throw new Error(response.msg || '更新灵感失败')
}

/**
 * 删除灵感
 */
export async function deleteInspiration(inspirationId: number): Promise<void> {
  const response = await request<{ code: number; msg: string }>({
    url: `/api/v1/client/inspirations/${inspirationId}`,
    method: 'DELETE',
  })

  if (response.code === 200) {
    return
  }

  throw new Error(response.msg || '删除灵感失败')
}

/**
 * 置顶/取消置顶灵感
 */
export async function pinInspiration(
  inspirationId: number,
  isPinned: boolean
): Promise<Inspiration> {
  const response = await request<{ code: number; data: Inspiration; msg: string }>({
    url: `/api/v1/client/inspirations/${inspirationId}/pin`,
    method: 'POST',
    data: { is_pinned: isPinned },
  })

  if (response.code === 200 && response.data) {
    return response.data
  }

  throw new Error(response.msg || '操作失败')
}

/**
 * 归档/取消归档灵感
 */
export async function archiveInspiration(
  inspirationId: number,
  status: 'active' | 'archived'
): Promise<Inspiration> {
  const response = await request<{ code: number; data: Inspiration; msg: string }>({
    url: `/api/v1/client/inspirations/${inspirationId}/archive`,
    method: 'POST',
    data: { status },
  })

  if (response.code === 200 && response.data) {
    return response.data
  }

  throw new Error(response.msg || '操作失败')
}

/**
 * 一键生成口播文案
 */
export async function generateScript(
  data: GenerateScriptRequest
): Promise<GenerateScriptResponse> {
  const response = await request<{
    code: number
    data: GenerateScriptResponse
    msg: string
  }>({
    url: `/api/v1/client/inspirations/${data.inspiration_id}/generate`,
    method: 'POST',
    data: {
      agent_type: data.agent_type,
      model_type: data.model_type,
      temperature: data.temperature,
      max_tokens: data.max_tokens,
    },
  })

  if (response.code === 200 && response.data) {
    return response.data
  }

  throw new Error(response.msg || '生成失败')
}

/**
 * 获取已生成的内容
 */
export async function getGeneratedContent(inspirationId: number): Promise<{
  content: string
  generated_at?: string
}> {
  const response = await request<{
    code: number
    data: {
      content: string
      generated_at?: string
    }
    msg: string
  }>({
    url: `/api/v1/client/inspirations/${inspirationId}/generated`,
    method: 'GET',
  })

  if (response.code === 200 && response.data) {
    return response.data
  }

  throw new Error(response.msg || '获取生成内容失败')
}

