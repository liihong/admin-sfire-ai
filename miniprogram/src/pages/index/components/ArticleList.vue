<template>
  <view class="article-list">
    <view class="article-header">
      <view class="header-left">
        <text class="section-title">运营干货</text>
      </view>
      <view class="header-right" @tap="handleViewAll">
        <text class="view-all-text">全部</text>
      </view>
    </view>
    <scroll-view class="article-scroll" scroll-x>
      <view class="article-container">
        <view
          class="article-card"
          v-for="(article, index) in articleList"
          :key="article.id"
          :class="{ 'card-orange': index === 0, 'card-white': index === 1 }"
          @tap="handleArticleClick(article)"
        >
          <view class="article-tag">{{ article.tag }}</view>
          <view class="article-title">{{ article.title }}</view>
          <view class="article-action">
            <text class="action-text">{{ index === 0 ? '立即研读' : '去看看' }}</text>
            <text class="action-arrow">></text>
          </view>
        </view>
      </view>
    </scroll-view>
  </view>
</template>

<script setup lang="ts">
import { reactive } from 'vue'

export interface ArticleItem {
  id: number
  tag: string
  title: string
  route?: string
}

const articleList = reactive<ArticleItem[]>([
  {
    id: 1,
    tag: '01. 爆款逻辑',
    title: '如何让AI写出"人味十足"的笔记',
    route: '/pages/article/detail?id=1'
  },
  {
    id: 2,
    tag: '02. 避坑指南',
    title: '县城商家起号最易犯的3个错误',
    route: '/pages/article/detail?id=2'
  }
])

const emit = defineEmits<{
  articleClick: [article: ArticleItem]
  viewAll: []
}>()

const handleArticleClick = (article: ArticleItem) => {
  emit('articleClick', article)
  if (article.route) {
    uni.navigateTo({ url: article.route })
  }
}

const handleViewAll = () => {
  emit('viewAll')
  uni.navigateTo({ url: '/pages/article/list' })
}
</script>

<style scoped lang="scss">
@import '@/styles/_variables.scss';

.article-list {
  margin-bottom: $spacing-md;
  padding: 0 $spacing-md;

  .article-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 24rpx;

    .header-left {
      .section-title {
        font-size: $font-size-sm;
        font-weight: 700;
        color: $text-main;
      }
    }

    .header-right {
      .view-all-text {
        font-size: 24rpx;
        color: $text-second;
      }
    }
  }

  .article-scroll {
    white-space: nowrap;
    width: 100%;

    .article-container {
      display: inline-flex;
      gap: 24rpx;
      padding-bottom: 8rpx;
      padding-left: 0;
    }

    .article-card {
      flex-shrink: 0;
      width: 400rpx;
      padding: 32rpx;
      border-radius: $radius-lg;
      display: flex;
      flex-direction: column;
      justify-content: space-between;
      min-height: 200rpx;
      box-sizing: border-box;

      &.card-orange {
        background: $brand-orange;

        .article-tag {
          font-size: 20rpx;
          color: rgba(255, 255, 255, 0.9);
          margin-bottom: 16rpx;
        }

        .article-title {
          font-size: 36rpx;
          font-weight: 700;
          color: $white;
          line-height: 1.5;
          margin-bottom: 24rpx;
          flex: 1;
          overflow: hidden;
          text-overflow: ellipsis;
          display: -webkit-box;
          -webkit-line-clamp: 2;
          -webkit-box-orient: vertical;
        }

        .article-action {
          display: flex;
          align-items: center;
          gap: 8rpx;

          .action-text {
            font-size: 24rpx;
            color: $white;
          }

          .action-arrow {
            font-size: 28rpx;
            color: $white;
          }
        }
      }

      &.card-white {
        background: $white;
        border: 1rpx solid $border-color;

        .article-tag {
          font-size: 20rpx;
          color: $text-second;
          margin-bottom: 16rpx;
        }

        .article-title {
          font-size: 36rpx;
          font-weight: 700;
          color: $text-main;
          line-height: 1.5;
          margin-bottom: 24rpx;
          flex: 1;
          overflow: hidden;
          text-overflow: ellipsis;
          display: -webkit-box;
          -webkit-line-clamp: 2;
          -webkit-box-orient: vertical;
        }

        .article-action {
          display: flex;
          align-items: center;
          gap: 8rpx;

          .action-text {
            font-size: 24rpx;
            color: $brand-orange;
          }

          .action-arrow {
            font-size: 28rpx;
            color: $brand-orange;
          }
        }
      }
    }
  }
}
</style>
