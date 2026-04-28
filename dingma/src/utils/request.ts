/**
 * Request 请求封装
 * 
 * 封装 uni.request，自动在 Header 中带上 Authorization: Bearer {token}
 * 支持请求/响应拦截、错误处理等
 */

import { useAuthStore } from '@/stores/auth'

// 请求配置类型
export interface RequestConfig {
  url: string
  method?: 'GET' | 'POST' | 'PUT' | 'DELETE' | 'OPTIONS' | 'HEAD' | 'TRACE' | 'CONNECT'
  data?: unknown
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
  // 内部标志：是否是重试请求（避免重试时再次刷新 token）
  _isRetry?: boolean
}

// 响应类型（后端返回格式: {code: 200, data: {...}, msg: "..."}）
export interface ResponseData<T = unknown> {
  code: number
  data?: T
  msg?: string
  // 兼容字段（用于错误处理）
  success?: boolean
  message?: string
  // 标记是否需要刷新 token（401 错误时使用）
  needRefresh?: boolean
}

// API 基础地址（在 vite.config.ts 中配置）
const BASE_URL = __API_BASE_URL__

// 请求超时时间（毫秒）
const TIMEOUT = 100000

// 防止重复处理 401 错误的标志
let isHandling401 = false

/**
 * 请求拦截器 - 处理请求前的逻辑
 */
function requestInterceptor(config: RequestConfig): RequestConfig {
  // 构建完整 URL
  if (!config.url.startsWith('http')) {
    config.url = BASE_URL + config.url
  }
  
  // GET 请求：将 data 转换为查询参数，并过滤掉 undefined/null 值
  if (config.method === 'GET' && config.data) {
    const params: string[] = []
    Object.keys(config.data).forEach(key => {
      const value = config.data[key]
      // 只添加非 undefined 和非 null 的值
      if (value !== undefined && value !== null && value !== '') {
        params.push(`${encodeURIComponent(key)}=${encodeURIComponent(String(value))}`)
      }
    })
    const queryString = params.join('&')
    if (queryString) {
      config.url += (config.url.includes('?') ? '&' : '?') + queryString
    }
    // GET 请求不需要 data 字段
    config.data = undefined
  }
  
  // 设置默认请求头
  config.header = config.header || {}
  config.header['Content-Type'] = config.header['Content-Type'] || 'application/json'
  
  // 自动添加 Authorization Token
  if (config.needToken !== false) {
    try {
      const authStore = useAuthStore()
      // 每次请求时都重新获取token，确保使用最新的token
      if (authStore && typeof authStore.getToken === 'function') {
        const token = authStore.getToken()
        if (token) {
          config.header['Authorization'] = `Bearer ${token}`
          config.header["X-My-Gate-Key"] = "Huoyuan2026";
        }
      }
    } catch {
    // 静默失败
    }
  }
  
  // 设置超时时间
  config.timeout = config.timeout || TIMEOUT
  
  return config
}

/**
 * 处理401未授权错误：先尝试刷新 token，失败后才清除认证信息并跳转到登录页
 * 
 * 刷新逻辑：
 * 1. 检查是否有 refreshToken，如果没有则直接清除认证信息并跳转登录页
 * 2. 使用 refreshToken 刷新 access_token
 * 3. 刷新成功后，两个 token 都会被更新，返回 true 以便重试请求
 * 4. 刷新失败时：
 *    - 如果是网络错误，保留当前认证状态，不跳转登录页
 *    - 如果是 token 失效，清除所有认证信息并跳转登录页
 */
async function handleUnauthorized(originalConfig?: RequestConfig): Promise<boolean> {
  // 防止重复处理
  if (isHandling401) {
    return false
  }
  isHandling401 = true

  const authStore = useAuthStore()

  // 检查是否有 refreshToken（刷新 token 需要 refreshToken）
  const refreshToken = authStore.getRefreshToken()
  if (!refreshToken) {
    // 立即重置标志，避免重复处理
    isHandling401 = false

    // 延迟跳转，避免在请求回调中直接跳转
    // setTimeout(() => {
    //   uni.reLaunch({
    //     url: '/pages/login/index'
    //   })
    // }, 0)
    return false
  }

  // 尝试刷新 token（会同时更新 access_token 和 refresh_token）
  const refreshResult = await authStore.refreshAccessToken()

  if (refreshResult.success) {
    isHandling401 = false
    return true
  }

  // 刷新失败
  if (refreshResult.isNetworkError) {
    // 网络错误，保留当前认证状态，不跳转登录页
    isHandling401 = false
    return false
  }

  // token 失效，清除认证信息并跳转到登录页
  // 注意：只有在 refresh_token 真正失效时才清除（不是网络错误）
  isHandling401 = false

  // 延迟跳转，避免在请求回调中直接跳转
  // setTimeout(() => {
  //   uni.reLaunch({
  //     url: '/pages/login/index'
  //   })
  // }, 0)

  return false
}

/**
 * SSE 响应数据块
 */
interface SSEChunk {
  conversation_id?: number
  content?: string
}

/**
 * 解析 SSE (Server-Sent Events) 格式的流式响应
 */
function parseSSEResponse(sseData: string): { code: number; data: { conversation_id?: number; content: string } } {
  const lines = sseData.split('\n')
  let conversationId: number | undefined
  let content = ''

  for (const line of lines) {
    const trimmed = line.trim()
    if (trimmed.startsWith('data: ')) {
      try {
        const jsonStr = trimmed.substring(6) // 移除 "data: " 前缀
        const parsed = JSON.parse(jsonStr) as SSEChunk

        if (parsed.conversation_id !== undefined) {
          conversationId = parsed.conversation_id
        }
        if (parsed.content) {
          content += parsed.content
        }
      } catch {
        // 忽略解析错误，继续处理下一行
      }
    }
  }

  return {
    code: 200,
    data: {
      conversation_id: conversationId,
      content: content
    }
  }
}

/**
 * 响应拦截器 - 处理响应数据
 */
function responseInterceptor<T>(response: UniApp.RequestSuccessCallbackResult): ResponseData<T> {
  const { statusCode, data } = response

  // 检查是否为 SSE 流式响应
  // 注意：微信小程序中 header 键名可能是小写
  const header = response.header || {}
  const contentType = (header['content-type'] || header['Content-Type'] || '').toLowerCase()
  const dataIsString = typeof data === 'string'
  const dataStr = dataIsString ? (data as string) : ''
  const startsWithData = dataIsString && dataStr.trim().startsWith('data: ')
  const isEventStream = contentType.includes('text/event-stream')
  const isSSEResponse = dataIsString && (isEventStream || startsWithData)

  let processedData = data

  // 如果是 SSE 格式，解析并转换为 JSON 格式
  if (isSSEResponse) {
    try {
      processedData = parseSSEResponse(dataStr)
    } catch {
      return {
        success: false,
        message: '解析流式响应失败',
        code: -3
      }
    }
  }

  // 检查响应数据中的code字段（后端可能返回HTTP 200但code为401）
  // 确保 processedData 是对象而不是字符串
  let responseData: ResponseData<T>
  if (typeof processedData === 'string') {
    // 如果仍然是字符串，尝试解析为 JSON
    try {
      responseData = JSON.parse(processedData) as ResponseData<T>
    } catch {
      return {
        success: false,
        message: '响应数据格式错误',
        code: -4
      }
    }
  } else {
    responseData = processedData as ResponseData<T>
  }

  const responseCode = responseData?.code

  // 处理401未授权（HTTP状态码401或响应数据code为401）
  // 注意：这里不直接调用 handleUnauthorized，而是在 request 函数中处理，以便重试请求
  if (statusCode === 401 || responseCode === 401) {
    return {
      success: false,
      message: responseData?.msg || responseData?.message || '登录已过期，请重新登录',
      code: 401,
      needRefresh: true // 标记需要刷新 token
    }
  }
  
  // HTTP 状态码处理
  if (statusCode >= 200 && statusCode < 300) {
    // 成功响应
    return processedData as ResponseData<T>;
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
  const errorData = data as { message?: string; detail?: string } | null
  return {
    success: false,
    data: data as T,
    message: errorData?.message || errorData?.detail || '请求失败',
    code: statusCode
  }
}

/**
 * Uni.request 错误类型
 */
interface UniRequestError {
  errMsg: string
  statusCode?: number
}

/**
 * 错误处理器
 */
function errorHandler(error: UniRequestError): ResponseData {
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
export function request<T = unknown>(config: RequestConfig): Promise<ResponseData<T>> {
  return new Promise(async (resolve) => {
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
      success: async (response) => {
        // 响应拦截
        const result = responseInterceptor<T>(response)

        // 如果是 401 错误，尝试刷新 token 并重试
        // 注意：如果是重试请求（_isRetry=true），不再刷新，直接返回错误，避免死循环
        if (result.needRefresh && !config._isRetry) {
          const refreshSuccess = await handleUnauthorized(config)
          if (refreshSuccess) {
            // 刷新成功，重新发起请求（标记为重试，避免再次刷新）
            const retryConfig = { ...config, _isRetry: true }
            const retryResult = await request<T>(retryConfig)
            resolve(retryResult)
            return
          }
        }

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

