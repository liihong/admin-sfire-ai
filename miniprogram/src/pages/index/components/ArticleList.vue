<template>
  <view class="article-list">
   <BaseSection>
      运营干货
      <template #right>
        <view @tap="handleViewAll">
          <text class="view-all-text">全部</text>
        </view>
     </template>
    </BaseSection>
    <scroll-view class="article-scroll" scroll-x>
      <view class="article-container">
        <navigator
          v-for="(article, index) in articleList"
          :key="article.id"
          class="article-card"
          :class="{ 'card-orange': index === 0, 'card-white': index === 1 }"
          :url="`/pages/article/detail?id=${article.id}`"
          open-type="navigate"
          hover-class="article-card--hover"
          hover-stay-time="70"
          @tap="onCardTap(article)"
        >
          <view class="article-tag">{{ article.tags && article.tags.length > 0 ? article.tags[0] : '' }}</view>
          <view class="article-title">{{ article.title }}</view>
          <view class="article-action">
            <text class="action-text">{{ index === 0 ? '立即研读' : '去看看' }}</text>
            <text class="action-arrow"> ›</text>
          </view>
        </navigator>
      </view>
    </scroll-view>
  </view>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import BaseSection from '@/components/base/BaseSection.vue'
import type { ArticleItem } from '@/api/home'

// 接收父组件传递的运营干货数据
const props = defineProps<{
  operationArticles?: ArticleItem[]
}>()

const emit = defineEmits<{
  articleClick: [article: ArticleItem]
  viewAll: []
}>()

// 只显示前2条
const articleList = computed(() => {
  if (props.operationArticles && props.operationArticles.length > 0) {
    return props.operationArticles.slice(0, 2)
  }
  return []
})

/** 跳转由 navigator 完成；此处仅向父组件透传（如统计） */
const onCardTap = (article: ArticleItem) => {
  emit('articleClick', article)
}

const handleViewAll = () => {
  emit('viewAll')
  uni.navigateTo({ url: '/pages/article/list?category=02' })
}
</script>

<style scoped lang="scss">
@import '@/styles/_variables.scss';

.article-list {
  margin-bottom: $spacing-md;
  padding: 0 $spacing-md;

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
      overflow: hidden;

      &--hover {
        opacity: 0.92;
      }

      &.card-orange {
        background: $brand-orange;

        .article-tag {
          font-size: 20rpx;
          color: rgba(255, 255, 255, 0.9);
          margin-bottom: 16rpx;
        }

        .article-title {
          font-size: 32rpx;
          font-weight: 700;
          color: $white;
          line-height: 1.5;
          margin-bottom: 24rpx;
          flex: 1;
          word-wrap: break-word;
            word-break: break-all;
            white-space: normal;
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
          word-wrap: break-word;
            word-break: break-all;
            white-space: normal;
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
.view-all-text {
  font-size: 20rpx;
  font-size: 20rpx;
  color: $text-second;
}
</style>
