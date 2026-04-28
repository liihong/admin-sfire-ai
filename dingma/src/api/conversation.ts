/**
 * Conversation API - 对话会话相关接口
 */
import { request } from '@/utils/request'

/**
 * 对话消息类型
 */
export interface ConversationMessage {
  id: number
  conversation_id: number
  role: 'user' | 'assistant' | 'system'
  content: string
  tokens: number
  sequence: number
  embedding_status: string
  status: string
  error_message?: string
  created_at: string
  updated_at?: string
}

/**
 * 对话会话类型
 */
export interface Conversation {
  id: number
  user_id: number
  agent_id?: number
  project_id?: number
  title: string
  model_type: string
  total_tokens: number
  message_count: number
  status: 'active' | 'archived'
  created_at: string
  updated_at?: string
  // 关联信息（从详情接口返回）
  agent_name?: string
  project_name?: string
}

/**
 * 对话详情类型（包含消息列表）
 */
export interface ConversationDetail extends Conversation {
  messages: ConversationMessage[]
}

/**
 * 获取对话列表请求参数
 */
export interface GetConversationListParams {
  pageNum?: number
  pageSize?: number
  status?: 'active' | 'archived'
  agent_id?: number
  project_id?: number
  keyword?: string
}

/**
 * 分页响应类型
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
 * 获取对话列表
 */
export async function getConversationList(
  params: GetConversationListParams = {}
): Promise<PageResponse<Conversation>> {
  const { pageNum = 1, pageSize = 10, ...restParams } = params
  
  // 构建查询参数对象（小程序环境不支持 URLSearchParams，使用对象方式）
  // request 工具会自动将 GET 请求的 data 转换为查询参数
  const queryData: Record<string, string | number> = {
    pageNum,
    pageSize,
  }
  
  // 添加其他参数
  Object.entries(restParams).forEach(([key, value]) => {
    if (value !== undefined && value !== null) {
      queryData[key] = value
    }
  })

  const response = await request<PageResponse<Conversation>>({
    url: '/api/v1/client/conversations',
    method: 'GET',
    data: queryData,
    showLoading: false,
  })

  if (response.code === 200) {
    return response
  }

  throw new Error(response.msg || '获取对话列表失败')
}

/**
 * 获取对话详情（包含消息列表）
 */
export async function getConversationDetail(
  conversationId: number
): Promise<ConversationDetail> {
  const response = await request<{ code: number; data: ConversationDetail; msg: string }>({
    url: `/api/v1/client/conversations/${conversationId}`,
    method: 'GET',
    showLoading: true,
    loadingText: '加载对话中...',
  })

  if (response.code === 200 && response.data) {
    return response.data
  }

  throw new Error(response.msg || '获取对话详情失败')
}

