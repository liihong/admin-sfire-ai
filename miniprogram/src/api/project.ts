/**
 * Project API - 项目相关接口
 */
import { post } from '@/utils/request'

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
  request: IPCollectRequest
): Promise<IPCollectResponse> {
  const response = await post<{
    code: number
    data: IPCollectResponse
    msg: string
  }>('/api/v1/client/projects/ai-collect', request)
  
  if (response.code === 200 && response.data) {
    return response.data
  }
  
  throw new Error(response.msg || '采集失败')
}

/**
 * AI智能填写 - IP信息压缩
 */
export async function compressIPInfo(
  request: IPCompressRequest
): Promise<IPCompressResponse> {
  const response = await post<{
    code: number
    data: IPCompressResponse
    msg: string
  }>('/api/v1/client/projects/ai-compress', request)
  
  if (response.code === 200 && response.data) {
    return response.data
  }
  
  throw new Error(response.msg || '压缩失败')
}





