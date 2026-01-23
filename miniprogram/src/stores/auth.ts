/**
 * Auth Store - 用户认证状态管理
 * 
 * 使用 Pinia 管理用户登录状态、token 和用户信息
 * 支持本地持久化存储
 */

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

// 用户信息类型
export interface UserInfo {
  openid: string
  nickname: string
  avatarUrl: string
  gender?: number
  city?: string
  province?: string
  country?: string
}

// 缓存 key
const TOKEN_KEY = 'sfire_ai_token'
const REFRESH_TOKEN_KEY = 'sfire_ai_refresh_token'
const USER_INFO_KEY = 'sfire_ai_user_info'

/**
 * Auth Store
 */
export const useAuthStore = defineStore('auth', () => {
  // ============== State ==============
  
  // 用户 token
  const token = ref<string>('')
  
  // 刷新 token（用于刷新 access_token）
  const refreshToken = ref<string>('')
  
  // 用户信息
  const userInfo = ref<UserInfo | null>(null)
  
  // 登录状态
  const isLoggedIn = computed(() => !!token.value)
  
  // 是否有 Token（用于路由拦截）
  const hasToken = computed(() => {
    // 优先检查内存中的 token
    if (token.value) return true
    // 再检查本地存储
    try {
      return !!uni.getStorageSync(TOKEN_KEY)
    } catch {
      return false
    }
  })
  
  // ============== Actions ==============
  
  /**
   * 设置 Token
   */
  function setToken(newToken: string) {
    token.value = newToken
    // 持久化存储
    try {
      uni.setStorageSync(TOKEN_KEY, newToken)
    } catch (error) {
      console.error('Failed to save token:', error)
    }
  }
  
  /**
   * 设置 Refresh Token
   */
  function setRefreshToken(newRefreshToken: string) {
    refreshToken.value = newRefreshToken
    // 持久化存储
    try {
      uni.setStorageSync(REFRESH_TOKEN_KEY, newRefreshToken)
    } catch (error) {
      console.error('Failed to save refresh token:', error)
    }
  }
  
  /**
   * 获取 Refresh Token（优先从内存，其次从本地存储）
   */
  function getRefreshToken(): string {
    if (refreshToken.value) {
      return refreshToken.value
    }
    // 尝试从本地存储恢复
    try {
      const storedRefreshToken = uni.getStorageSync(REFRESH_TOKEN_KEY)
      if (storedRefreshToken) {
        refreshToken.value = storedRefreshToken
        return storedRefreshToken
      }
    } catch (error) {
      console.error('Failed to get refresh token:', error)
    }
    return ''
  }
  
  /**
   * 设置用户信息
   */
  function setUserInfo(info: UserInfo) {
    userInfo.value = info
    // 持久化存储
    try {
      uni.setStorageSync(USER_INFO_KEY, JSON.stringify(info))
    } catch (error) {
      console.error('Failed to save user info:', error)
    }
  }
  
  /**
   * 获取 Token（优先从内存，其次从本地存储）
   * 注意：如果从storage读取的token已过期，会自动清除
   */
  function getToken(): string {
    // 优先从内存读取
    if (token.value) {
      return token.value
    }
    
    // 尝试从本地存储恢复
    try {
      const storedToken = uni.getStorageSync(TOKEN_KEY)
      if (storedToken) {
        // 检查token是否过期，如果过期则清除
        if (isTokenExpired(storedToken)) {
          console.warn('[getToken] Stored token is expired, clearing it')
          // 清除过期的token
          uni.removeStorageSync(TOKEN_KEY)
          token.value = ''
          return ''
        }
        // token有效，更新内存并返回
        token.value = storedToken
        return storedToken
      }
    } catch (error) {
      console.error('Failed to get token:', error)
    }
    return ''
  }
  
  /**
   * 从本地存储加载认证信息
   * 注意：如果token已过期，会自动清除
   */
  function loadFromStorage() {
    try {
      // 加载 token（检查是否过期）
      const storedToken = uni.getStorageSync(TOKEN_KEY)
      if (storedToken) {
        // 检查token是否过期
        if (isTokenExpired(storedToken)) {
          console.warn('[loadFromStorage] Stored token is expired, clearing it')
          // 清除过期的token
          uni.removeStorageSync(TOKEN_KEY)
          token.value = ''
        } else {
          // token有效，加载到内存
          token.value = storedToken
        }
      }
      
      // 加载 refresh token（refresh_token 长期有效，不需要检查过期）
      const storedRefreshToken = uni.getStorageSync(REFRESH_TOKEN_KEY)
      if (storedRefreshToken) {
        refreshToken.value = storedRefreshToken
      }
      
      // 加载用户信息
      const storedUserInfo = uni.getStorageSync(USER_INFO_KEY)
      if (storedUserInfo) {
        userInfo.value = JSON.parse(storedUserInfo)
      }
    } catch (error) {
      console.error('Failed to load auth info:', error)
    }
  }
  
  /**
   * 清除认证信息（登出）
   */
  function clearAuth() {
    token.value = ''
    refreshToken.value = ''
    userInfo.value = null
    try {
      uni.removeStorageSync(TOKEN_KEY)
      uni.removeStorageSync(REFRESH_TOKEN_KEY)
      uni.removeStorageSync(USER_INFO_KEY)
    } catch (error) {
      console.error('Failed to clear auth:', error)
    }
  }
  
  /**
   * 静默登录
   * 调用 uni.login 获取 code，发送给后端换取 token
   */
  async function silentLogin(): Promise<boolean> {
    try {
      // 调用微信登录获取 code
      const loginResult = await wxLogin()
      
      if (!loginResult.code) {
        console.error('Failed to get login code')
        return false
      }
      
      console.log('Got login code:', loginResult.code)
      
      // 发送 code 给后端换取 token
      const response = await loginWithCode(loginResult.code)
      
      if (response.success && response.token) {
        setToken(response.token)
        // 保存 refreshToken（如果返回了）
        if (response.refreshToken) {
          setRefreshToken(response.refreshToken)
        }
        if (response.userInfo) {
          setUserInfo(response.userInfo)
        }
        console.log('Silent login success')
        return true
      }
      
      return false
    } catch (error) {
      console.error('Silent login failed:', error)
      return false
    }
  }
  
  // 初始化时从本地存储加载
  loadFromStorage()
  
  /**
   * 开发环境自动登录（仅用于调试）
   * 调用后端登录接口获取真实有效的 token
   * 仅在开发版本(develop)中可用
   */
  async function devAutoLogin(): Promise<boolean> {
    // 环境检查：仅开发版可用
    try {
      // @ts-ignore - uni.getAccountInfoSync 在部分平台可能不存在
      const accountInfo = uni.getAccountInfoSync?.()
      // miniProgram.envVersion: develop(开发版) / trial(体验版) / release(正式版)
      if (accountInfo?.miniProgram?.envVersion !== 'develop') {
        console.warn('[devAutoLogin] 仅开发环境可用，当前环境:', accountInfo?.miniProgram?.envVersion)
        return false
      }
    } catch {
      // 获取环境信息失败，默认不允许
      console.warn('[devAutoLogin] 无法获取环境信息，已禁用')
      return false
    }

    // 开发者调试账号 - 使用固定的 code 以获得相同的 mock openid
    const DEV_CODE = 'dev_login_13261276633'

    try {
      console.log('[devAutoLogin] 开始开发环境自动登录')

      // 调用后端登录接口
      const response = await loginWithCode(DEV_CODE)

      if (response.success && response.token) {
        setToken(response.token)
        // 保存 refreshToken（如果返回了）
        if (response.refreshToken) {
          setRefreshToken(response.refreshToken)
        }
        if (response.userInfo) {
          setUserInfo(response.userInfo)
        }
        console.log('[devAutoLogin] 开发环境自动登录成功')
        return true
      }

      console.error('[devAutoLogin] 登录失败，响应:', response)
      return false
    } catch (error) {
      console.error('[devAutoLogin] 登录异常:', error)
      return false
    }
  }

  /**
   * 检查是否需要登录，未登录时跳转到登录页面
   * @param redirectToLogin 未登录时是否跳转登录页（默认 true）
   * @returns 是否已登录
   */
  async function requireLogin(redirectToLogin: boolean = true): Promise<boolean> {
    if (isLoggedIn.value) {
      return true
    }

    // 未登录，直接跳转到登录页面
    if (redirectToLogin) {
      uni.navigateTo({
        url: '/pages/login/index'
      })
    }

    return false
  }
  
  /**
   * 刷新 Token
   * 使用 refreshToken 获取新的 access_token 和 refresh_token
   * 
   * 注意：刷新 token 的请求不应该携带过期的 access_token
   * 
   * @returns {Promise<{success: boolean, isNetworkError?: boolean}>}
   *   - success: 是否刷新成功
   *   - isNetworkError: 是否为网络错误（true 表示网络错误，false 表示 token 失效）
   */
  async function refreshAccessToken(): Promise<{success: boolean, isNetworkError?: boolean}> {
    const currentRefreshToken = getRefreshToken()
    if (!currentRefreshToken) {
      console.warn('[refreshToken] No refresh token found')
      return { success: false, isNetworkError: false }
    }
    
    try {
      const baseUrl = getBaseUrl()
      const response = await new Promise<{
        success: boolean
        token?: string
        refreshToken?: string
        isNetworkError?: boolean
      }>((resolve) => {
        uni.request({
          url: `${baseUrl}/api/v1/client/auth/refresh`,
          method: 'POST',
          data: { refreshToken: currentRefreshToken },
          header: {
            'Content-Type': 'application/json'
            // 注意：刷新 token 的请求不应该携带过期的 access_token
            // 所以不设置 Authorization header
          },
          success: (res: any) => {
            if (res.statusCode === 200 && res.data) {
              const responseData = res.data
              if (responseData.code === 200 && responseData.data) {
                resolve({
                  success: true,
                  token: responseData.data.token,
                  refreshToken: responseData.data.refreshToken
                })
              } else {
                // API 返回错误（可能是 token 失效）
                console.error('[refreshToken] API error:', responseData)
                resolve({ success: false, isNetworkError: false })
              }
            } else {
              console.error('[refreshToken] API error:', res)
              resolve({ success: false, isNetworkError: false })
            }
          },
          fail: (err) => {
            // 判断是否为网络错误
            // uni.request 的 fail 回调可能包含多种错误：网络错误、超时、DNS解析失败等
            const errMsg = err.errMsg || ''
            const isNetworkError = errMsg.includes('fail') || 
                                  errMsg.includes('timeout') || 
                                  errMsg.includes('network') ||
                                  errMsg.includes('DNS')
            
            if (isNetworkError) {
              console.error('[refreshToken] Request failed (network error):', err)
              resolve({ success: false, isNetworkError: true })
            } else {
              // 其他错误（如服务器错误），视为 token 失效
              console.error('[refreshToken] Request failed (other error):', err)
              resolve({ success: false, isNetworkError: false })
            }
          }
        })
      })
      
      if (response.success && response.token) {
        // 更新 access_token（会同时更新内存和storage）
        setToken(response.token)
        
        // 确保内存中的token是最新的（防止时序问题）
        token.value = response.token
        
        // 更新 refresh_token（后端每次都会返回新的 refreshToken，必须更新）
        if (response.refreshToken) {
          setRefreshToken(response.refreshToken)
          // 确保内存中的refreshToken是最新的
          refreshToken.value = response.refreshToken
        } else {
          console.warn('[refreshToken] No refreshToken in response, keeping old one')
        }
        
        console.log('[refreshToken] Token refreshed successfully, both tokens updated')
        console.log('[refreshToken] New token saved to memory and storage')
        return { success: true }
      }
      
      return { success: false, isNetworkError: response.isNetworkError || false }
    } catch (error) {
      // 异常情况，可能是网络错误
      console.error('[refreshToken] Refresh failed:', error)
      return { success: false, isNetworkError: true }
    }
  }
  
  /**
   * 刷新用户信息（静默刷新，不阻塞）
   * 使用当前的 access_token 获取最新的用户信息
   * 
   * 注意：使用 uni.request 而不是 request 工具，避免循环依赖
   * 如果返回 401，会自动尝试刷新 token 并重试
   * 
   * @returns {Promise<boolean>} 是否刷新成功
   */
  async function refreshUserInfo(): Promise<boolean> {
    const currentToken = getToken()
    if (!currentToken) {
      console.warn('[refreshUserInfo] No token found')
      return false
    }
    
    // 即使 token 可能即将过期，也尝试请求
    // 如果返回 401，会自动尝试刷新 token
    
    try {
      const baseUrl = getBaseUrl()
      const response = await new Promise<{
        success: boolean
        userInfo?: UserInfo
        needRefresh?: boolean
      }>((resolve) => {
        uni.request({
          url: `${baseUrl}/api/v1/client/auth/user`,
          method: 'GET',
          header: {
            'Authorization': `Bearer ${currentToken}`,
            'Content-Type': 'application/json'
          },
          success: (res: any) => {
            if (res.statusCode === 200 && res.data) {
              const responseData = res.data
              if (responseData.code === 200 && responseData.data) {
                resolve({
                  success: true,
                  userInfo: responseData.data.userInfo
                })
              } else if (responseData.code === 401) {
                // 返回 401，需要刷新 token
                resolve({ success: false, needRefresh: true })
              } else {
                console.error('[refreshUserInfo] API error:', responseData)
                resolve({ success: false })
              }
            } else {
              console.error('[refreshUserInfo] API error:', res)
              resolve({ success: false })
            }
          },
          fail: (err) => {
            console.error('[refreshUserInfo] Request failed:', err)
            resolve({ success: false })
          }
        })
      })
      
      // 如果返回 401，尝试刷新 token 并重试
      if (response.needRefresh) {
        console.log('[refreshUserInfo] Got 401, attempting to refresh token')
        const refreshResult = await refreshAccessToken()
        if (refreshResult.success) {
          // 刷新成功，使用新的 token 重试
          const newToken = getToken()
          if (newToken) {
            const retryResponse = await new Promise<{
              success: boolean
              userInfo?: UserInfo
            }>((resolve) => {
              uni.request({
                url: `${baseUrl}/api/v1/client/auth/user`,
                method: 'GET',
                header: {
                  'Authorization': `Bearer ${newToken}`,
                  'Content-Type': 'application/json'
                },
                success: (res: any) => {
                  if (res.statusCode === 200 && res.data) {
                    const responseData = res.data
                    if (responseData.code === 200 && responseData.data) {
                      resolve({
                        success: true,
                        userInfo: responseData.data.userInfo
                      })
                    } else {
                      resolve({ success: false })
                    }
                  } else {
                    resolve({ success: false })
                  }
                },
                fail: () => {
                  resolve({ success: false })
                }
              })
            })
            
            if (retryResponse.success && retryResponse.userInfo) {
              setUserInfo(retryResponse.userInfo)
              console.log('[refreshUserInfo] User info refreshed successfully after token refresh')
              return true
            }
          }
        }
        // 刷新失败，返回 false
        return false
      }
      
      if (response.success && response.userInfo) {
        setUserInfo(response.userInfo)
        console.log('[refreshUserInfo] User info refreshed successfully')
        return true
      }
      
      return false
    } catch (error) {
      console.error('[refreshUserInfo] Refresh failed:', error)
      return false
    }
  }
  
  /**
   * Base64 URL 解码（兼容微信小程序环境）
   */
  function base64UrlDecode(str: string): string {
    // Base64 URL 转 Base64 标准格式
    let base64 = str.replace(/-/g, '+').replace(/_/g, '/')
    // 添加 padding
    const pad = base64.length % 4
    if (pad) {
      base64 += '='.repeat(4 - pad)
    }
    
    // 尝试使用 atob（浏览器环境）
    // #ifdef H5
    try {
      return decodeURIComponent(
        atob(base64)
          .split('')
          .map(c => '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2))
          .join('')
      )
    } catch {
      // fallback to manual decode
    }
    // #endif
    
    // 手动 Base64 解码（兼容所有环境）
    const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/='
    let output = ''
    let i = 0
    
    while (i < base64.length) {
      const enc1 = chars.indexOf(base64.charAt(i++))
      const enc2 = chars.indexOf(base64.charAt(i++))
      const enc3 = chars.indexOf(base64.charAt(i++))
      const enc4 = chars.indexOf(base64.charAt(i++))
      
      const chr1 = (enc1 << 2) | (enc2 >> 4)
      const chr2 = ((enc2 & 15) << 4) | (enc3 >> 2)
      const chr3 = ((enc3 & 3) << 6) | enc4
      
      output += String.fromCharCode(chr1)
      if (enc3 !== 64) output += String.fromCharCode(chr2)
      if (enc4 !== 64) output += String.fromCharCode(chr3)
    }
    
    // 转换为 UTF-8 字符串
    try {
      return decodeURIComponent(escape(output))
    } catch {
      return output
    }
  }
  
  /**
   * 检查 token 是否过期（简单检查，不验证签名）
   * 通过解析 JWT token 的 payload 来检查过期时间
   */
  function isTokenExpired(tokenStr: string): boolean {
    if (!tokenStr) return true
    
    try {
      // JWT token 格式: header.payload.signature
      const parts = tokenStr.split('.')
      if (parts.length !== 3) return true
      
      // 解码 payload（Base64 URL 解码）
      const payloadStr = base64UrlDecode(parts[1])
      const decodedPayload = JSON.parse(payloadStr)
      
      // 检查过期时间（exp 字段是 Unix 时间戳，单位：秒）
      const exp = decodedPayload.exp
      if (!exp) return true
      
      // 当前时间（秒）
      const now = Math.floor(Date.now() / 1000)
      
      // 如果过期时间小于当前时间，说明已过期
      // 提前 5 分钟刷新（避免在边界时间出现问题）
      return exp < (now + 300)
    } catch (error) {
      console.error('[isTokenExpired] Failed to check token expiration:', error)
      // 解析失败，认为已过期
      return true
    }
  }

  return {
    // State
    token,
    userInfo,
    
    // Getters
    isLoggedIn,
    hasToken,
    
    // Actions
    setToken,
    setRefreshToken,
    setUserInfo,
    getToken,
    getRefreshToken,
    loadFromStorage,
    clearAuth,
    silentLogin,
    requireLogin,
    devAutoLogin,
    refreshAccessToken,
    refreshUserInfo,
    isTokenExpired
  }
})

// ============== 辅助函数 ==============

/**
 * 封装 uni.login 为 Promise
 * 在开发环境使用 Mock 数据
 */
function wxLogin(): Promise<{ code: string }> {
  return new Promise((resolve, reject) => {
    // #ifdef MP-WEIXIN
    // 微信小程序环境
    uni.login({
      provider: 'weixin',
      success: (res) => {
        if (res.code) {
          resolve({ code: res.code })
        } else {
          // 如果获取 code 失败，使用 mock code
          console.warn('uni.login failed, using mock code')
          resolve({ code: generateMockCode() })
        }
      },
      fail: (err) => {
        console.warn('uni.login error, using mock code:', err)
        // 失败时使用 mock code
        resolve({ code: generateMockCode() })
      }
    })
    // #endif
    
    // #ifndef MP-WEIXIN
    // 非微信小程序环境（H5、App 等），使用 Mock
    console.log('[Mock] Using mock login code for non-WeChat environment')
    resolve({ code: generateMockCode() })
    // #endif
  })
}

/**
 * 生成 Mock 登录 code
 */
function generateMockCode(): string {
  const timestamp = Date.now()
  const random = Math.random().toString(36).substring(2, 10)
  return `mock_code_${timestamp}_${random}`
}

/**
 * 发送登录 code 给后端
 */
async function loginWithCode(code: string): Promise<{
  success: boolean
  token?: string
  refreshToken?: string
  userInfo?: UserInfo
}> {
  return new Promise((resolve) => {
    // 获取后端 API 地址
    const baseUrl = getBaseUrl()
    
    uni.request({
      url: `${baseUrl}/api/v1/client/auth/login`,
      method: 'POST',
      data: { code },
      header: {
        'Content-Type': 'application/json'
      },
      success: (res: any) => {
        // 后端返回格式: {code: 200, data: {token: "...", userInfo: {...}}, msg: "..."}
        if (res.statusCode === 200 && res.data) {
          const responseData = res.data
          if (responseData.code === 200 && responseData.data) {
            resolve({
              success: true,
              token: responseData.data.token,
              refreshToken: responseData.data.refreshToken,
              userInfo: responseData.data.userInfo
            })
          } else {
            console.error('Login API error:', responseData)
            resolve({ success: false })
          }
        } else {
          console.error('Login API error:', res)
          resolve({ success: false })
        }
      },
      fail: (err) => {
        console.error('Login request failed:', err)
        // 请求失败时，使用 Mock 数据（方便开发调试）
        console.log('[Mock] Using mock login response')
        resolve(getMockLoginResponse(code))
      }
    })
  })
}

/**
 * 获取后端 API 基础地址
 */
function getBaseUrl(): string {
  // 开发环境
  // #ifdef H5
  return 'http://localhost:8000'
  // #endif
  
  // #ifdef MP-WEIXIN
  // 微信小程序需要配置合法域名，开发时可以使用本地地址
  return 'http://localhost:8000'
  // #endif
  
  // #ifndef H5
  // #ifndef MP-WEIXIN
  return 'http://localhost:8000'
  // #endif
  // #endif
}

/**
 * Mock 登录响应（用于开发调试）
 */
function getMockLoginResponse(code: string): {
  success: boolean
  token: string
  userInfo: UserInfo
} {
  // 生成 mock token
  const mockToken = `mock_token_${Date.now()}_${Math.random().toString(36).substring(2, 15)}`
  
  // mock 用户信息
  const mockUserInfo: UserInfo = {
    openid: `mock_openid_${code.substring(0, 8)}`,
    nickname: '测试用户',
    avatarUrl: '/static/default-avatar.png',
    gender: 0,
    city: '深圳',
    province: '广东',
    country: '中国'
  }
  
  return {
    success: true,
    token: mockToken,
    userInfo: mockUserInfo
  }
}

