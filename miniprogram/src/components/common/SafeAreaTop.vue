<template>
  <view 
    class="safe-area-top" 
    :style="{ height: safeAreaHeight + 'rpx' }"
  ></view>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'

// 安全区高度（rpx）
const safeAreaHeight = ref(0)

onMounted(() => {
  try {
    // 使用微信官方 API 获取安全区域信息（推荐方案）
    const systemInfo = uni.getSystemInfoSync()
    const safeAreaInsets = (systemInfo.safeAreaInsets as { top?: number; bottom?: number; left?: number; right?: number }) || {}
    const statusBarHeight = systemInfo.statusBarHeight || 0
    
    // 优先使用 safeAreaInsets.top，否则使用 statusBarHeight
    // 注意：uni.getSystemInfoSync() 返回的是 px，需要转换为 rpx（乘以 2）
    const topHeight = safeAreaInsets.top || statusBarHeight || 0
    safeAreaHeight.value = topHeight * 2 // px 转 rpx
    
    console.log('[SafeAreaTop] 安全区域信息:', {
      safeAreaInsetsTop: safeAreaInsets.top,
      statusBarHeight: statusBarHeight,
      finalHeight: safeAreaHeight.value + 'rpx'
    })
  } catch (error) {
    console.warn('[SafeAreaTop] 获取安全区域信息失败:', error)
    safeAreaHeight.value = 0
  }
})
</script>

<style lang="scss" scoped>
.safe-area-top {
  flex-shrink: 0;
  width: 100%;
  /* CSS 方案作为 fallback（微信小程序中可能不生效） */
  height: constant(safe-area-inset-top);
  height: env(safe-area-inset-top);
  min-height: constant(safe-area-inset-top);
  min-height: env(safe-area-inset-top);
}
</style>

