<template>
  <view class="recent-landing">
    <BaseSection>
      最近落地
      <template #right>
        <view @tap="handleViewAll">
          <text class="view-all-text">全部</text>
        </view>
      </template>
    </BaseSection>

    <view v-if="displayList.length > 0" class="landing-list">
      <navigator
        v-for="article in displayList"
        :key="article.id"
        class="landing-item"
        :url="`/pages/article/detail?id=${article.id}`"
        open-type="navigate"
        hover-class="landing-item--hover"
        hover-stay-time="70"
      >
        <image
          v-if="article.cover_image"
          class="landing-cover"
          :src="article.cover_image"
          mode="aspectFill"
        />
        <view v-else class="landing-cover landing-cover--placeholder">
          <text class="placeholder-icon">📄</text>
        </view>
        <view class="landing-body">
          <text class="landing-title">{{ article.title }}</text>
          <text v-if="article.summary" class="landing-summary">{{ article.summary }}</text>
          <view class="landing-meta">
            <text v-if="formatTime(article.publish_time)" class="meta-text">{{
              formatTime(article.publish_time)
            }}</text>
            <text class="meta-text">阅读 {{ article.view_count ?? 0 }}</text>
          </view>
        </view>
      </navigator>
    </view>
  </view>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import BaseSection from '@/components/base/BaseSection.vue'
import type { ArticleItem } from '@/api/home'

const props = defineProps<{
  articles?: ArticleItem[]
}>()

const displayList = computed(() => (props.articles && props.articles.length > 0 ? props.articles : []))

function handleViewAll() {
  uni.navigateTo({ url: '/pages/article/list?category=05' })
}

function formatTime(timeStr?: string): string {
  if (!timeStr) return ''
  try {
    const date = new Date(timeStr)
    const now = new Date()
    const diff = now.getTime() - date.getTime()
    const minutes = Math.floor(diff / 60000)
    const hours = Math.floor(diff / 3600000)
    const days = Math.floor(diff / 86400000)
    if (minutes < 1) return '刚刚'
    if (minutes < 60) return `${minutes}分钟前`
    if (hours < 24) return `${hours}小时前`
    if (days < 7) return `${days}天前`
    const month = date.getMonth() + 1
    const day = date.getDate()
    const year = date.getFullYear()
    const currentYear = now.getFullYear()
    if (year === currentYear) {
      return `${month}月${day}日`
    }
    return `${year}年${month}月${day}日`
  } catch {
    return timeStr
  }
}
</script>

<style scoped lang="scss">
@import '@/styles/_variables.scss';

.recent-landing {
  padding: 0 $spacing-md;
  margin-bottom: $spacing-md;
}

.view-all-text {
  font-size: 20rpx;
  color: $text-second;
}

.landing-list {
  display: flex;
  flex-direction: column;
  gap: 24rpx;
}

.landing-item {
  display: flex;
  flex-direction: row;
  background: $white;
  border-radius: $radius-lg;
  border: 1rpx solid $border-color;
  overflow: hidden;
  padding: 20rpx;
  box-sizing: border-box;

  &--hover {
    opacity: 0.92;
  }
}

.landing-cover {
  width: 200rpx;
  height: 140rpx;
  border-radius: $radius-md;
  flex-shrink: 0;
  background: $bg-color;

  &--placeholder {
    display: flex;
    align-items: center;
    justify-content: center;
  }

  .placeholder-icon {
    font-size: 48rpx;
    opacity: 0.35;
  }
}

.landing-body {
  flex: 1;
  min-width: 0;
  margin-left: 20rpx;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
}

.landing-title {
  font-size: 28rpx;
  font-weight: 700;
  color: $text-main;
  line-height: 1.4;
  display: -webkit-box;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2;
  overflow: hidden;
}

.landing-summary {
  margin-top: 8rpx;
  font-size: 22rpx;
  color: $text-second;
  line-height: 1.4;
  display: -webkit-box;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2;
  overflow: hidden;
}

.landing-meta {
  margin-top: 12rpx;
  display: flex;
  flex-wrap: wrap;
  gap: 16rpx;
}

.meta-text {
  font-size: 20rpx;
  color: $text-second;
}
</style>
