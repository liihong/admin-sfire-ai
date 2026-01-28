<script setup lang="ts">
import { onLaunch, onShow, onHide } from "@dcloudio/uni-app";
import { useAuthStore } from "@/stores/auth";
import { setConfig } from "uview-plus";

// ============== 路由白名单 ==============
const WHITE_LIST = [
  '/pages/login/index',
  '/pages/login/profile',
  '/pages/mine/index',
  '/pages/contact/index'
]

// Tabbar 页面列表（不能使用 redirectTo 跳转）
const TABBAR_PAGES = [
  '/pages/index/index',
  '/pages/project/index',
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

  // 白名单路径放行
  if (isWhiteListed(url)) {
    return true
  }
  
  // 检查是否有 Token
  if (!authStore.hasToken) {
    // 如果用户已经选择继续浏览过这个页面，直接放行
    if (allowedVisitorUrls.has(path)) {
      return true
    }

    // 游客模式：先阻止路由跳转，显示提示弹窗
    // 使用 Promise.resolve 确保当前拦截器调用完成后再执行
    Promise.resolve().then(() => {
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

          // 使用 Promise.resolve 确保拦截器状态更新后再执行跳转
          Promise.resolve().then(() => {
            if (interceptorType === 'navigateTo') {
              uni.navigateTo({ url })
            } else if (interceptorType === 'redirectTo') {
              uni.redirectTo({ url })
            } else if (interceptorType === 'reLaunch') {
              uni.reLaunch({ url })
            }
          })
        }
      })
    })
    
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
      const authStore = useAuthStore()
      const path = args.url.split('?')[0]

      // 检查是否是 tabbar 页面，redirectTo 不能跳转到 tabbar 页面
      if (isTabbarPage(args.url)) {
        console.log('[Router] redirectTo to tabbar page, using switchTab instead:', args.url)

        // 先检查认证状态
        if (!authStore.hasToken) {
          // 游客模式：显示提示弹窗
          if (!allowedVisitorUrls.has(path)) {
            // 使用 Promise.resolve 确保当前拦截器调用完成后再执行
            Promise.resolve().then(() => {
              showMemberTip((goToLogin) => {
                if (goToLogin) {
                  uni.reLaunch({ url: '/pages/login/index' })
                } else {
                  allowedVisitorUrls.add(path)
                  // 使用 Promise.resolve 确保路由状态清理后再调用 switchTab
                  Promise.resolve().then(() => {
                    uni.switchTab({ url: args.url })
                  })
                }
              })
            })
            return false
          }
        }

        // 有 token 或已选择继续浏览，直接用 switchTab
        // 使用 Promise.resolve 确保当前拦截器调用完成后再执行 switchTab
        Promise.resolve().then(() => {
          uni.switchTab({ url: args.url })
        })
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
        // 使用 Promise.resolve 确保当前拦截器调用完成后再执行
        Promise.resolve().then(() => {
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

              // 使用 Promise.resolve 确保拦截器状态更新后再执行跳转
              Promise.resolve().then(() => {
                uni.switchTab({ url: args.url })
              })
            }
          })
        })
        
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
  
  // 配置 uview-plus 使用本地字体，避免请求阿里云 CDN
  // 注意：需要先将字体文件下载到 /static/fonts/uview-iconfont.ttf
  setConfig({
    iconUrl: '/static/fonts/uview-iconfont.ttf'
  });
  
  // 设置路由拦截器
  setupRouteInterceptors()
  
  // 初始化安全区域信息（用于动态设置 CSS 变量）
  try {
    const systemInfo = uni.getSystemInfoSync()
    const safeAreaInsets = systemInfo.safeAreaInsets || {}
    const statusBarHeight = systemInfo.statusBarHeight || 0
    
    // 设置全局 CSS 变量（如果 env() 不生效时使用）
    const safeAreaTop = safeAreaInsets.top || statusBarHeight || 0
    const safeAreaBottom = safeAreaInsets.bottom || 0
    
    // 将安全区域高度存储到全局，供组件使用
    // 注意：这里存储的是 px，转换为 rpx 需要乘以 2
    if (safeAreaTop > 0 || safeAreaBottom > 0) {
      console.log('[App] 安全区域信息:', {
        top: safeAreaTop,
        bottom: safeAreaBottom,
        statusBarHeight
      })
    }
  } catch (error) {
    console.warn('[App] 获取安全区域信息失败:', error)
  }
  
  // 初始化认证 Store（loadFromStorage 已在 auth.ts 中自动调用）
  const authStore = useAuthStore();
  
  // 注意：loadFromStorage() 已经在 auth.ts 初始化时自动调用
  // 它会自动处理 token 加载和用户信息刷新
  // 这里不需要重复调用，也不需要手动检查 token 状态
  // 如果 token 过期，refreshUserInfo() 会自动处理 token 刷新
  // 如果刷新失败，request 工具会自动清除认证信息
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

/* 引入 iconfont.css */
@import '@/styles/iconfont.css';
/* 全局样式 */
page {
  background-color: #f5f5f5;
  font-family: -apple-system, BlinkMacSystemFont, 'Helvetica Neue', Helvetica,
      Segoe UI, Arial, Roboto, 'PingFang SC', 'miui', 'Hiragino Sans GB', 'Microsoft Yahei',
      sans-serif;
  
    /* 开启字体抗锯齿，让文字在 iOS 上更清晰 */
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
    /* 1. 颜色不要用纯黑 #000，太刺眼，用深灰 */
    color: #333333;
  
    /* 2. 行高设为字号的 1.5 到 1.6 倍 */
    line-height: 1.6;
  
    /* 3. 适当增加字间距 */
    letter-spacing: 1rpx;
}
page, view, text, scroll-view, swiper, button, input, textarea, label, navigator, image {
  box-sizing: border-box;
}
/* 自定义tabbar图标大小 */
.tab-bar .uni-tabbar__icon image {
  width: 20rpx; /* 调整为你想要的宽度 */
  height: 20rpx; /* 调整为你想要的高度 */
}

/* ========== iPhone 灵动岛适配工具类 ========== */
/* 
 * 注意：微信小程序中 env(safe-area-inset-top) 可能不生效
 * 推荐使用 SafeAreaTop 组件或通过 JS 动态设置高度
 * 这里保留 CSS 方案作为 fallback，但主要依赖 JS 动态设置
 */
.safe-area-top {
  flex-shrink: 0;
  width: 100%;
  /* CSS 方案作为 fallback（可能不生效） */
  height: constant(safe-area-inset-top);
  height: env(safe-area-inset-top);
  min-height: constant(safe-area-inset-top);
  min-height: env(safe-area-inset-top);
}

/* 底部安全区占位 */
.safe-area-bottom {
  flex-shrink: 0;
  width: 100%;
  /* CSS 方案作为 fallback（可能不生效） */
  height: constant(safe-area-inset-bottom);
  height: env(safe-area-inset-bottom);
  min-height: constant(safe-area-inset-bottom);
  min-height: env(safe-area-inset-bottom);
}
</style>
