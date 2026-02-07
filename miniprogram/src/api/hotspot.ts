/**
 * Hotspot API - 热点榜单相关接口
 */
import { request } from '@/utils/request'

/**
 * 热点榜单项类型
 */
export interface HotspotItem {
  rank: number  // 排名
  title: string  // 热点标题
  hot_value?: number  // 热度值
  word?: string  // 关键词
  label?: string  // 标签
  url?: string  // 链接
  update_time?: string  // 更新时间
}

/**
 * 热点榜单响应类型
 */
export interface HotspotListResponse {
  list: HotspotItem[]
  update_time?: string
}

/**
 * 获取抖音热点榜单
 * @param billboardType 榜单类型：hot-热点榜, music-音乐榜, topic-话题榜
 */
export function getHotspotList(billboardType: string = 'hot') {
  return request<HotspotListResponse>({
    url: '/api/v1/client/tikhub/hotspot-list',
    method: 'GET',
    data: {
      billboard_type: billboardType
    },
    showLoading: true
  })
}








