/**
 * Quick Entry API - 快捷入口相关接口
 */
import { request } from '@/utils/request'

/**
 * 快捷入口信息类型
 */
export interface QuickEntry {
  id: number
  unique_key: string
  type: 'category' | 'command'
  title: string
  subtitle: string | null
  instructions: string | null
  agent_type: string | null
  /** Agent类型对应的字典名称（sys_dict id=3） */
  agent_type_name: string | null
  icon_class: string
  bg_color: string | null
  action_type: 'agent' | 'skill' | 'prompt' | 'url'
  action_value: string
  tag: 'none' | 'new' | 'hot'
  priority: number
  status: number
  created_at: string | null
  updated_at: string | null
}

/**
 * 快捷入口列表响应类型
 */
export interface QuickEntryListResponse {
  entries: QuickEntry[]
}

/**
 * 获取快捷入口列表
 * @param type 入口类型筛选（category-今天拍点啥, command-快捷指令库）
 * @param agentType Agent类型筛选（关联sys_dict id=3的字典项）
 */
export function getQuickEntries(type?: 'category' | 'command', agentType?: string) {
  const params: string[] = []
  if (type) params.push(`type=${encodeURIComponent(type)}`)
  if (agentType) params.push(`agent_type=${encodeURIComponent(agentType)}`)
  const query = params.join('&')
  const url = query ? `/api/v1/client/quick-entries?${query}` : '/api/v1/client/quick-entries'
  return request<QuickEntryListResponse>({
    url,
    method: 'GET',
    showLoading: false,
    // 公开列表，勿携带可能过期的 JWT，避免网关/中间层对无效 Bearer 返回 401
    needToken: false
  })
}

