/**
 * User API - 用户相关接口
 */
import { request } from '@/utils/request'
import { useAuthStore } from '@/stores/auth'

/**
 * 用户等级信息类型
 */
export interface UserLevelInfo {
  code: string  // 等级代码：normal/vip/svip/max
  name: string  // 等级名称（中文显示）
  max_ip_count: number | null  // 最大IP数量（null表示不限制）
  ip_type: string  // IP类型：temporary/permanent
  daily_tokens_limit: number | null  // 每日AI能量限制（null表示无限制）
  can_use_advanced_agent: boolean  // 是否可使用高级智能体
  unlimited_conversations: boolean  // 是否无限制对话
}

/**
 * 认证用户信息类型（完整用户信息）
 */
export interface AuthUserInfo {
  openid: string
  nickname: string
  avatarUrl: string
  avatar?: string  // 兼容字段，与 avatarUrl 相同
  phone?: string
  gender?: number
  city?: string
  province?: string
  country?: string
  // 等级相关字段
  level: string  // 用户等级代码：normal/vip/svip/max
  level_code?: string
  level_name?: string
  levelInfo?: UserLevelInfo | null
  // 余额相关字段
  power?: string  // 算力可用余额（总余额-冻结余额）
  total_balance?: string  // 算力总余额
  frozen_balance?: string  // 冻结算力余额
  partner_balance?: string
  partnerBalance?: string  // 兼容字段，与 partner_balance 相同
  // 状态相关字段
  partner_status?: string
  partnerStatus?: string  // 兼容字段，与 partner_status 相同
  vip_expire_date?: string | null
  expireDate?: string | null  // 兼容字段，与 vip_expire_date 相同
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
 * 获取当前用户完整信息
 * 
 * 返回完整的用户信息，包括：
 * - 基础信息：openid、nickname、avatarUrl、avatar、phone
 * - 等级信息：level、level_code、level_name、levelInfo
 * - 余额信息：power（算力可用余额）、total_balance（算力总余额）、frozen_balance（冻结算力）、partner_balance、partnerBalance
 * - 状态信息：partner_status、partnerStatus、vip_expire_date、expireDate
 * 
 * 建议：前端应该从 store 读取用户信息，只在刷新页面时才调用此接口
 */
export function getCurrentUserInfo() {
  return request<{ success: boolean; userInfo: AuthUserInfo } | AuthUserInfo>({
    url: '/api/v1/client/auth/user',
    method: 'GET',
    showLoading: false
  })
}

/**
 * 上传头像响应类型
 */
export interface UploadAvatarResponse {
  code: number
  data: {
    url: string
    path: string
    filename: string
    original_name: string
    size: number
    content_type: string
  }
  msg: string
}

/**
 * 上传头像
 * @param filePath 文件路径（从 chooseAvatar 获取的临时路径）
 */
export function uploadAvatar(filePath: string): Promise<UploadAvatarResponse> {
  return new Promise((resolve, reject) => {
    // 获取 token
    const authStore = useAuthStore()
    const token = authStore.getToken()
    
    if (!token) {
      reject(new Error('未登录，请先登录'))
      return
    }

    // 构建完整 URL
    const BASE_URL = __API_BASE_URL__
    const url = BASE_URL + '/api/v1/client/upload/avatar'

    // 显示上传进度
    uni.showLoading({
      title: '上传中...',
      mask: true
    })

    // 使用 uni.uploadFile 上传文件
    uni.uploadFile({
      url: url,
      filePath: filePath,
      name: 'file', // 后端接收文件的字段名
      header: {
        'Authorization': `Bearer ${token}`,
        'X-My-Gate-Key': 'Huoyuan2026'
      },
      success: (res) => {
        uni.hideLoading()
        
        // 解析响应数据
        let responseData: UploadAvatarResponse
        try {
          const data = typeof res.data === 'string' ? JSON.parse(res.data) : res.data
          
          // 检查 HTTP 状态码
          if (res.statusCode >= 200 && res.statusCode < 300) {
            responseData = data
            resolve(responseData)
          } else {
            // HTTP 错误
            reject(new Error(data?.msg || data?.message || `上传失败，状态码: ${res.statusCode}`))
          }
        } catch (error) {
          console.error('解析上传响应失败:', error)
          reject(new Error('解析响应数据失败'))
        }
      },
      fail: (error) => {
        uni.hideLoading()
        console.error('上传头像失败:', error)
        
        // 处理错误信息
        let errorMsg = '上传失败'
        if (error.errMsg) {
          if (error.errMsg.includes('timeout')) {
            errorMsg = '上传超时，请重试'
          } else if (error.errMsg.includes('fail')) {
            errorMsg = '网络连接失败，请检查网络'
          } else {
            errorMsg = error.errMsg
          }
        }
        
        reject(new Error(errorMsg))
      }
    })
  })
}
