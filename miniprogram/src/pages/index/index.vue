<template>
  <scroll-view scroll-y class="container">
    <!-- FOUNDER'S MESSAGE 轮播区域 -->
    <FounderMessage />

    <!-- 智能体动态通知条 -->
    <NotificationBar />

    <!-- 功能入口区域 -->
    <FeatureGrid />

    <!-- 运营闪念区域 -->
    <ArticleList />

    <!-- 最近落地区域 -->
    <RecentLanding />

    <view class="bottom-gap" />
  </scroll-view>
</template>

<script setup lang="ts">
import FounderMessage from './components/FounderMessage.vue'
import NotificationBar from './components/NotificationBar.vue'
import FeatureGrid from './components/FeatureGrid.vue'
import ArticleList from './components/ArticleList.vue'
import RecentLanding from './components/RecentLanding.vue'
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
