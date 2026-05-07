<template>
  <view class="article-list-page">
    <!-- 页面头部 -->
    <BaseHeader :title="categoryLabel" @back="goBack" />

    <!-- 列表区域 -->
    <scroll-view
      class="list-wrapper"
      scroll-y
      :refresher-enabled="true"
      @refresherrefresh="onRefresh"
      :refresher-triggered="isRefreshing"
      @scrolltolower="onLoadMore"
      :lower-threshold="100"
    >
      <!-- 空状态 -->
      <view class="empty-state" v-if="!isLoading && articleList.length === 0">
        <text class="empty-icon">📄</text>
        <text class="empty-title">暂无文章</text>
        <text class="empty-desc">该分类下还没有文章内容</text>
      </view>

      <!-- 文章列表 -->
      <view class="article-list" v-else>
        <view
          class="article-item"
          v-for="article in articleList"
          :key="article.id"
          @tap="goToDetail(article.id)"
        >
          <!-- 封面图 -->
          <!-- <image
            v-if="article.cover_image"
            :src="article.cover_image"
            mode="aspectFill"
            class="article-cover"
          />
          <view v-else class="article-cover-placeholder">
            <text class="placeholder-icon">📄</text>
          </view> -->

          <!-- 文章信息 -->
          <view class="article-info">
            <text class="article-title">{{ article.title }}</text>
            <text v-if="article.summary" class="article-summary">{{ article.summary }}</text>
            <view class="article-meta">
              <text v-if="article.publish_time" class="meta-item">
                {{ formatTime(article.publish_time) }}
              </text>
              <text class="meta-item">阅读 {{ article.view_count || 0 }}</text>
            </view>
          </view>
        </view>
      </view>

      <!-- 加载更多提示 -->
      <view class="load-more" v-if="articleList.length > 0">
        <text class="load-more-text" v-if="isLoadingMore">加载中...</text>
        <text class="load-more-text" v-else-if="hasMore">上拉加载更多</text>
        <text class="load-more-text" v-else>没有更多数据了</text>
      </view>

      <!-- 底部占位 -->
      <view class="list-footer-spacer"></view>
    </scroll-view>

    <!-- Loading 状态 -->
    <view class="loading-overlay" v-if="isLoading && articleList.length === 0">
      <view class="loading-spinner"></view>
      <text class="loading-text">加载中...</text>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { onLoad } from '@dcloudio/uni-app'
import { getArticleList, type ArticleItem, type ArticleListResponse } from '@/api/article'
import BaseHeader from '@/components/base/BaseHeader.vue'

// 文章类型（sys_dict article_category：01-05）
const category = ref<string | undefined>(undefined)

// 分类标签
const categoryLabel = computed(() => {
  const labelMap: Record<string, string> = {
    '01': '商业底牌',
    '02': '流量心法',
    '03': '实操手册',
    '04': '创始人说',
    '05': '最近落地'
  }
  return labelMap[category.value || ''] || '全部文章'
})

// 文章列表
const articleList = ref<ArticleItem[]>([])
const isLoading = ref(false)
const isRefreshing = ref(false)
const isLoadingMore = ref(false)
const hasMore = ref(true)
const currentPage = ref(1)
const pageSize = ref(10)

// 页面加载时获取分类参数
onLoad((options: any) => {
  if (options.category) {
    category.value = options.category as any
  }
  loadArticles(1, true)
})

// 加载文章列表
async function loadArticles(pageNum: number, isRefresh: boolean = false) {
  // 防止重复加载
  if (isLoading.value || isLoadingMore.value) return

  if (isRefresh) {
    isLoading.value = true
    currentPage.value = 1
  } else {
    isLoadingMore.value = true
  }

  try {
    const response = await getArticleList(category.value, pageNum, pageSize.value)

    // 检查响应格式
    if (!response) {
      throw new Error('响应数据为空')
    }

    // 检查响应码
    if (response.code === 200) {
      // 成功响应，处理数据
      const data = response.data as ArticleListResponse | undefined
      if (data) {
        const list = data.list || []
        const total = data.total || 0

        if (isRefresh) {
          articleList.value = list
        } else {
          articleList.value = [...articleList.value, ...list]
        }

        // 判断是否还有更多数据
        const currentTotal = articleList.value.length
        hasMore.value = currentTotal < total && list.length === pageSize.value

        if (!isRefresh) {
          currentPage.value = pageNum
        }
      } else {
        // data 为空，可能是响应格式错误
        console.warn('响应数据格式异常:', response)
        if (isRefresh) {
          articleList.value = []
        }
        hasMore.value = false
      }
    } else {
      // 业务错误，显示错误消息
      const errorMsg = response.msg || response.message || '加载失败'
      uni.showToast({
        title: errorMsg,
        icon: 'none'
      })
      // 如果是刷新操作，清空列表
      if (isRefresh) {
        articleList.value = []
        hasMore.value = false
      }
    }
  } catch (error: any) {
    console.error('加载文章列表失败:', error)
    const errorMsg = error.message || error.msg || '加载失败，请稍后重试'
    uni.showToast({
      title: errorMsg,
      icon: 'none'
    })
    // 如果是刷新操作，清空列表
    if (isRefresh) {
      articleList.value = []
      hasMore.value = false
    }
  } finally {
    isLoading.value = false
    isLoadingMore.value = false
    isRefreshing.value = false
  }
}

// 下拉刷新
async function onRefresh() {
  isRefreshing.value = true
  await loadArticles(1, true)
}

// 加载更多
function onLoadMore() {
  if (!hasMore.value || isLoadingMore.value || isLoading.value) return
  loadArticles(currentPage.value + 1, false)
}

// 返回上一页
function goBack() {
  uni.navigateBack({
    fail: () => {
      uni.switchTab({ url: '/pages/home/index' })
    }
  })
}

// 跳转到详情页
function goToDetail(id: number) {
  uni.navigateTo({
    url: `/pages/article/detail?id=${id}`
  })
}

// 格式化时间
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

    // 超过7天显示具体日期
    const month = date.getMonth() + 1
    const day = date.getDate()
    const year = date.getFullYear()
    const currentYear = now.getFullYear()

    if (year === currentYear) {
      return `${month}月${day}日`
    }
    return `${year}年${month}月${day}日`
  } catch (error) {
    return timeStr
  }
}
</script>

<style lang="scss" scoped>
@import '@/styles/_variables.scss';

.article-list-page {
  min-height: 100vh;
  background: $bg-color;
}

// 列表区域
.list-wrapper {
  padding: $spacing-md 32rpx;
  min-height: calc(100vh - 180rpx);
}

// 空状态
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 200rpx 40rpx;
  text-align: center;
}

.empty-icon {
  font-size: 120rpx;
  margin-bottom: 32rpx;
  opacity: 0.6;
}

.empty-title {
  font-size: 32rpx;
  font-weight: 600;
  color: $text-main;
  margin-bottom: 16rpx;
}

.empty-desc {
  font-size: 28rpx;
  color: $text-second;
}

// 文章列表
.article-list {
  padding-bottom: 40rpx;
}

.article-item {
  background: $white;
  border-radius: $radius-lg;
  padding: $spacing-md;
  margin-bottom: $spacing-md;
  display: flex;
  gap: $spacing-md;
  box-shadow: $card-shadow;
}

.article-cover {
  width: 200rpx;
  height: 150rpx;
  border-radius: $radius-md;
  flex-shrink: 0;
  background: $bg-light;
}

.article-cover-placeholder {
  width: 200rpx;
  height: 150rpx;
  border-radius: $radius-md;
  flex-shrink: 0;
  background: $bg-light;
  display: flex;
  align-items: center;
  justify-content: center;
}

.placeholder-icon {
  font-size: 60rpx;
  opacity: 0.3;
}

.article-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: $spacing-sm;
  min-width: 0;
}

.article-title {
  font-size: $font-size-lg;
  font-weight: 600;
  color: $text-main;
  line-height: 1.5;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}

.article-summary {
  font-size: $font-size-sm;
  color: $text-second;
  line-height: 1.5;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}

.article-meta {
  display: flex;
  gap: $spacing-md;
  align-items: center;
  margin-top: auto;
}

.meta-item {
  font-size: $font-size-xs;
  color: $text-second;
}

// 加载更多
.load-more {
  padding: 40rpx 0;
  text-align: center;
}

.load-more-text {
  font-size: 26rpx;
  color: $text-second;
}

// 底部占位
.list-footer-spacer {
  height: 40rpx;
}

// Loading 状态
.loading-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(255, 255, 255, 0.9);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  z-index: 100;
}

.loading-spinner {
  width: 60rpx;
  height: 60rpx;
  border: 4rpx solid #e5e7eb;
  border-top-color: $brand-orange;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 24rpx;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.loading-text {
  font-size: 28rpx;
  color: $text-second;
}
</style>

