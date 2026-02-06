<template>
 <view class="article-detail-page">
    <!-- 顶部导航栏 -->
   <BaseHeader title="文章详情" @back="goBack">
      <template #right>
        <view @tap="handleShare">
          <text class="share-icon">分享</text>
        </view>
     </template>
    </BaseHeader>

    <!-- 加载状态 -->
    <view class="loading-container" v-if="isLoading">
      <view class="loading-spinner"></view>
      <text class="loading-text">加载中...</text>
    </view>

    <!-- 错误状态 -->
    <view class="error-container" v-else-if="error">
      <text class="error-icon">⚠️</text>
      <text class="error-text">{{ error }}</text>
      <view class="retry-btn" @tap="fetchArticleDetail">
        <text class="retry-text">重试</text>
      </view>
    </view>

    <!-- 文章内容 -->
    <scroll-view class="article-content" scroll-y v-else-if="article">
      <!-- 封面图 -->
      <image
        v-if="article.cover_image"
        :src="article.cover_image"
        mode="aspectFill"
        class="cover-image"
        @tap="previewImage"
      />

      <!-- 文章信息卡片 -->
      <view class="article-info-card">
        <!-- 标题 -->
        <text class="article-title">{{ article.title }}</text>

        <!-- 摘要 -->
        <text v-if="article.summary" class="article-summary">{{ article.summary }}</text>

        <!-- 标签和元信息 -->
        <view class="article-meta">
          <!-- 标签 -->
          <view class="tags-container" v-if="article.tags && article.tags.length > 0">
            <view
              v-for="tag in article.tags"
              :key="tag"
              class="tag-item"
            >
              {{ tag }}
            </view>
          </view>

          <!-- 发布时间和浏览量 -->
          <view class="meta-info">
            <text v-if="article.publish_time" class="meta-item">
              {{ formatTime(article.publish_time) }}
            </text>
            <text class="meta-item">
              阅读 {{ article.view_count || 0 }}
            </text>
          </view>
        </view>
      </view>

      <!-- 文章正文 -->
      <view class="article-body-card">
        <rich-text
          :nodes="article.content"
          class="article-body"
        />
      </view>

      <!-- 底部占位 -->
      <view class="bottom-spacer"></view>
    </scroll-view>
  </view>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { onLoad, onShareAppMessage, onShareTimeline } from '@dcloudio/uni-app'
import { getArticleDetail, type ArticleItem } from '@/api/article'
import BaseHeader from '@/components/base/BaseHeader.vue'

// 文章ID
const articleId = ref<number>(0)

// 文章数据
const article = ref<ArticleItem | null>(null)

// 加载状态
const isLoading = ref(false)

// 错误信息
const error = ref<string>('')

// 页面加载时获取文章ID
onLoad((options: any) => {
  if (options.id) {
    articleId.value = parseInt(options.id)
    fetchArticleDetail()
  } else {
    error.value = '文章ID不存在'
  }
})

// 获取文章详情
async function fetchArticleDetail() {
  if (!articleId.value) return

  isLoading.value = true
  error.value = ''

  try {
    const res = await getArticleDetail(articleId.value)
    if (res && res.code === 200 && res.data) {
      article.value = res.data
      
      // 设置页面标题
      uni.setNavigationBarTitle({
        title: res.data.title || '文章详情'
      })
    } else {
      error.value = res?.msg || '获取文章详情失败'
    }
  } catch (err: any) {
    console.error('获取文章详情失败:', err)
    error.value = err.message || '加载失败，请稍后重试'
  } finally {
    isLoading.value = false
  }
}

// 返回上一页
function goBack() {
  uni.navigateBack({
    fail: () => {
      uni.switchTab({ url: '/pages/index/index' })
    }
  })
}

// 分享功能
function handleShare() {
  uni.showShareMenu({
    withShareTicket: true,
    menus: ['shareAppMessage', 'shareTimeline']
  })
}

// 分享给好友
onShareAppMessage(() => {
  if (!article.value) {
    return {
      title: '火源灵感火花 - AI驱动的智能创作平台',
      path: '/pages/index/index',
      imageUrl: '/static/logo.png'
    }
  }

  return {
    title: article.value.title,
    path: `/pages/article/detail?id=${article.value.id}`,
    imageUrl: article.value.cover_image || '/static/logo.png'
  }
})

// 分享到朋友圈
onShareTimeline(() => {
  if (!article.value) {
    return {
      title: '火源灵感火花 - AI驱动的智能创作平台',
      query: '',
      imageUrl: '/static/logo.png'
    }
  }

  return {
    title: article.value.title,
    query: `id=${article.value.id}`,
    imageUrl: article.value.cover_image || '/static/logo.png'
  }
})

// 预览封面图
function previewImage() {
  if (!article.value?.cover_image) return
  
  uni.previewImage({
    urls: [article.value.cover_image],
    current: article.value.cover_image
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

.article-detail-page {
  min-height: 100vh;
  background: $bg-color;
  position: relative;
}

.share-icon {
  font-size: 28rpx;
  color: $brand-orange;
}

// 加载状态
.loading-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 200rpx 40rpx;
  gap: 24rpx;
}

.loading-spinner {
  width: 60rpx;
  height: 60rpx;
  border: 4rpx solid #E5E7EB;
  border-top-color: $brand-orange;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
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

// 错误状态
.error-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 200rpx 40rpx;
  gap: 32rpx;
}

.error-icon {
  font-size: 80rpx;
  opacity: 0.6;
}

.error-text {
  font-size: 28rpx;
  color: $color-error;
  text-align: center;
}

.retry-btn {
  padding: 20rpx 40rpx;
  background: $brand-orange;
  border-radius: $radius-md;
}

.retry-text {
  font-size: 28rpx;
  color: $white;
  font-weight: 600;
}

// 文章内容区域
.article-content {
  padding: 0;
}

// 封面图
.cover-image {
  width: 100%;
  height: 400rpx;
  background: $bg-light;
}

// 文章信息卡片
.article-info-card {
  background: $white;
  padding: $spacing-lg;
  margin-bottom: $spacing-md;
}

.article-title {
  display: block;
  font-size: $font-size-xxl;
  font-weight: 700;
  color: $text-main;
  line-height: 1.5;
  margin-bottom: $spacing-md;
}

.article-summary {
  display: block;
  font-size: $font-size-md;
  color: $text-second;
  line-height: 1.6;
  margin-bottom: $spacing-md;
}

.article-meta {
  display: flex;
  flex-direction: column;
  gap: $spacing-md;
}

.tags-container {
  display: flex;
  flex-wrap: wrap;
  gap: $spacing-sm;
}

.tag-item {
  padding: 8rpx 16rpx;
  background: rgba(243, 112, 33, 0.1);
  color: $brand-orange;
  font-size: $font-size-xs;
  border-radius: $radius-sm;
}

.meta-info {
  display: flex;
  gap: $spacing-md;
  align-items: center;
}

.meta-item {
  font-size: $font-size-sm;
  color: $text-second;
}

// 文章正文卡片
.article-body-card {
  background: $white;
  margin-bottom: $spacing-md;
  min-height: 400rpx;
}

.article-body {
  font-size: $font-size-md;
  color: $text-main;
  line-height: 1.8;
  word-wrap: break-word;
  
  // 富文本内容样式
  :deep(p) {
    margin-bottom: $spacing-md;
  }
  
  :deep(img) {
    max-width: 100%;
    height: auto;
    border-radius: $radius-md;
    margin: $spacing-md 0;
  }
  
  :deep(h1),
  :deep(h2),
  :deep(h3) {
    font-weight: 700;
    margin: $spacing-lg 0 $spacing-md;
    color: $text-main;
  }
  
  :deep(h1) {
    font-size: $font-size-xxl;
  }
  
  :deep(h2) {
    font-size: $font-size-xl;
  }
  
  :deep(h3) {
    font-size: $font-size-lg;
  }
  
  :deep(ul),
  :deep(ol) {
    padding-left: $spacing-lg;
    margin-bottom: $spacing-md;
  }
  
  :deep(li) {
    margin-bottom: $spacing-sm;
  }
  
  :deep(blockquote) {
    border-left: 4rpx solid $brand-orange;
    padding-left: $spacing-md;
    margin: $spacing-md 0;
    color: $text-second;
    font-style: italic;
  }
  
  :deep(code) {
    background: $bg-light;
    padding: 4rpx 8rpx;
    border-radius: $radius-sm;
    font-family: 'Courier New', monospace;
    font-size: $font-size-sm;
  }
  
  :deep(pre) {
    background: $bg-light;
    padding: $spacing-md;
    border-radius: $radius-md;
    overflow-x: auto;
    margin: $spacing-md 0;
  }
  
  :deep(a) {
    color: $brand-orange;
    text-decoration: underline;
  }
}

// 底部占位
.bottom-spacer {
  height: $spacing-xl;
}
</style>

