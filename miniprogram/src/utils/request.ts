/**
 * Request 请求封装
 * 
 * 封装 uni.request，自动在 Header 中带上 Authorization: Bearer {token}
 * 支持请求/响应拦截、错误处理、Mock 数据等
 */

import { useAuthStore } from '@/stores/auth'

// 请求配置类型
export interface RequestConfig {
  url: string
  method?: 'GET' | 'POST' | 'PUT' | 'DELETE' | 'OPTIONS' | 'HEAD' | 'TRACE' | 'CONNECT'
  data?: any
  header?: Record<string, string>
  timeout?: number
  dataType?: string
  responseType?: 'text' | 'arraybuffer'
  // 是否需要 token（默认 true）
  needToken?: boolean
  // 是否显示 loading（默认 false）
  showLoading?: boolean
  // loading 提示文字
  loadingText?: string
  // 是否使用 Mock 数据（默认 false）
  useMock?: boolean
  // Mock 数据
  mockData?: any
}

// 响应类型
export interface ResponseData<T = any> {
  success: boolean
  data?: T
  message?: string
  code?: number
}

// API 基础地址（在 vite.config.ts 中配置）
const BASE_URL = __API_BASE_URL__

// 请求超时时间（毫秒）
const TIMEOUT = 30000

// 是否开启全局 Mock 模式（开发环境可设为 true）
const GLOBAL_MOCK_MODE = false

/**
 * 请求拦截器 - 处理请求前的逻辑
 */
function requestInterceptor(config: RequestConfig): RequestConfig {
  // 构建完整 URL
  if (!config.url.startsWith('http')) {
    config.url = BASE_URL + config.url
  }
  
  // 设置默认请求头
  config.header = config.header || {}
  config.header['Content-Type'] = config.header['Content-Type'] || 'application/json'
  
  // 自动添加 Authorization Token
  if (config.needToken !== false) {
    const authStore = useAuthStore()
    const token = authStore.getToken()
    if (token) {
      config.header['Authorization'] = `Bearer ${token}`
    }
  }
  
  // 设置超时时间
  config.timeout = config.timeout || TIMEOUT
  
  return config
}

/**
 * 处理401未授权错误：清除认证信息并跳转到登录页
 */
function handleUnauthorized() {
  const authStore = useAuthStore()
  authStore.clearAuth()
  
  console.warn('Token expired or invalid, redirecting to login')
  
  // 延迟跳转，避免在请求回调中直接跳转
  setTimeout(() => {
    uni.reLaunch({
      url: '/pages/login/index'
    })
  }, 0)
}

/**
 * 响应拦截器 - 处理响应数据
 */
function responseInterceptor<T>(response: UniApp.RequestSuccessCallbackResult): ResponseData<T> {
  const { statusCode, data } = response
  
  // 检查响应数据中的code字段（后端可能返回HTTP 200但code为401）
  const responseData = data as any
  const responseCode = responseData?.code
  
  // 处理401未授权（HTTP状态码401或响应数据code为401）
  if (statusCode === 401 || responseCode === 401) {
    handleUnauthorized()
    return {
      success: false,
      message: responseData?.msg || responseData?.message || '登录已过期，请重新登录',
      code: 401
    }
  }
  
  // HTTP 状态码处理
  if (statusCode >= 200 && statusCode < 300) {
    // 成功响应
    return {
      success: true,
      data: data as T,
      code: statusCode
    }
  }
  
  if (statusCode === 403) {
    return {
      success: false,
      message: '没有权限访问',
      code: 403
    }
  }
  
  if (statusCode === 404) {
    return {
      success: false,
      message: '请求的资源不存在',
      code: 404
    }
  }
  
  if (statusCode >= 500) {
    return {
      success: false,
      message: '服务器错误，请稍后重试',
      code: statusCode
    }
  }
  
  // 其他错误
  return {
    success: false,
    data: data as T,
    message: (data as any)?.message || (data as any)?.detail || '请求失败',
    code: statusCode
  }
}

/**
 * 错误处理器
 */
function errorHandler(error: any): ResponseData {
  console.error('Request error:', error)
  
  // 网络错误
  if (error.errMsg?.includes('request:fail')) {
    return {
      success: false,
      message: '网络连接失败，请检查网络设置',
      code: -1
    }
  }
  
  // 超时错误
  if (error.errMsg?.includes('timeout')) {
    return {
      success: false,
      message: '请求超时，请稍后重试',
      code: -2
    }
  }
  
  return {
    success: false,
    message: error.errMsg || '请求失败',
    code: -999
  }
}

/**
 * 核心请求方法
 */
export function request<T = any>(config: RequestConfig): Promise<ResponseData<T>> {
  return new Promise((resolve) => {
    // 全局 Mock 模式或单个请求 Mock
    if (GLOBAL_MOCK_MODE || config.useMock) {
      console.log('[Mock] Using mock data for:', config.url)
      setTimeout(() => {
        resolve({
          success: true,
          data: config.mockData as T,
          code: 200
        })
      }, 300) // 模拟网络延迟
      return
    }
    
    // 请求拦截
    const processedConfig = requestInterceptor(config)
    
    // 显示 loading
    if (config.showLoading) {
      uni.showLoading({
        title: config.loadingText || '加载中...',
        mask: true
      })
    }
    
    // 发起请求
    uni.request({
      url: processedConfig.url,
      method: processedConfig.method || 'GET',
      data: processedConfig.data,
      header: processedConfig.header,
      timeout: processedConfig.timeout,
      dataType: processedConfig.dataType || 'json',
      responseType: processedConfig.responseType || 'text',
      success: (response) => {
        // 响应拦截
        const result = responseInterceptor<T>(response)
        resolve(result)
      },
      fail: (error) => {
        // 错误处理
        const result = errorHandler(error)
        resolve(result)
      },
      complete: () => {
        // 隐藏 loading
        if (config.showLoading) {
          uni.hideLoading()
        }
      }
    })
  })
}

// ============== 快捷方法 ==============

/**
 * GET 请求
 */
export function get<T = any>(url: string, params?: Record<string, any>, config?: Partial<RequestConfig>): Promise<ResponseData<T>> {
  // 处理 query 参数
  if (params) {
    const queryString = Object.entries(params)
      .filter(([_, value]) => value !== undefined && value !== null)
      .map(([key, value]) => `${encodeURIComponent(key)}=${encodeURIComponent(String(value))}`)
      .join('&')
    
    if (queryString) {
      url += (url.includes('?') ? '&' : '?') + queryString
    }
  }
  
  return request<T>({
    url,
    method: 'GET',
    ...config
  })
}

/**
 * POST 请求
 */
export function post<T = any>(url: string, data?: any, config?: Partial<RequestConfig>): Promise<ResponseData<T>> {
  return request<T>({
    url,
    method: 'POST',
    data,
    ...config
  })
}

/**
 * PUT 请求
 */
export function put<T = any>(url: string, data?: any, config?: Partial<RequestConfig>): Promise<ResponseData<T>> {
  return request<T>({
    url,
    method: 'PUT',
    data,
    ...config
  })
}

/**
 * DELETE 请求
 */
export function del<T = any>(url: string, data?: any, config?: Partial<RequestConfig>): Promise<ResponseData<T>> {
  return request<T>({
    url,
    method: 'DELETE',
    data,
    ...config
  })
}

// ============== API 模块 ==============

/**
 * 用户信息 API
 */
export const userApi = {
  /**
   * 获取用户详细信息（我的页面使用）
   */
  getUserInfo: () => {
    return get<{
      phone: string
      avatar: string
      nickname: string
      power: string
      partnerBalance: string
      partnerStatus: string
      expireDate: string | null
    }>('/api/v1/client/auth/user/info', undefined, { 
      showLoading: false 
    })
  },
  
  /**
   * 更新用户信息
   */
  updateUserInfo: (data: {
    nickname?: string
    avatar?: string
  }) => {
    return put<{
      success: boolean
      userInfo: {
        openid: string
        nickname: string
        avatarUrl: string
      }
    }>('/api/v1/client/auth/user', data, { 
      showLoading: true,
      loadingText: '更新中...'
    })
  }
}

/**
 * 生成内容 API
 */
export const generateApi = {
  /**
   * 通用生成接口（对话式创作）
   */
  generate: (params: {
    project_id?: number
    agent_type?: string
    messages: Array<{role: string, content: string}>
    model_type?: string
    temperature?: number
    max_tokens?: number
    stream?: boolean
  }) => {
    return post<{
      success: boolean
      content: string
      agent_type: string
      model_type: string
    }>('/api/v1/client/creation/chat', {
      project_id: params.project_id,
      agent_type: params.agent_type || 'efficient_oral',
      messages: params.messages,
      model_type: params.model_type || 'deepseek',
      temperature: params.temperature,
      max_tokens: params.max_tokens || 2048,
      stream: params.stream !== false
    }, { showLoading: true, loadingText: 'AI 生成中...' })
  },
  
  /**
   * 快速文案生成
   */
  copywriting: (params: {
    content: string
    agent_type?: string
    project_id?: number
    model_type?: string
  }) => {
    const queryParams = new URLSearchParams()
    queryParams.append('content', params.content)
    if (params.agent_type) queryParams.append('agent_type', params.agent_type)
    if (params.project_id) queryParams.append('project_id', String(params.project_id))
    if (params.model_type) queryParams.append('model_type', params.model_type)
    
    return post<{
      success: boolean
      content: string
      agent_type: string
      model_type: string
    }>(`/api/v1/client/creation/chat/quick?${queryParams.toString()}`, null, { showLoading: true })
  }
}

// 默认导出
export default {
  request,
  get,
  post,
  put,
  del,
  userApi,
  generateApi
}

