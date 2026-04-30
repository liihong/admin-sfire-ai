<template>
  <view class="wrap">
    <!-- #ifdef MP-WEIXIN -->
    <web-view v-if="src" :src="src" @message="onMessage" />
    <view v-else class="empty">链接无效</view>
    <!-- #endif -->
    <!-- #ifndef MP-WEIXIN -->
    <view class="empty">请在微信小程序中打开</view>
    <!-- #endif -->
  </view>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { onLoad } from '@dcloudio/uni-app'

const src = ref('')

onLoad((options) => {
  const raw = options?.url ? decodeURIComponent(String(options.url)) : ''
  if (raw && (raw.startsWith('https://') || raw.startsWith('http://'))) {
    src.value = raw
  }
  const title = options?.title ? decodeURIComponent(String(options.title)) : ''
  if (title) {
    uni.setNavigationBarTitle({ title })
  }
})

function onMessage() {
  // 预留 H5 postMessage
}
</script>

<style scoped lang="scss">
.wrap {
  width: 100%;
  height: 100vh;
}

.empty {
  padding: 48rpx;
  color: #86909c;
  font-size: 28rpx;
}
</style>
