<template>
  <view class="text-extract-page">
    <view class="nav-header">
      <SafeAreaTop />
      <view class="nav-content">
        <view class="nav-left" @tap="goBack">
          <text class="back-icon">‹</text>
        </view>
        <view class="nav-center">
          <text class="nav-title">文案提取</text>
        </view>
        <view class="nav-right" />
      </view>
    </view>

    <scroll-view class="main-scroll" scroll-y>
      <view class="card">
        <text class="card-title">粘贴抖音视频链接</text>
        <text class="tip">
          支持分享短链或浏览器打开的视频页链接。解析与语音识别在云端完成，不保存视频或音频文件。每次成功提取会消耗火源币（解析或识别失败不扣费）。
        </text>
        <textarea
          v-model="shareUrl"
          class="url-input"
          :maxlength="2000"
          placeholder="例如：https://v.douyin.com/xxxxx/"
          :show-confirm-bar="false"
        />
        <view
          class="primary-btn"
          :class="{ disabled: !shareUrl.trim() || loading }"
          @tap="doExtract"
        >
          <text v-if="loading" class="btn-loading">识别中…</text>
          <text v-else>提取口播文案</text>
        </view>
      </view>

      <view v-if="resultText !== null" class="card result-card">
        <text class="card-title">识别结果</text>
        <text v-if="videoTitle" class="meta">标题：{{ videoTitle }}</text>
        <view class="result-box">
          <text class="result-text" selectable>{{ resultText }}</text>
        </view>
        <view class="secondary-btn" @tap="copyText">
          <text>复制全文</text>
        </view>
      </view>

      <view class="bottom-safe-area" />
    </scroll-view>
  </view>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import SafeAreaTop from '@/components/common/SafeAreaTop.vue'
import { useAuthStore } from '@/stores/auth'
import { extractDouyinCaption } from '@/api/tools'

const authStore = useAuthStore()

const shareUrl = ref('')
const loading = ref(false)
const resultText = ref<string | null>(null)
const videoTitle = ref<string | null>(null)

async function doExtract() {
  const url = shareUrl.value.trim()
  if (!url)
    return

  const loggedIn = await authStore.requireLogin()
  if (!loggedIn) return

  loading.value = true
  resultText.value = null
  videoTitle.value = null
  try {
    const res = await extractDouyinCaption({ url })
    if (res.code === 200 && res.data?.text != null) {
      resultText.value = res.data.text
      videoTitle.value = res.data.title ?? null
      uni.showToast({ title: '提取成功', icon: 'success' })
    } else {
      uni.showToast({
        title: res.msg || res.message || '提取失败',
        icon: 'none'
      })
    }
  } finally {
    loading.value = false
  }
}

function copyText() {
  if (!resultText.value) return
  uni.setClipboardData({
    data: resultText.value,
    success: () => {
      uni.showToast({ title: '已复制', icon: 'success' })
    },
    fail: () => {
      uni.showToast({ title: '复制失败', icon: 'none' })
    }
  })
}

function goBack() {
  uni.navigateBack({
    fail: () => {
      uni.switchTab({ url: '/pages/quick-entries/index' })
    }
  })
}
</script>

<style scoped lang="scss">
@import '@/styles/_variables.scss';

.text-extract-page {
  min-height: 100vh;
  background: $bg-color;
}

.nav-header {
  background: $white;
  position: sticky;
  top: 0;
  z-index: 100;

  .nav-content {
    display: flex;
    align-items: center;
    padding: $spacing-md $spacing-lg;

    .nav-left {
      width: 60rpx;

      .back-icon {
        font-size: 48rpx;
        color: $text-main;
        line-height: 1;
      }
    }

    .nav-center {
      flex: 1;
      text-align: center;

      .nav-title {
        font-size: $font-size-lg;
        font-weight: 600;
        color: $text-main;
      }
    }

    .nav-right {
      width: 60rpx;
    }
  }
}

.main-scroll {
  height: calc(100vh - 120rpx);
  box-sizing: border-box;
}

.card {
  margin: $spacing-md;
  padding: $spacing-lg;
  background: $white;
  border-radius: $radius-xl;
  box-shadow: 0 2rpx 12rpx rgba(0, 0, 0, 0.06);

  .card-title {
    display: block;
    font-size: $font-size-md;
    font-weight: 600;
    color: $text-main;
    margin-bottom: $spacing-sm;
  }

  .tip {
    display: block;
    font-size: $font-size-sm;
    color: $text-second;
    line-height: 1.6;
    margin-bottom: $spacing-md;
  }

  .url-input {
    width: 100%;
    min-height: 160rpx;
    padding: $spacing-md;
    box-sizing: border-box;
    font-size: $font-size-sm;
    color: $text-main;
    background: $bg-color;
    border-radius: $radius-md;
    border: 1rpx solid $border-color;
  }

  .primary-btn {
    margin-top: $spacing-lg;
    height: 88rpx;
    line-height: 88rpx;
    text-align: center;
    border-radius: $radius-lg;
    background: linear-gradient(135deg, $primary-orange 0%, $primary-orange-alt 100%);
    color: $white;
    font-size: $font-size-md;
    font-weight: 600;

    &.disabled {
      opacity: 0.45;
      pointer-events: none;
    }

    .btn-loading {
      color: $white;
    }
  }
}

.result-card {
  .meta {
    display: block;
    font-size: $font-size-sm;
    color: $text-second;
    margin-bottom: $spacing-sm;
  }

  .result-box {
    padding: $spacing-md;
    background: $bg-color;
    border-radius: $radius-md;
    border: 1rpx solid $border-color;
    max-height: 60vh;
    overflow-y: auto;
  }

  .result-text {
    font-size: $font-size-sm;
    color: $text-main;
    line-height: 1.7;
    white-space: pre-wrap;
    word-break: break-all;
  }

  .secondary-btn {
    margin-top: $spacing-md;
    height: 80rpx;
    line-height: 80rpx;
    text-align: center;
    border-radius: $radius-lg;
    border: 2rpx solid $primary-orange;
    color: $primary-orange;
    font-size: $font-size-md;
  }
}

.bottom-safe-area {
  height: 48rpx;
}
</style>
