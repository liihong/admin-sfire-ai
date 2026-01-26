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
  icon_class: string
  bg_color: string | null
  action_type: 'agent' | 'skill' | 'prompt'
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
 */
export function getQuickEntries(type?: 'category' | 'command') {
  let url = '/api/v1/client/quick-entries'
  if (type) {
    url += `?type=${type}`
  }
  return request<QuickEntryListResponse>({
    url,
    method: 'GET',
    showLoading: false
  })
}

