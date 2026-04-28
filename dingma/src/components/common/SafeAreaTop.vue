<template>
  <view 
    class="safe-area-top" 
:style="{ height: safeAreaHeight + 'px' }"
  ></view>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'

// 安全区高度（px，直接使用系统返回值，适配各机型）
const safeAreaHeight = ref(0)

onMounted(() => {
  try {
    const systemInfo = uni.getSystemInfoSync()
    const safeAreaInsets = (systemInfo.safeAreaInsets as { top?: number }) || {}
    const statusBarHeight = systemInfo.statusBarHeight || 0

    // 直接使用 px，不做 rpx 转换，适配 iPhone 12/13/15 Pro 等各机型
    safeAreaHeight.value = safeAreaInsets.top ?? statusBarHeight ?? 0
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

