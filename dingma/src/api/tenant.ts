/**
 * 租户公开配置 API
 */
import { request } from '@/utils/request'

export interface TenantPublicConfig {
  /** 是否开启上线审查；开启时「我的」页隐藏「查看会员权益」 */
  release_review_enabled: boolean
}

/** 获取当前租户公开配置（无需登录） */
export function getTenantPublicConfig() {
  return request<TenantPublicConfig>({
    url: '/api/v1/client/tenant/config',
    method: 'GET'
  })
}
