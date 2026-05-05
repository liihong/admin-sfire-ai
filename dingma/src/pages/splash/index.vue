<template>
  <view class="splash-page">
    <view class="splash-frame">
      <image
        class="splash-img"
        :class="{
          'splash-img--animate': phase === 'animate',
          'splash-img--hold': phase === 'hold'
        }"
        :src="imageUrl"
        mode="aspectFill"
        @animationend="onZoomAnimationEnd"
      />
    </view>
    <view class="skip-wrap" :style="{ paddingBottom: skipBottom + 'px' }">
      <view class="skip-btn" @tap="handleSkip">跳过</view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import {
  DINGMA_SPLASH_IMAGE_URL,
  STORAGE_DINGMA_SPLASH_ZOOM_PLAYED
} from '@/constants/tenant'
import { storage } from '@/utils/storage'

const imageUrl = DINGMA_SPLASH_IMAGE_URL

type SplashPhase = 'animate' | 'hold' | 'still'

const phase = ref<SplashPhase>('still')
const skipBottom = ref(24)
let fallbackTimer: ReturnType<typeof setTimeout> | null = null

function markZoomPlayed() {
  storage.set(STORAGE_DINGMA_SPLASH_ZOOM_PLAYED, true)
}

function onZoomAnimationEnd() {
  markZoomPlayed()
  phase.value = 'hold'
  if (fallbackTimer) {
    clearTimeout(fallbackTimer)
    fallbackTimer = null
  }
}

function handleSkip() {
  markZoomPlayed()
  phase.value = phase.value === 'animate' ? 'still' : 'hold'
  if (fallbackTimer) {
    clearTimeout(fallbackTimer)
    fallbackTimer = null
  }
  uni.switchTab({ url: '/pages/home/index' })
}

function updateSkipInset() {
  try {
    const sys = uni.getSystemInfoSync()
    const safe = sys.safeAreaInsets?.bottom ?? 0
    skipBottom.value = Math.max(24, safe + 16)
  } catch {
    skipBottom.value = 32
  }
}

function goMainTab() {
  uni.switchTab({ url: '/pages/home/index' })
}

onShow(() => {
  if (storage.get<boolean>(STORAGE_DINGMA_SPLASH_ZOOM_PLAYED, false)) {
    goMainTab()
    return
  }
  updateSkipInset()
})

onMounted(() => {
  if (storage.get<boolean>(STORAGE_DINGMA_SPLASH_ZOOM_PLAYED, false)) {
    return
  }
  phase.value = 'animate'
  fallbackTimer = setTimeout(() => {
    fallbackTimer = null
    if (!storage.get<boolean>(STORAGE_DINGMA_SPLASH_ZOOM_PLAYED, false)) {
      markZoomPlayed()
      phase.value = 'hold'
    }
  }, 3000)
})

onUnmounted(() => {
  if (fallbackTimer) {
    clearTimeout(fallbackTimer)
    fallbackTimer = null
  }
})
</script>

<style scoped lang="scss">
.splash-page {
  position: relative;
  width: 100%;
  height: 100vh;
  background: #000;
  overflow: hidden;
}

.splash-frame {
  position: absolute;
  inset: 0;
  overflow: hidden;
}

.splash-img {
  width: 100%;
  height: 100%;
  display: block;
  transform: scale(1);
  transform-origin: 45% 35%;
}

.splash-img--animate {
  animation: dingmaSplashZoom 2.6s ease-out forwards;
}

.splash-img--hold {
  transform: scale(1.0);
}

.skip-wrap {
  position: fixed;
  right: 0;
  bottom: 0;
  z-index: 10;
  padding-right: 28rpx;
  padding-left: 28rpx;
  pointer-events: none;
}

.skip-btn {
  pointer-events: auto;
  padding: 14rpx 36rpx;
  border-radius: 999rpx;
  background: rgba(0, 0, 0, 0.48);
  border: 1rpx solid rgba(255, 255, 255, 0.35);
  color: #fff;
  font-size: 26rpx;
  font-weight: 500;
}

.skip-btn:active {
  opacity: 0.85;
}
</style>
