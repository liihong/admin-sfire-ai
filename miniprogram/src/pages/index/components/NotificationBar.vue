<template>
 <view class="notification-bar" v-if="announcements && announcements.length > 0">
    <view class="notification-left">
     <SvgIcon name="notice" size="32" color="#FF8800" />
      <text class="notification-label">上新</text>
      <view class="divider"></view>
    </view>
    <view class="notification-content">
     <text class="notification-text">{{ latestAnnouncement?.title || '暂无公告' }}</text>
   </view>
  </view>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { ArticleItem } from '@/api/home'
import SvgIcon from '@/components/base/SvgIcon.vue'

// 接收父组件传递的公告数据
const props = defineProps<{
  announcements?: ArticleItem[]
}>()

// 获取最新公告
const latestAnnouncement = computed(() => {
  if (props.announcements && props.announcements.length > 0) {
    return props.announcements[0]
  }
  return null
})

const handleClick = () => {
  if (latestAnnouncement.value && latestAnnouncement.value.id) {
    uni.navigateTo({ url: `/pages/article/detail?id=${latestAnnouncement.value.id}` })
  }
}
</script>

<style scoped lang="scss">
@import '@/styles/_variables.scss';

.notification-bar {
  display: flex;
  align-items: center;
  padding: 24rpx 32rpx;
  background: $white;
  margin-bottom: $spacing-md;
  margin-left: $spacing-md;
  margin-right: $spacing-md;
  border-radius: $radius-md;

  .notification-left {
    display: flex;
    align-items: center;
    margin-right: 16rpx;
    gap: 8rpx;

    .notification-label {
      font-size: 24rpx;
      font-weight: 600;
      color: $brand-orange;
    }

    .divider {
      width: 2rpx;
      height: 32rpx;
      background: #E4E7ED;
      margin-left: 16rpx;
      margin-right: 16rpx;
    }
  }

  .notification-content {
    flex: 1;
    overflow: hidden;

    .notification-text {
      font-size: 24rpx;
      color: $text-second;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }
  }
}
</style>
