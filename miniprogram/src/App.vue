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

// 记录用户已选择继续浏览的 URL（避免重复弹窗）
const allowedVisitorUrls = new Set<string>()

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
  console.log('会员提示')
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
  const path = url.split('?')[0] // 获取路径部分，忽略参数
  
  console.log('[Router] Intercepting:', url)
  
  // 白名单路径放行
  if (isWhiteListed(url)) {
    console.log('[Router] Whitelist path, allow')
    return true
  }
  
  // 检查是否有 Token
  if (!authStore.hasToken) {
    // 如果用户已经选择继续浏览过这个页面，直接放行
    if (allowedVisitorUrls.has(path)) {
      console.log('[Router] User already chose to continue browsing this page, allow')
      return true
    }

    console.log('[Router] No token, visitor mode')
    
    // 游客模式：先阻止路由跳转，显示提示弹窗
    setTimeout(() => {
      showMemberTip((goToLogin) => {
        if (goToLogin) {
          // 用户选择去登录，跳转到登录页
          uni.reLaunch({
            url: '/pages/login/index'
          })
        } else {
          // 用户选择继续浏览，记录允许的 URL，然后手动执行路由跳转
          allowedVisitorUrls.add(path)
          console.log('[Router] User continues as visitor, navigating to:', url)

          // 使用 nextTick 确保拦截器状态更新后再执行跳转
          setTimeout(() => {
            if (interceptorType === 'navigateTo') {
              uni.navigateTo({ url })
            } else if (interceptorType === 'redirectTo') {
              uni.redirectTo({ url })
            } else if (interceptorType === 'reLaunch') {
              uni.reLaunch({ url })
            }
          }, 100)
        }
      })
    }, 0)
    
    // 先阻止路由跳转，等待用户选择
    return false
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
      const path = args.url.split('?')[0] // 获取路径部分，忽略参数
      
      console.log('[Router] switchTab intercepting:', args.url)
      
      // 检查是否有 Token
      if (!authStore.hasToken) {
        // 如果用户已经选择继续浏览过这个页面，直接放行
        if (allowedVisitorUrls.has(path)) {
          console.log('[Router] User already chose to continue browsing this tab, allow')
          return true
        }

        console.log('[Router] No token, visitor mode')
        
        // 游客模式：先阻止路由跳转，显示提示弹窗
        setTimeout(() => {
          showMemberTip((goToLogin) => {
            if (goToLogin) {
              // 用户选择去登录，跳转到登录页
              uni.reLaunch({
                url: '/pages/login/index'
              })
            } else {
              // 用户选择继续浏览，记录允许的 URL，然后手动执行 tabbar 跳转
              allowedVisitorUrls.add(path)
              console.log('[Router] User continues as visitor, switching to tab:', args.url)

              // 使用 nextTick 确保拦截器状态更新后再执行跳转
              setTimeout(() => {
                uni.switchTab({ url: args.url })
              }, 100)
            }
          })
        }, 0)
        
        // 先阻止路由跳转，等待用户选择
        return false
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

<style lang="scss">
/* 加上这一行，解决 common.scss 找不到变量的问题 */
  @import 'uview-plus/theme.scss'; 
  
  /* 引入基础样式 */
  @import 'uview-plus/index.scss';

/* 全局样式 */
page {
  background-color: #f5f5f5;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
}
page, view, text, scroll-view, swiper, button, input, textarea, label, navigator, image {
  box-sizing: border-box;
}
</style>
