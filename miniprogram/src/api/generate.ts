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
 * 聊天请求参数类型
 */
export interface ChatRequest {
    agent_type: string
    conversation_id?: number
    messages: Array<{ role: string, content: string }>
    project_id?: number
    stream: boolean
}

/**
 * 聊天响应数据类型（response.data 的类型）
 */
export interface ChatResponseData {
    content?: string
    conversation_id?: number
    [key: string]: any
}

/**
 * 聊天接口（对话式创作）
 */
export function chat(params: ChatRequest) {
    return request<ChatResponseData>({
        url: '/api/v1/client/chat',
        method: 'POST',
        data: {
            agent_type: params.agent_type,
            conversation_id: params.conversation_id,
            messages: params.messages,
            project_id: params.project_id,
            stream: params.stream
        },
        loadingText: 'AI 生成中...'
    })
}

