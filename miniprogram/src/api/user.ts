/**
 * User API - 用户相关接口
 */
import { request } from '@/utils/request'

/**
 * 用户信息响应类型（我的页面使用）
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
 * 认证用户信息类型（登录返回）
 */
export interface AuthUserInfo {
  openid: string
  nickname: string
  avatarUrl: string
  gender?: number
  city?: string
  province?: string
  country?: string
}

/**
 * 登录请求类型
 */
export interface LoginRequest {
  code: string
}

/**
 * 登录响应类型
 */
export interface LoginResponse {
  token: string
  refreshToken?: string
  userInfo?: AuthUserInfo
}

/**
 * 刷新Token请求类型
 */
export interface RefreshTokenRequest {
  refreshToken: string
}

/**
 * 刷新Token响应类型
 */
export interface RefreshTokenResponse {
  token: string
  refreshToken?: string
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

/**
 * 使用 code 登录
 * @param code 微信登录 code
 */
export function loginWithCode(code: string) {
  return request<LoginResponse>({
    url: '/api/v1/client/auth/login',
    method: 'POST',
    data: { code },
    needToken: false, // 登录接口不需要 token
    showLoading: false
  })
}

/**
 * 刷新 Access Token
 * @param refreshToken 刷新 token
 */
export function refreshAccessToken(refreshToken: string) {
  return request<RefreshTokenResponse>({
    url: '/api/v1/client/auth/refresh',
    method: 'POST',
    data: { refreshToken },
    needToken: false, // 刷新 token 接口不需要 access_token
    showLoading: false
  })
}

/**
 * 获取当前用户信息（用于刷新用户信息）
 */
export function getCurrentUserInfo() {
  return request<{ userInfo: AuthUserInfo }>({
    url: '/api/v1/client/auth/user',
    method: 'GET',
    showLoading: false
  })
}
