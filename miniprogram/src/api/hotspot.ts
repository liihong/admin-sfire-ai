/**
 * Hotspot API - 热点榜单相关接口
 * 数据来源：Coze 工作流 API
 */
import { request } from '@/utils/request'

/**
 * 热点榜单项类型（Coze 工作流返回格式）
 */
export interface HotspotItem {
  hot: string       // 热度值
  id: string        // 热点ID
  mobileUrl: string // 移动端链接
  timestamp: string // 更新时间
  title: string     // 热点标题
  url: string       // 链接
}

/**
 * 获取抖音热点榜单
 */
export function getHotspotList() {
  return request<HotspotItem[]>({
    url: '/api/v1/client/coze/hotspot-list',
    method: 'GET',
    showLoading: true
  })
}
