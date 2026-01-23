<template>
  <view class="category-grid">
    <view
      v-for="item in categories"
      :key="item.key"
      class="category-item"
      @tap="handleClick(item.key)"
    >
      <view class="category-icon-wrapper">
        <AgentIcon :iconName="item.icon" :size="64" />
      </view>
      <text class="category-label">{{ item.label }}</text>
    </view>
  </view>
</template>

<script setup lang="ts">
import { AgentIcon } from '@/components/base'

interface CategoryItem {
  key: string
  label: string
  icon: string
}

interface Props {
  categories?: CategoryItem[]
}

// 在 withDefaults 中直接使用内联数组，避免引用局部变量
const props = withDefaults(defineProps<Props>(), {
  categories: () => [
    { key: 'story', label: '讲故事', icon: 'Reading' },
    { key: 'opinion', label: '聊观点', icon: 'ChatDotRound' },
    { key: 'process', label: '晒过程', icon: 'Film' },
    { key: 'knowledge', label: '教知识', icon: 'Document' },
    { key: 'hotspot', label: '蹭热点', icon: 'TrendCharts' }
  ]
})

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
    padding: 8rpx 0;
    transition: transform $transition-base;
    
    &:active {
      transform: scale(0.92);
    }
    
    .category-icon-wrapper {
      :deep(.agent-icon) {
        box-shadow: 0 4rpx 12rpx rgba(0, 0, 0, 0.1);
      }
    }
    
    .category-label {
      font-size: $font-size-sm;
      font-weight: 500;
      color: $text-main;
      text-align: center;
    }
  }
}
</style>
