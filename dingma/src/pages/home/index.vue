<template>
  <scroll-view scroll-y class="page" enhanced :show-scrollbar="false">
    <view class="banner-wrap">
      <image class="banner-bg" :src="bannerUrl" mode="aspectFill" />
      <view class="banner-mask" />
      <view class="banner-inner" :style="{ paddingTop: bannerTopPx + 'px' }">
        <view class="banner-top-row">
          <view class="title-block">
            <text class="banner-title">顶妈 AI 创富助手</text>
            <view class="tag-pill">
              <text class="tag-pill-text">您身边不停歇的私人导师</text>
            </view>
          </view>
          <view class="info-btn" @tap="onBannerInfo">
            <text class="info-icon">i</text>
          </view>
        </view>
        <view class="banner-bottom-row">
          <view class="price-block">
            <text class="promo-line">创富年费特惠</text>
            <text class="price-line">¥365 /年</text>
          </view>
          <view class="learn-btn" @tap="onLearnDingma">
            <text class="learn-btn-text">了解顶妈</text>
            <text class="learn-btn-arrow">›</text>
          </view>
        </view>
      </view>
    </view>

    <view class="section">
      <view class="section-head">
        <view class="section-head-left">
          <view class="wand-wrap">
            <SvgIcon name="linggan3" :size="40" color="#3B82F6" />
          </view>
          <text class="section-title">创作工具箱</text>
        </view>
        <text class="section-count">12 TOOLS</text>
      </view>

      <view class="tool-grid">
        <view
          v-for="item in tools"
          :key="item.id"
          class="tool-card"
          :style="{ background: item.bg }"
          @tap="onToolTap(item)"
        >
          <view v-if="item.hot" class="hot-ribbon">
            <text class="hot-ribbon-text">HOT</text>
          </view>
          <view class="tool-icon-wrap" :style="{ background: item.iconWrapBg }">
            <SvgIcon :name="item.icon" :size="44" :color="item.iconColor" />
          </view>
          <text class="tool-title">{{ item.title }}</text>
          <text class="tool-desc">{{ item.desc }}</text>
        </view>
      </view>
    </view>

    <view class="page-bottom-space" />
  </scroll-view>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { DINGMA_HOME_BANNER_URL } from '@/constants/tenant'
import { useSafeArea } from '@/composables/useSafeArea'
import SvgIcon from '@/components/base/SvgIcon.vue'

const bannerUrl = DINGMA_HOME_BANNER_URL
const { safeArea, updateSafeArea } = useSafeArea()
const bannerTopPx = ref(12)

interface ToolDef {
  id: string
  title: string
  desc: string
  bg: string
  iconWrapBg: string
  icon: string
  iconColor: string
  hot?: boolean
}

const tools: ToolDef[] = [
  {
    id: 'moment',
    title: '爆款朋友圈',
    desc: '一键生成顶妈同款风格文案',
    bg: '#E8F1FF',
    iconWrapBg: 'rgba(59, 130, 246, 0.22)',
    icon: 'hotspot',
    iconColor: '#2563EB',
    hot: true
  },
  {
    id: 'video',
    title: '短视频脚本',
    desc: '5分钟拍出高转化的早餐视频',
    bg: '#EDE9FF',
    iconWrapBg: 'rgba(124, 58, 237, 0.2)',
    icon: 'process',
    iconColor: '#7C3AED',
    hot: true
  },
  {
    id: 'reply',
    title: '高情商回复',
    desc: '解决私域咨询时的各种尴尬',
    bg: '#E8F8EF',
    iconWrapBg: 'rgba(16, 185, 129, 0.22)',
    icon: 'service',
    iconColor: '#059669'
  },
  {
    id: 'naming',
    title: '新品起名',
    desc: '让你的产品自带流量光环',
    bg: '#FFF0E8',
    iconWrapBg: 'rgba(234, 88, 12, 0.18)',
    icon: 'linggan',
    iconColor: '#EA580C'
  }
]

function onBannerInfo() {
  uni.showModal({
    title: '顶妈 AI 创富助手',
    content: '面向内容创作者的随身 AI 帮手，助你高效产出文案、脚本与话术。',
    showCancel: false,
    confirmText: '知道了'
  })
}

function onLearnDingma() {
  uni.showModal({
    title: '了解顶妈',
    content:
      '顶妈团队将多年私域实战与新媒体经验沉淀为可复用的方法论，本产品提供 AI 创富工具与进阶经营能力。',
    confirmText: '好的',
    showCancel: false
  })
}

function onToolTap(_item: ToolDef) {
  uni.switchTab({ url: '/pages/quick-entries/index' })
}

onMounted(() => {
  updateSafeArea()
  const top =
    typeof safeArea.value.top === 'number' && safeArea.value.top > 0
      ? safeArea.value.top
      : safeArea.value.statusBarHeight || 0
  bannerTopPx.value = Math.ceil(top > 0 ? top + 6 : 12)
})
</script>

<style scoped lang="scss">
$page-bg: #f4f6f8;

.page {
  min-height: 100vh;
  background: $page-bg;
  box-sizing: border-box;
}

.banner-wrap {
  position: relative;
  margin: 24rpx 28rpx 0;
  height: 360rpx;
  border-radius: 28rpx;
  overflow: hidden;
  box-shadow: 0 12rpx 40rpx rgba(33, 37, 41, 0.12);
}

.banner-bg {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
}

.banner-mask {
  position: absolute;
  inset: 0;
  background: linear-gradient(
    180deg,
    rgba(0, 0, 0, 0.28) 0%,
    rgba(0, 0, 0, 0.45) 100%
  );
}

.banner-inner {
  position: relative;
  z-index: 2;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  box-sizing: border-box;
  height: 100%;
  padding-left: 32rpx;
  padding-right: 28rpx;
  padding-bottom: 28rpx;
}

.banner-top-row {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
}

.title-block {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 14rpx;
}

.banner-title {
  font-size: 40rpx;
  font-weight: 700;
  color: #fff;
  letter-spacing: 0.02em;
  text-shadow: 0 4rpx 16rpx rgba(0, 0, 0, 0.25);
}

.tag-pill {
  align-self: flex-start;
  padding: 8rpx 20rpx;
  border-radius: 999rpx;
  background: rgba(34, 40, 49, 0.55);
  border: 1rpx solid rgba(255, 255, 255, 0.12);
}

.tag-pill-text {
  font-size: 22rpx;
  color: rgba(255, 255, 255, 0.94);
}

.info-btn {
  width: 52rpx;
  height: 52rpx;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.28);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  margin-left: 16rpx;
}

.info-btn:active {
  opacity: 0.85;
}

.info-icon {
  font-size: 26rpx;
  font-weight: 700;
  font-style: italic;
  color: #fff;
}

.banner-bottom-row {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 24rpx;
}

.promo-line {
  display: block;
  font-size: 22rpx;
  color: rgba(255, 255, 255, 0.88);
  margin-bottom: 6rpx;
}

.price-line {
  display: block;
  font-size: 48rpx;
  font-weight: 700;
  color: #fff;
  letter-spacing: 0.02em;
}

.learn-btn {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  gap: 4rpx;
  padding: 16rpx 28rpx;
  border-radius: 999rpx;
  background: #fff;
  box-shadow: 0 6rpx 24rpx rgba(0, 0, 0, 0.12);
}

.learn-btn:active {
  opacity: 0.92;
}

.learn-btn-text {
  font-size: 26rpx;
  font-weight: 600;
  color: #2563eb;
}

.learn-btn-arrow {
  font-size: 28rpx;
  font-weight: 600;
  color: #2563eb;
  line-height: 1;
}

.section {
  margin-top: 36rpx;
  padding: 0 28rpx 24rpx;
}

.section-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 24rpx;
}

.section-head-left {
  display: flex;
  align-items: center;
  gap: 12rpx;
}

.wand-wrap {
  width: 48rpx;
  height: 48rpx;
  display: flex;
  align-items: center;
  justify-content: center;
}

.section-title {
  font-size: 34rpx;
  font-weight: 700;
  color: #1d2129;
}

.section-count {
  font-size: 22rpx;
  font-weight: 500;
  color: #c0c4cc;
  letter-spacing: 0.06em;
}

.tool-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20rpx;
}

.tool-card {
  position: relative;
  border-radius: 24rpx;
  padding: 28rpx 24rpx 28rpx;
  min-height: 200rpx;
  box-sizing: border-box;
  overflow: hidden;
  box-shadow: 0 4rpx 24rpx rgba(0, 0, 0, 0.04);
}

.tool-card:active {
  opacity: 0.92;
}

.hot-ribbon {
  position: absolute;
  top: 16rpx;
  right: -36rpx;
  width: 140rpx;
  padding: 6rpx 0;
  background: linear-gradient(90deg, #f87171, #ef4444);
  transform: rotate(45deg);
  transform-origin: center;
  box-shadow: 0 4rpx 12rpx rgba(239, 68, 68, 0.35);
}

.hot-ribbon-text {
  display: block;
  text-align: center;
  font-size: 18rpx;
  font-weight: 800;
  color: #fff;
  letter-spacing: 0.04em;
}

.tool-icon-wrap {
  width: 64rpx;
  height: 64rpx;
  border-radius: 18rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 20rpx;
}

.tool-title {
  display: block;
  font-size: 30rpx;
  font-weight: 700;
  color: #1d2129;
  margin-bottom: 10rpx;
}

.tool-desc {
  display: block;
  font-size: 22rpx;
  color: #64748b;
  line-height: 1.45;
}

.page-bottom-space {
  height: calc(28rpx + env(safe-area-inset-bottom));
  height: calc(28rpx + constant(safe-area-inset-bottom));
}
</style>
