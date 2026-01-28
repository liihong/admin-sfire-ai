<template>
  <scroll-view scroll-y class="container">
    <!-- FOUNDER'S MESSAGE 轮播区域 -->
   <FounderMessage :founder-stories="homeData.founder_stories" />

  <!-- 公告通知条 -->
    <NotificationBar v-if="homeData.announcements && homeData.announcements.length > 0"
      :announcements="homeData.announcements" />

    <!-- 功能入口区域 -->
   <FeatureGrid :feature-list="homeData.featured_modules" />

  <!-- 运营干货区域 -->
    <ArticleList :operation-articles="homeData.operation_articles" />

    <!-- 最近落地区域 -->
    <RecentLanding />

    <view class="bottom-gap" />
  </scroll-view>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { onShareAppMessage, onShareTimeline } from '@dcloudio/uni-app'
import { getHomeContent, type HomeContentResponse } from '@/api/home'
import FounderMessage from './components/FounderMessage.vue'
import NotificationBar from './components/NotificationBar.vue'
import FeatureGrid from './components/FeatureGrid.vue'
import ArticleList from './components/ArticleList.vue'
import RecentLanding from './components/RecentLanding.vue'

// 首页数据
const homeData = ref<HomeContentResponse>({
  banners: {
    home_top: [],
    home_middle: [],
    home_bottom: []
  },
  founder_stories: [],
  operation_articles: [],
  announcements: [],
  customer_cases: [],
  featured_modules: []
})

const isLoading = ref(false)

// 获取首页内容
const fetchHomeContent = async () => {
  isLoading.value = true
  try {
    const res = await getHomeContent()
    if (res && res.code === 200 && res.data) {
      // res.data 已经是 HomeContentResponse 类型
      homeData.value = {
        banners: res.data.banners || {
          home_top: [],
          home_middle: [],
          home_bottom: []
        },
        founder_stories: res.data.founder_stories || [],
        operation_articles: res.data.operation_articles || [],
        announcements: res.data.announcements || [],
        customer_cases: res.data.customer_cases || [],
        featured_modules: res.data.featured_modules || []
      }
    }
  } catch (error) {
    console.error('获取首页内容失败:', error)
  } finally {
    isLoading.value = false
  }
}

onMounted(() => {
  fetchHomeContent()
})

/**
 * 分享给好友
 * 用户点击右上角分享按钮时触发
 */
onShareAppMessage(() => {
  return {
    title: '火源灵感火花 - AI驱动的智能创作平台',
    path: '/pages/index/index',
    imageUrl: '/static/logo.png' // 分享图片，使用应用logo
  }
})

/**
 * 分享到朋友圈
 * 用户点击右上角菜单中的"分享到朋友圈"时触发
 */
onShareTimeline(() => {
  return {
    title: '火源灵感火花 - AI驱动的智能创作平台',
    query: '', // 分享参数，可根据需要添加
    imageUrl: '/static/logo.png' // 分享图片，使用应用logo
  }
})
</script>

<style scoped lang="scss">
@import '@/styles/_variables.scss';

.container {
  min-height: 100vh;
  background: $bg-color;
  padding-top: $spacing-md;
  padding-bottom: $spacing-xl;
  box-sizing: border-box;
}

.bottom-gap {
  height: $spacing-xl;
}
</style>
