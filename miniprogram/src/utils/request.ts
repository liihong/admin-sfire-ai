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
}

// 响应类型（后端返回格式: {code: 200, data: {...}, msg: "..."}）
export interface ResponseData<T = any> {
  code: number
  data?: T
  msg?: string
  // 兼容字段（用于错误处理）
  success?: boolean
  message?: string
}

// API 基础地址（在 vite.config.ts 中配置）
const BASE_URL = __API_BASE_URL__

// 请求超时时间（毫秒）
const TIMEOUT = 60000

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
    return data as ResponseData<T>;
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

// 默认导出
export default {
  request
}

