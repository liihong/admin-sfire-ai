/**
 * Auth Store - 用户认证状态管理
 * 
 * 使用 Pinia 管理用户登录状态、token 和用户信息
 * 支持本地持久化存储
 */

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { loginWithCode, refreshAccessToken as refreshTokenAPI, getCurrentUserInfo, type AuthUserInfo } from '@/api/user'
import { storage } from '@/utils/storage'

// 用户信息类型（导出以便其他地方使用）
export type UserInfo = AuthUserInfo

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
    return storage.has(TOKEN_KEY)
  })
  
  // ============== Actions ==============
  
  /**
   * 设置 Token
   */
  function setToken(newToken: string) {
    token.value = newToken
    storage.set(TOKEN_KEY, newToken)
  }
  
  /**
   * 设置 Refresh Token
   */
  function setRefreshToken(newRefreshToken: string) {
    refreshToken.value = newRefreshToken
    storage.set(REFRESH_TOKEN_KEY, newRefreshToken)
  }
  
  /**
   * 获取 Refresh Token（优先从内存，其次从本地存储）
   */
  function getRefreshToken(): string {
    if (refreshToken.value) {
      return refreshToken.value
    }
    // 尝试从本地存储恢复
    const storedRefreshToken = storage.get<string>(REFRESH_TOKEN_KEY)
    if (storedRefreshToken) {
      refreshToken.value = storedRefreshToken
      return storedRefreshToken
    }
    return ''
  }
  
  /**
   * 设置用户信息
   */
  function setUserInfo(info: UserInfo) {
    if (!info) {
      return
    }
    
    userInfo.value = info
    storage.set(USER_INFO_KEY, info)
  }
  
  /**
   * 获取 Token（优先从内存，其次从本地存储）
   * 注意：不会自动清除过期的token，保留token以便刷新
   */
  function getToken(): string {
    // 优先从内存读取
    if (token.value) {
      return token.value
    }
    
    // 尝试从本地存储恢复
    const storedToken = storage.get<string>(TOKEN_KEY)
    if (storedToken) {
      // 更新内存并返回（不判断过期，保留token以便刷新）
      token.value = storedToken
      return storedToken
    }
    return ''
  }
  
  /**
   * 从本地存储加载认证信息
   * 如果有token，会尝试刷新用户信息（如果token过期会自动刷新token）
   */
  async function loadFromStorage() {
    try {
      // 加载 token（不判断过期，保留token以便后续刷新）
      const storedToken = storage.get<string>(TOKEN_KEY)
      if (storedToken) {
        token.value = storedToken
      }
      
      // 加载 refresh token（refresh_token 长期有效，不需要检查过期）
      const storedRefreshToken = storage.get<string>(REFRESH_TOKEN_KEY)
      if (storedRefreshToken) {
        refreshToken.value = storedRefreshToken
      }
      
      // 加载用户信息
      const storedUserInfo = storage.get<UserInfo>(USER_INFO_KEY)
      if (storedUserInfo) {
        userInfo.value = storedUserInfo
      }
      
      // 如果有token，尝试刷新用户信息（这会自动处理token刷新）
      // refreshUserInfo 内部会通过 request 工具自动处理401和token刷新
      if (storedToken) {
        // 延迟一下，确保 refreshToken 已经加载到内存
        setTimeout(() => {
          refreshUserInfo().catch(() => {
            // refreshUserInfo 失败时，request工具已经处理了token刷新和清除逻辑
            // 这里不需要额外处理
          })
        }, 100)
      }
    } catch {
    // 静默失败
    }
  }
  
  /**
   * 清除认证信息（登出）
   */
  function clearAuth() {
    token.value = ''
    refreshToken.value = ''
    userInfo.value = null
    storage.remove(TOKEN_KEY)
    storage.remove(REFRESH_TOKEN_KEY)
    storage.remove(USER_INFO_KEY)
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
        return false
      }

      // 发送 code 给后端换取 token
      const response = await loginWithCode(loginResult.code)
      
      if (response.code === 200 && response.data) {
        setToken(response.data.token)
        // 保存 refreshToken（如果返回了）
        if (response.data.refreshToken) {
          setRefreshToken(response.data.refreshToken)
        }
        if (response.data.userInfo) {
          setUserInfo(response.data.userInfo)
        }
        return true
      }
      
      return false
    } catch {
      return false
    }
  }
  
  // 初始化时从本地存储加载（异步，不阻塞）
  loadFromStorage()

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
      return { success: false, isNetworkError: false }
    }
    
    try {
      const response = await refreshTokenAPI(currentRefreshToken)
      
      // 判断是否为网络错误
      const isNetworkError = response.code === -1 || response.code === -2
      
      if (response.code === 200 && response.data) {
        // 更新 access_token（会同时更新内存和storage）
        setToken(response.data.token)
        
        // 确保内存中的token是最新的（防止时序问题）
        token.value = response.data.token
        
        // 更新 refresh_token（后端每次都会返回新的 refreshToken，必须更新）
        if (response.data.refreshToken) {
          setRefreshToken(response.data.refreshToken)
          // 确保内存中的refreshToken是最新的
          refreshToken.value = response.data.refreshToken
        }

        return { success: true }
      }
      
      return { success: false, isNetworkError }
    } catch (error) {
      // 异常情况，可能是网络错误
      return { success: false, isNetworkError: true }
    }
  }
  
  /**
   * 刷新用户信息（静默刷新，不阻塞）
   * 使用当前的 access_token 获取最新的用户信息
   * 
   * 如果返回 401，会自动尝试刷新 token 并重试
   * 
   * @returns {Promise<boolean>} 是否刷新成功
   */
  async function refreshUserInfo(): Promise<boolean> {
    const currentToken = getToken()
    if (!currentToken) {
      return false
    }
    
    // 即使 token 可能即将过期，也尝试请求
    // 如果返回 401，request 工具会自动尝试刷新 token

    try {
      const response = await getCurrentUserInfo()
      
      // 检查响应是否有效
      if (!response) {
        console.warn('刷新用户信息失败: 响应为空')
        return false
      }

      // 如果返回 401，request 工具已经处理了刷新逻辑
      // 这里只需要处理成功的情况
      if (response.code === 200 && response.data) {
        // 检查返回的数据结构（支持两种格式：{success: true, userInfo: {...}} 或直接 {...}）
        let userInfoData: UserInfo | null = null

        if (typeof response.data === 'object' && response.data !== null) {
          // 如果返回格式是 {success: true, userInfo: {...}}
          if ('userInfo' in response.data) {
            userInfoData = (response.data as { userInfo: UserInfo }).userInfo
          }
          // 如果返回格式是直接的用户信息对象
          else if ('openid' in response.data) {
            userInfoData = response.data as UserInfo
          }
        }

        if (userInfoData) {
          setUserInfo(userInfoData)
          return true
        } else {
          console.warn('刷新用户信息失败: 无法解析用户信息数据', response.data)
        }
      } else {
        // 非200响应，记录日志但不抛出异常（401等错误已由request工具处理）
        if (response.code !== 401) {
          console.warn('刷新用户信息失败: 响应码', response.code, response.msg || response.message)
        }
      }
      
      return false
    } catch (error) {
      // 捕获可能的异常（虽然request工具理论上不会抛出异常，但为了防御性编程）
      console.error('刷新用户信息异常:', error)
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
    } catch {
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
    refreshAccessToken,
    refreshUserInfo,
    isTokenExpired
  }
})

// ============== 辅助函数 ==============

/**
 * 封装 uni.login 为 Promise
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
          reject(new Error('获取登录 code 失败'))
        }
      },
      fail: (err) => {
        reject(err)
      }
    })
    // #endif

    // #ifndef MP-WEIXIN
    // 非微信小程序环境（H5、App 等），不支持微信登录
    reject(new Error('当前环境不支持微信登录'))
    // #endif
  })
}

