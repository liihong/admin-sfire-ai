import { ref, computed, onMounted } from 'vue'

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

function readSafeAreaFromSystem(): SafeAreaInfo {
  try {
    const systemInfo = uni.getSystemInfoSync()
    const safeAreaInsets = systemInfo.safeAreaInsets || {}

    return {
      top: safeAreaInsets.top || 0,
      bottom: safeAreaInsets.bottom || 0,
      left: safeAreaInsets.left || 0,
      right: safeAreaInsets.right || 0,
      statusBarHeight: systemInfo.statusBarHeight || 0,
      screenHeight: systemInfo.screenHeight || systemInfo.windowHeight || 0,
      screenWidth: systemInfo.screenWidth || systemInfo.windowWidth || 0,
    }
  } catch (error) {
    console.warn('[SafeArea] 获取安全区域信息失败:', error)
    return {
      top: 0,
      bottom: 0,
      left: 0,
      right: 0,
      statusBarHeight: 0,
      screenHeight: 0,
      screenWidth: 0,
    }
  }
}

/**
 * 获取安全区域信息的 composable
 * 用于在 JS 中动态获取安全区域值（当 CSS env() 不生效时使用）
 */
export function useSafeArea() {
  const safeArea = ref<SafeAreaInfo>(readSafeAreaFromSystem())

  const updateSafeArea = () => {
    safeArea.value = readSafeAreaFromSystem()
  }

  /** scroll-view 可用高度（px），避免 calc() 在小程序渲染层被误解析 */
  const getScrollViewHeight = (navBarHeight = 44) =>
    computed(() => {
      const navH = safeArea.value.top + navBarHeight
      const h = safeArea.value.screenHeight - navH
      return h > 0 ? `${h}px` : '100vh'
    })

  onMounted(() => {
    updateSafeArea()
  })

  return {
    safeArea,
    updateSafeArea,
    getScrollViewHeight,
  }
}







