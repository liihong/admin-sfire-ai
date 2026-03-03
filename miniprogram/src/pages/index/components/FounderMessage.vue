<template>
  <view class="founder-message">
    <swiper
      class="founder-swiper"
      :indicator-dots="true"
      :autoplay="true"
:interval="4000"
      :duration="500"
      indicator-color="rgba(255,255,255,0.3)"
      indicator-active-color="#ffffff"
      circular
:display-multiple-items="1"
    >
     <swiper-item v-for="(item, index) in bannerList" :key="item.id || index">
        <view class="banner-card" @tap="handleBannerTap(item)">
          <image v-if="item.image_url" class="banner-image" :src="item.image_url" mode="aspectFill" />
          <view v-else class="message-card">
            <view class="message-title">{{ item.title }}</view>
           <view class="message-desc">{{ item.title }}</view>
          </view>
        </view>
      </swiper-item>
    </swiper>
  </view>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { BannerItem } from '@/api/home'

// 接收父组件传递的 banners 数据（home_top）
const props = defineProps<{
  banners?: BannerItem[]
}>()

// 使用父组件接口查询的 banners 数据
const bannerList = computed(() => {
  if (props.banners && props.banners.length > 0) {
    return props.banners
  }
  // 默认占位
  return [{
    id: 0,
    title: '武峥:火源AI创始人',
    image_url: '',
    link_url: '',
    link_type: 'none' as const,
    position: 'home_top' as const,
    sort_order: 0
  }]
})

const handleBannerTap = (item: BannerItem) => {
  if (item.link_type === 'internal' && item.link_url) {
    uni.navigateTo({ url: item.link_url })
  } else if (item.link_type === 'external' && item.link_url) {
    uni.navigateTo({ url: `/pages/webview/index?url=${encodeURIComponent(item.link_url)}` })
  }
}
</script>

<style scoped lang="scss">
@import '@/styles/_variables.scss';

.founder-message {
  margin-bottom: $spacing-md;
  padding: 0 $spacing-md;

  .founder-swiper {
    height: 350rpx;
  }

        .banner-card {
          width: 100%;
          height: 100%;
          border-radius: $radius-lg;
          overflow: hidden;
        }
    
        .banner-image {
          width: 100%;
          height: 100%;
          display: block;
        }
  .message-card {
    position: relative;
    width: 100%;
    height: 100%;
    background: #1A1A2E;
    border-radius: $radius-lg;
    padding: 48rpx 36rpx;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    box-sizing: border-box;

    .message-tag {
      font-size: 20rpx;
      color: rgba(255, 255, 255, 0.6);
      letter-spacing: 2rpx;
      text-transform: uppercase;
      margin-bottom: 24rpx;
      font-weight: 400;
    }

    .message-title {
      font-size: 44rpx;
      font-weight: 700;
      color: $white;
      line-height: 1.4;
      margin-bottom: 16rpx;
    }

    .message-desc {
      font-size: 28rpx;
      color: rgba(255, 255, 255, 0.9);
      line-height: 1.6;
      margin-bottom: 32rpx;
    }

    .message-btn {
      align-self: flex-start;
      padding: 0 10rpx;
      background: $white;
      border-radius: 100rpx;
      border: 2rpx solid $white;

      .btn-text {
        font-size: 20rpx;
        font-weight: 600;
        color: #1A1A2E;
      }
    }
  }
}
</style>
