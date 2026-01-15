/**
 * Generate API - 生成内容相关接口
 */
import { request } from '@/utils/request'

/**
 * 生成请求参数类型
 */
export interface GenerateRequest {
  project_id?: number
  agent_type?: string
  messages: Array<{role: string, content: string}>
  model_type?: string
  temperature?: number
  max_tokens?: number
  stream?: boolean
}

/**
 * 生成响应类型
 */
export interface GenerateResponse {
  success: boolean
  content: string
  agent_type: string
  model_type: string
}

/**
 * 快速文案生成请求参数类型
 */
export interface CopywritingRequest {
  content: string
  agent_type?: string
  project_id?: number
  model_type?: string
}

/**
 * 快速文案生成响应类型
 */
export interface CopywritingResponse {
  success: boolean
  content: string
  agent_type: string
  model_type: string
}

/**
 * 通用生成接口（对话式创作）
 */
export function generate(params: GenerateRequest) {
  return request<GenerateResponse>({
    url: '/api/v1/client/creation/chat',
    method: 'POST',
    data: {
      project_id: params.project_id,
      agent_type: params.agent_type || 'efficient_oral',
      messages: params.messages,
      model_type: params.model_type || 'deepseek',
      temperature: params.temperature,
      max_tokens: params.max_tokens || 2048,
      stream: params.stream !== false
    },
    showLoading: true,
    loadingText: 'AI 生成中...'
  })
}

/**
 * 快速文案生成
 */
export function copywriting(params: CopywritingRequest) {
  const queryParams = new URLSearchParams()
  queryParams.append('content', params.content)
  if (params.agent_type) queryParams.append('agent_type', params.agent_type)
  if (params.project_id) queryParams.append('project_id', String(params.project_id))
  if (params.model_type) queryParams.append('model_type', params.model_type)
  
  return request<CopywritingResponse>({
    url: `/api/v1/client/creation/chat/quick?${queryParams.toString()}`,
    method: 'POST',
    data: null,
    showLoading: true
  })
}

