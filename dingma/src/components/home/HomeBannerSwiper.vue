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
          <navigator
            v-if="getBannerCaption(item) && hasBannerLink(item)"
            class="banner-caption banner-caption--link"
            :url="normalizeBannerLink(item)"
            hover-class="banner-caption--active"
            @tap.stop
          >
            <text class="banner-caption__text">{{ getBannerCaption(item) }}</text>
          </navigator>
          <view v-else-if="getBannerCaption(item)" class="banner-caption">
            <text class="banner-caption__text">{{ getBannerCaption(item) }}</text>
          </view>
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
import { safeNavigateTo } from '@/utils/navigation'

const props = defineProps<{
  banners?: BannerItem[]
}>()

const indicatorActive = '#D94B36'
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

function getBannerCaption(item: BannerItem) {
  return item.title?.trim() ?? ''
}

function hasBannerLink(item: BannerItem) {
  const linkUrl = item.link_url?.trim() ?? ''
  return linkUrl !== '' && item.link_type !== 'none'
}

function normalizeBannerLink(item: BannerItem) {
  const linkUrl = item.link_url?.trim() ?? ''
  if (!linkUrl) return ''
  if (item.link_type === 'external') {
    return `/pages/common/webview?title=${encodeURIComponent(item.title || '详情')}&url=${encodeURIComponent(linkUrl)}`
  }
  return linkUrl.startsWith('/') ? linkUrl : `/${linkUrl}`
}

function handleTap(item: BannerItem) {
  const linkUrl = item.link_url?.trim() ?? ''

  if (linkUrl && isPdfUrl(linkUrl)) {
    openRemotePdf(linkUrl, { loadingTitle: '正在打开文档…' })
    return
  }
  if (item.link_type === 'internal' && linkUrl) {
    safeNavigateTo({ url: normalizeBannerLink(item) })
    return
  }
  if (item.link_type === 'external' && linkUrl) {
    safeNavigateTo({ url: normalizeBannerLink(item) })
    return
  }
  openDefaultPdf()
}
</script>

<style scoped lang="scss">
@import '@/styles/_variables.scss';

.banner-swiper-wrap {
  margin: 0;
  border-radius: 0;
  overflow: hidden;
  box-shadow: $shadow-banner-3d;
}

.banner-swiper {
  height: 370rpx;
}

.banner-slide {
  position: relative;
  width: 100%;
  height: 370rpx;
  overflow: hidden;

  &--placeholder {
    border-radius: 0;
  }
}

.banner-image {
  width: 100%;
  height: 100%;
  display: block;
}

.banner-caption {
  position: absolute;
  left: 24rpx;
  bottom: 24rpx;
  z-index: 2;
  max-width: calc(100% - 48rpx);
  padding: 10rpx 24rpx;
  border-radius: 999rpx;
  background: rgba(0, 0, 0, 0.42);
  box-sizing: border-box;

  &--link {
    background: rgba(0, 0, 0, 0.52);
  }

  &--active {
    opacity: 0.82;
  }

  &__text {
    display: block;
    color: #fff;
    font-size: 22rpx;
    line-height: 1.4;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }
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
  background: #d94b36 !important;
}
</style>
