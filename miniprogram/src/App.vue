<script setup lang="ts">
import { onLaunch, onShow, onHide } from "@dcloudio/uni-app";
import { useAuthStore } from "@/stores/auth";
import { setConfig } from "uview-plus";

onLaunch(async () => {
  // 配置 uview-plus 使用本地字体，避免请求阿里云 CDN
  // 注意：需要先将字体文件下载到 /static/fonts/uview-iconfont.ttf
  setConfig({
    iconUrl: '/static/fonts/uview-iconfont.ttf'
  });

  // 初始化安全区域信息（用于动态设置 CSS 变量）
  try {
    const systemInfo = uni.getSystemInfoSync()
    const safeAreaInsets = (systemInfo.safeAreaInsets as { top?: number; bottom?: number }) || {}
    const statusBarHeight = systemInfo.statusBarHeight || 0
    
    // 设置全局 CSS 变量（如果 env() 不生效时使用）
    const safeAreaTop = safeAreaInsets.top || statusBarHeight || 0
    const safeAreaBottom = safeAreaInsets.bottom || 0
    
    // 将安全区域高度存储到全局，供组件使用
    // 注意：这里存储的是 px，转换为 rpx 需要乘以 2
  } catch {
  // 静默失败
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
  // App 显示
});

onHide(() => {
  // App 隐藏
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
