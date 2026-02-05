/**
 * 微信小程序工具函数
 * 
 * 封装微信小程序相关的通用功能
 */

/**
 * 微信登录获取 code
 * 
 * @returns Promise<{ code: string }> 返回包含 code 的对象
 * @throws Error 获取失败时抛出错误
 */
export function wxLogin(): Promise<{ code: string }> {
  return new Promise((resolve, reject) => {
    // #ifdef MP-WEIXIN
    uni.login({
      provider: 'weixin',
      success: (res) => {
        if (res.code) {
          resolve({ code: res.code })
        } else {
          reject(new Error('获取登录凭证失败'))
        }
      },
      fail: (err) => {
        console.error('uni.login failed:', err)
        reject(err)
      }
    })
    // #endif

    // #ifndef MP-WEIXIN
    // 非微信环境，登录失败
    reject(new Error('当前仅支持微信小程序环境'))
    // #endif
  })
}

/**
 * 关闭小程序
 * 
 * 在微信小程序环境中调用退出小程序API，非微信环境则返回上一页或跳转首页
 * 
 * @param fallbackUrl 关闭失败时的回退页面路径（可选）
 */
export function exitMiniProgram(fallbackUrl?: string): void {
  // #ifdef MP-WEIXIN
  // 微信小程序环境，使用退出小程序API
  uni.exitMiniProgram({
    success: () => {
      console.log('小程序已关闭')
    },
    fail: (err) => {
      console.error('关闭小程序失败:', err)
      // 如果关闭失败，执行回退逻辑
      handleFallback(fallbackUrl)
    }
  })
  // #endif

  // #ifndef MP-WEIXIN
  // 非微信环境，执行回退逻辑
  handleFallback(fallbackUrl)
  // #endif
}

/**
 * 处理关闭小程序失败时的回退逻辑
 * 
 * @param fallbackUrl 回退页面路径（可选）
 */
function handleFallback(fallbackUrl?: string): void {
  const pages = getCurrentPages()
  if (pages.length > 1) {
    // 有上一页，则返回
    uni.navigateBack({ delta: 1 })
  } else if (fallbackUrl) {
    // 有指定的回退路径，则跳转
    if (fallbackUrl.startsWith('/pages/')) {
      // tabBar 页面使用 switchTab
      const tabBarPages = ['/pages/index/index', '/pages/project/index', '/pages/mine/index']
      if (tabBarPages.includes(fallbackUrl)) {
        uni.switchTab({ url: fallbackUrl })
      } else {
        uni.redirectTo({ url: fallbackUrl })
      }
    }
  } else {
    // 默认跳转到首页
    uni.switchTab({ url: '/pages/index/index' })
  }
}

/**
 * 从页面参数中获取 scene 值
 * 
 * 微信小程序码的 scene 值可能通过多种方式传递：
 * 1. options.scene（直接参数）
 * 2. options.query.scene（查询参数）
 * 3. 从当前页面实例获取
 * 
 * @param options 页面加载时的 options 参数
 * @returns scene 值，如果不存在则返回 null
 */
export function getSceneFromOptions(options: any): string | null {
  // 方式1: 直接从 options.scene 获取
  if (options?.scene) {
    return String(options.scene)
  }
  
  // 方式2: 从 options.query.scene 获取
  if (options?.query?.scene) {
    return String(options.query.scene)
  }
  
  // 方式3: 从当前页面实例获取
  try {
    const pages = getCurrentPages()
    const currentPage = pages[pages.length - 1]
    if (currentPage?.options) {
      const sceneValue = currentPage.options.scene || currentPage.options.query?.scene
      if (sceneValue) {
        return String(sceneValue)
      }
    }
  } catch (error) {
    console.error('获取 scene 参数失败:', error)
  }
  
  return null
}

