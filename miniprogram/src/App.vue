<script setup lang="ts">
import { onLaunch, onShow, onHide } from "@dcloudio/uni-app";
import { useAuthStore } from "@/stores/auth";

// ============== 路由白名单 ==============
const WHITE_LIST = [
  '/pages/login/index',
  '/pages/login/profile',
  '/pages/mine/index',
  '/pages/project/list',
  '/pages/contact/index'
]

// Tabbar 页面列表（不能使用 redirectTo 跳转）
const TABBAR_PAGES = [
  '/pages/index/index',
  '/pages/project/list',
  '/pages/mine/index'
]

/**
 * 检查路径是否在白名单中
 */
function isWhiteListed(url: string): boolean {
  // 处理 URL 参数
  const path = url.split('?')[0]
  return WHITE_LIST.some(item => path === item || path.startsWith(item + '?'))
}

/**
 * 检查路径是否是 tabbar 页面
 */
function isTabbarPage(url: string): boolean {
  const path = url.split('?')[0]
  return TABBAR_PAGES.some(item => path === item)
}

/**
 * 显示会员提示弹窗
 * @param callback 用户选择后的回调函数
 */
function showMemberTip(callback: (goToLogin: boolean) => void) {
  uni.showModal({
    title: '提示',
    content: '您当前为游客模式，部分功能受限。开通会员后可体验全部功能，是否前往登录？',
    confirmText: '去登录',
    cancelText: '继续浏览',
    success: (res) => {
      if (res.confirm) {
        // 用户选择去登录
        callback(true)
      } else {
        // 用户选择继续浏览
        callback(false)
      }
    },
    fail: () => {
      // 弹窗显示失败，默认允许访问
      callback(false)
    }
  })
}

/**
 * 路由拦截处理
 */
function handleRouteIntercept(args: { url: string }, interceptorType: string): boolean {
  const authStore = useAuthStore()
  const url = args.url
  
  console.log('[Router] Intercepting:', url)
  
  // 白名单路径放行
  if (isWhiteListed(url)) {
    console.log('[Router] Whitelist path, allow')
    return true
  }
  
  // 检查是否有 Token
  if (!authStore.hasToken) {
    console.log('[Router] No token, visitor mode')
    
    // 游客模式：显示提示，不强制跳转
    // 使用 setTimeout 延迟执行，避免拦截器冲突
    setTimeout(() => {
      showMemberTip((goToLogin) => {
        if (goToLogin) {
          // 用户选择去登录，跳转到登录页
          uni.reLaunch({
            url: '/pages/login/index'
          })
        } else {
          // 用户选择继续浏览，允许访问（功能可能受限）
          console.log('[Router] User continues as visitor')
        }
      })
    }, 0)
    
    // 允许继续访问（游客模式）
    return true
  }
  
  // 有 Token，放行
  console.log('[Router] Has token, allow')
  return true
}

/**
 * 设置全局路由拦截器
 */
function setupRouteInterceptors() {
  // 拦截 navigateTo
  uni.addInterceptor('navigateTo', {
    invoke(args: { url: string }) {
      return handleRouteIntercept(args, 'navigateTo')
    }
  })
  
  // 拦截 redirectTo
  uni.addInterceptor('redirectTo', {
    invoke(args: { url: string }) {
      // 检查是否是 tabbar 页面，redirectTo 不能跳转到 tabbar 页面
      if (isTabbarPage(args.url)) {
        console.warn('[Router] redirectTo cannot redirect to tabbar page:', args.url)
        // 不允许使用 redirectTo 跳转到 tabbar 页面
        return false
      }
      return handleRouteIntercept(args, 'redirectTo')
    }
  })
  
  // 拦截 reLaunch
  uni.addInterceptor('reLaunch', {
    invoke(args: { url: string }) {
      // reLaunch 到登录页时不拦截，避免死循环
      if (isWhiteListed(args.url)) {
        return true
      }
      return handleRouteIntercept(args, 'reLaunch')
    }
  })
  
  // 拦截 switchTab
  uni.addInterceptor('switchTab', {
    invoke(args: { url: string }) {
      const authStore = useAuthStore()
      
      console.log('[Router] switchTab intercepting:', args.url)
      
      // 检查是否有 Token
      if (!authStore.hasToken) {
        console.log('[Router] No token, visitor mode')
        
        // 游客模式：显示提示，不强制跳转
        setTimeout(() => {
          showMemberTip((goToLogin) => {
            if (goToLogin) {
              // 用户选择去登录，跳转到登录页
              uni.reLaunch({
                url: '/pages/login/index'
              })
            } else {
              // 用户选择继续浏览，允许访问
              console.log('[Router] User continues as visitor')
            }
          })
        }, 0)
        
        // 允许继续访问（游客模式）
        return true
      }
      
      return true
    }
  })
  
  console.log('[Router] Interceptors setup complete')
}

onLaunch(async () => {
  console.log("App Launch");
  
  // 设置路由拦截器
  setupRouteInterceptors()
  
  // 初始化认证 Store
  const authStore = useAuthStore();
  
  // 从本地存储加载认证信息
  authStore.loadFromStorage()
  
  // 检查是否已有 token
  const existingToken = authStore.getToken();
  
  if (existingToken) {
    console.log("Token exists, skip silent login");
  } else {
    console.log("No token found, user needs to login");
    // 不再自动静默登录，等待用户手动登录
  }
});

onShow(() => {
  console.log("App Show");
});

onHide(() => {
  console.log("App Hide");
});
</script>

<style>
/* 全局样式 */
page {
  background-color: #f5f5f5;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
}
page, view, text, scroll-view, swiper, button, input, textarea, label, navigator, image {
  box-sizing: border-box;
}
</style>
