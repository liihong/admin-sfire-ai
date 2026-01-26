/**
 * Agent API - 智能体相关接口
 */
import { request } from '@/utils/request'

/**
 * 智能体信息类型
 */
export interface Agent {
  type: string
  id: string
  name: string
  icon: string
  description: string
}

/**
 * 智能体列表响应类型
 */
export interface AgentListResponse {
  success: boolean
  agents: Agent[]
}

/**
 * 获取智能体列表
 */
export function getAgentList() {
  return request<AgentListResponse>({
    url: '/api/v1/client/agents',
    method: 'GET',
    showLoading: false
  })
}

/**
 * 智能体详情响应类型（仅基本信息，不包含 system_prompt）
 */
export interface AgentDetailResponse {
  code: number
  data: {
    id: string
    name: string
    icon: string
    description: string
  }
  msg: string
}

