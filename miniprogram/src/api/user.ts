/**
 * User API - 用户相关接口
 */
import { request } from '@/utils/request'

/**
 * 用户信息响应类型
 */
export interface UserInfo {
  phone: string
  avatar: string
  nickname: string
  power: string
  partnerBalance: string
  partnerStatus: string
  expireDate: string | null
}

/**
 * 更新用户信息请求类型
 */
export interface UpdateUserInfoRequest {
  nickname?: string
  avatar?: string
}

/**
 * 更新用户信息响应类型
 */
export interface UpdateUserInfoResponse {
  success: boolean
  userInfo: {
    openid: string
    nickname: string
    avatarUrl: string
  }
}

/**
 * 获取用户详细信息（我的页面使用）
 */
export function getUserInfo() {
  return request<UserInfo>({
    url: '/api/v1/client/auth/user/info',
    method: 'GET',
    showLoading: false
  })
}

/**
 * 更新用户信息
 */
export function updateUserInfo(data: UpdateUserInfoRequest) {
  return request<UpdateUserInfoResponse>({
    url: '/api/v1/client/auth/user',
    method: 'PUT',
    data,
    showLoading: true,
    loadingText: '更新中...'
  })
}

