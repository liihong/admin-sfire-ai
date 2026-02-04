<template>
  <view class="category-grid">
    <view
      v-for="item in categories"
      :key="item.key"
      class="category-item"
      @tap="handleClick(item.key)"
    >
      <view class="category-icon-wrapper">
        <!-- <u-icon :name="item.icon" :size="34" color="#f69c0e" /> -->
       <SvgIcon :name="item.icon" :size="40" :color="item.color" />
      </view>
      <text class="category-label">{{ item.label }}</text>

    </view>
  </view>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import SvgIcon from '@/components/base/SvgIcon.vue'

interface CategoryItem {
  key: string
  label: string
  icon: string
  color: string
}

interface Props {
  categories?: CategoryItem[]
}

// 默认分类数据数组（用于 defineProps 的默认值）
const DEFAULT_CATEGORIES: CategoryItem[] = [
  { key: 'story', label: '讲故事', icon: 'book', color: '#F69C0E' },
  { key: 'opinion', label: '聊观点', icon: 'point', color: '#397FF6' },
  { key: 'process', label: '晒过程', icon: 'process', color: '#397FF6' },
  { key: 'knowledge', label: '教知识', icon: 'knowledge', color: '#00B781' },
  { key: 'hotspot', label: '蹭热点', icon: 'hotspot', color: '#F53C5E' }
]

// 在 defineProps 中直接内联默认值，避免引用局部变量
const props = withDefaults(defineProps<Props>(), {
  categories: () => [
    { key: 'story', label: '讲故事', icon: 'book', color: '#F69C0E' },
    { key: 'opinion', label: '聊观点', icon: 'point', color: '#397FF6' },
    { key: 'process', label: '晒过程', icon: 'process', color: '#397FF6' },
    { key: 'knowledge', label: '教知识', icon: 'knowledge', color: '#00B781' },
    { key: 'hotspot', label: '蹭热点', icon: 'hotspot', color: '#F53C5E' }
  ] as CategoryItem[]
})

// 使用传入的分类数据，如果没有或为空则使用默认数据
const categories = computed(() => props.categories && props.categories.length > 0 ? props.categories : DEFAULT_CATEGORIES)

const emit = defineEmits<{
  click: [key: string]
}>()

function handleClick(key: string) {
  emit('click', key)
}
</script>

<style lang="scss" scoped>
@import '@/styles/_variables.scss';

.category-grid {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: $spacing-sm;
  margin-bottom: $spacing-lg;

  .category-item {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: $spacing-sm;
    transition: transform $transition-base;

    &:active {
      transform: scale(0.92);
    }

    .category-icon-wrapper {
      border-radius: 20rpx;
      padding: 20rpx 30rpx;
      border: 1rpx solid #e5e7eb;
      box-shadow: 0 2rpx 8rpx rgba(0, 0, 0, 0.1);

      :deep(.agent-icon) {
        box-shadow: 0 4rpx 12rpx rgba(0, 0, 0, 0.1);
      }
    }

    .category-label {
      font-size: $font-size-sm;
      font-weight: 900;
      color: $text-primary;
      text-align: center;
    }
  }
}
</style>
