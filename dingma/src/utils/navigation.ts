/**
 * 路由导航工具
 * 统一处理页面跳转，包含错误处理
 */

/**
 * 检查路由错误并显示友好提示
 * @param error 错误对象
 */
function handleNavigationError(error: any) {
  const errMsg = error?.errMsg || ''
  
  // 检查是否是页面不存在的错误
  if (errMsg.includes('is not found') || errMsg.includes('页面不存在')) {
    uni.showToast({
      title: '功能开发中，请耐心等待',
      icon: 'none',
      duration: 2000
    })
    return true
  }
  
  return false
}

/**
 * 包装 navigateTo，添加错误处理
 */
export function safeNavigateTo(options: UniApp.NavigateToOptions) {
  uni.navigateTo({
    ...options,
    fail: (error) => {
      // 先尝试统一错误处理
      const handled = handleNavigationError(error)
      
      // 如果用户提供了自定义 fail 回调，也执行它
      if (options.fail && !handled) {
        options.fail(error)
      }
    }
  })
}

/**
 * 包装 redirectTo，添加错误处理
 */
export function safeRedirectTo(options: UniApp.RedirectToOptions) {
  uni.redirectTo({
    ...options,
    fail: (error) => {
      const handled = handleNavigationError(error)
      if (options.fail && !handled) {
        options.fail(error)
      }
    }
  })
}

/**
 * 包装 switchTab，添加错误处理
 */
export function safeSwitchTab(options: UniApp.SwitchTabOptions) {
  uni.switchTab({
    ...options,
    fail: (error) => {
      const handled = handleNavigationError(error)
      if (options.fail && !handled) {
        options.fail(error)
      }
    }
  })
}

/**
 * 包装 reLaunch，添加错误处理
 */
export function safeReLaunch(options: UniApp.ReLaunchOptions) {
  uni.reLaunch({
    ...options,
    fail: (error) => {
      const handled = handleNavigationError(error)
      if (options.fail && !handled) {
        options.fail(error)
      }
    }
  })
}










