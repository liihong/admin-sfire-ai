<script setup lang="ts">
import { onLaunch, onShow, onHide } from "@dcloudio/uni-app";
import { useAuthStore } from "@/stores/auth";

// ============== 路由白名单 ==============
const WHITE_LIST = [
  '/pages/login/index',
  '/pages/login/profile'
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
 * 路由拦截处理
 */
function handleRouteIntercept(args: { url: string }): boolean {
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
    console.log('[Router] No token, redirect to login')
    
    // 使用 setTimeout 延迟执行，避免拦截器冲突
    setTimeout(() => {
      uni.reLaunch({
        url: '/pages/login/index'
      })
    }, 0)
    
    // 阻止原导航
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
      return handleRouteIntercept(args)
    }
  })
  
  // 拦截 redirectTo
  uni.addInterceptor('redirectTo', {
    invoke(args: { url: string }) {
      return handleRouteIntercept(args)
    }
  })
  
  // 拦截 reLaunch
  uni.addInterceptor('reLaunch', {
    invoke(args: { url: string }) {
      // reLaunch 到登录页时不拦截，避免死循环
      if (isWhiteListed(args.url)) {
        return true
      }
      return handleRouteIntercept(args)
    }
  })
  
  // 拦截 switchTab
  uni.addInterceptor('switchTab', {
    invoke(args: { url: string }) {
      const authStore = useAuthStore()
      
      console.log('[Router] switchTab intercepting:', args.url)
      
      // 检查是否有 Token
      if (!authStore.hasToken) {
        console.log('[Router] No token, redirect to login')
        
        setTimeout(() => {
          uni.reLaunch({
            url: '/pages/login/index'
          })
        }, 0)
        
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
