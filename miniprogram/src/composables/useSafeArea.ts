import { ref, onMounted } from 'vue'

/**
 * 安全区域信息
 */
export interface SafeAreaInfo {
  top: number      // 顶部安全区域高度（px）
  bottom: number   // 底部安全区域高度（px）
  left: number     // 左侧安全区域宽度（px）
  right: number    // 右侧安全区域宽度（px）
  statusBarHeight: number  // 状态栏高度（px）
  screenHeight: number     // 屏幕高度（px）
  screenWidth: number      // 屏幕宽度（px）
}

/**
 * 获取安全区域信息的 composable
 * 用于在 JS 中动态获取安全区域值（当 CSS env() 不生效时使用）
 */
export function useSafeArea() {
  const safeArea = ref<SafeAreaInfo>({
    top: 0,
    bottom: 0,
    left: 0,
    right: 0,
    statusBarHeight: 0,
    screenHeight: 0,
    screenWidth: 0
  })

  const updateSafeArea = () => {
    try {
      const systemInfo = uni.getSystemInfoSync()
      
      // 获取安全区域信息
      const safeAreaInsets = systemInfo.safeAreaInsets || {}
      const statusBarHeight = systemInfo.statusBarHeight || 0
      
      safeArea.value = {
        top: safeAreaInsets.top || 0,
        bottom: safeAreaInsets.bottom || 0,
        left: safeAreaInsets.left || 0,
        right: safeAreaInsets.right || 0,
        statusBarHeight: statusBarHeight,
        screenHeight: systemInfo.screenHeight || 0,
        screenWidth: systemInfo.screenWidth || 0
      }
      
      console.log('[SafeArea] 安全区域信息:', safeArea.value)
    } catch (error) {
      console.warn('[SafeArea] 获取安全区域信息失败:', error)
    }
  }

  onMounted(() => {
    updateSafeArea()
  })

  return {
    safeArea,
    updateSafeArea
  }
}


