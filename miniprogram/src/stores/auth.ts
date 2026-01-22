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
const USER_INFO_KEY = 'sfire_ai_user_info'

/**
 * Auth Store
 */
export const useAuthStore = defineStore('auth', () => {
  // ============== State ==============
  
  // 用户 token
  const token = ref<string>('')
  
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
   */
  function getToken(): string {
    if (token.value) {
      return token.value
    }
    // 尝试从本地存储恢复
    try {
      const storedToken = uni.getStorageSync(TOKEN_KEY)
      if (storedToken) {
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
   */
  function loadFromStorage() {
    try {
      // 加载 token
      const storedToken = uni.getStorageSync(TOKEN_KEY)
      if (storedToken) {
        token.value = storedToken
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
    userInfo.value = null
    try {
      uni.removeStorageSync(TOKEN_KEY)
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

  return {
    // State
    token,
    userInfo,
    
    // Getters
    isLoggedIn,
    hasToken,
    
    // Actions
    setToken,
    setUserInfo,
    getToken,
    loadFromStorage,
    clearAuth,
    silentLogin,
    requireLogin,
    devAutoLogin
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

