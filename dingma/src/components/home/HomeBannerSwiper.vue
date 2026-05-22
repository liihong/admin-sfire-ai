<template>
  <view class="banner-swiper-wrap">
    <swiper
      v-if="displayList.length > 0"
      class="banner-swiper"
      :indicator-dots="displayList.length > 1"
      :autoplay="displayList.length > 1"
      :interval="4000"
      :duration="500"
      indicator-color="rgba(255,255,255,0.45)"
      :indicator-active-color="indicatorActive"
      circular
    >
      <swiper-item v-for="(item, index) in displayList" :key="item.id ?? index">
        <view class="banner-slide" @tap="handleTap(item)">
          <image class="banner-image" :src="item.image_url" mode="aspectFill" />
        </view>
      </swiper-item>
    </swiper>
    <view v-else class="banner-slide banner-slide--placeholder" @tap="openDefaultPdf">
      <image class="banner-image" :src="fallbackUrl" mode="aspectFill" />
    </view>
  </view>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { BannerItem } from '@/api/home'
import { DINGMA_HOME_BANNER_URL, DINGMA_PROJECT_PDF_URL } from '@/constants/tenant'
import { isPdfUrl, openRemotePdf } from '@/utils/document'

const props = defineProps<{
  banners?: BannerItem[]
}>()

const indicatorActive = '#F37021'
const fallbackUrl = DINGMA_HOME_BANNER_URL

const displayList = computed(() => {
  const list = props.banners?.filter((b) => b.image_url?.trim()) ?? []
  if (list.length > 0) return list
  return [
    {
      id: 0,
      title: '',
      image_url: fallbackUrl,
      link_type: 'none' as const,
      position: 'home_top' as const,
      sort_order: 0
    }
  ]
})

function openDefaultPdf() {
  openRemotePdf(DINGMA_PROJECT_PDF_URL, { loadingTitle: '正在打开文档…' })
}

function handleTap(item: BannerItem) {
  const linkUrl = item.link_url?.trim() ?? ''

  if (linkUrl && isPdfUrl(linkUrl)) {
    openRemotePdf(linkUrl, { loadingTitle: '正在打开文档…' })
    return
  }
  if (item.link_type === 'internal' && linkUrl) {
    uni.navigateTo({ url: linkUrl })
    return
  }
  if (item.link_type === 'external' && linkUrl) {
    uni.navigateTo({
      url: `/pages/common/webview?title=${encodeURIComponent(item.title || '详情')}&url=${encodeURIComponent(linkUrl)}`
    })
    return
  }
  openDefaultPdf()
}
</script>

<style scoped lang="scss">
@import '@/styles/_variables.scss';

.banner-swiper-wrap {
  margin: 0 28rpx;
  border-radius: 24rpx;
  overflow: hidden;
  box-shadow: 0 8rpx 32rpx rgba(33, 37, 41, 0.08);
}

.banner-swiper {
  height: 320rpx;
}

.banner-slide {
  width: 100%;
  height: 320rpx;
  overflow: hidden;

  &--placeholder {
    border-radius: 24rpx;
  }
}

.banner-image {
  width: 100%;
  height: 100%;
  display: block;
}
</style>

<style lang="scss">
.banner-swiper-wrap .wx-swiper-dots .wx-swiper-dot {
  width: 12rpx;
  height: 12rpx;
  border-radius: 50%;
}
.banner-swiper-wrap .wx-swiper-dots .wx-swiper-dot-active {
  width: 36rpx;
  height: 12rpx;
  border-radius: 6rpx;
  background: #f37021 !important;
}
</style>
