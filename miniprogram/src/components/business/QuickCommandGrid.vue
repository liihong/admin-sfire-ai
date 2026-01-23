<template>
  <view class="quick-command-grid">
    <view
      v-for="item in commands"
      :key="item.key"
      class="command-card"
      @tap="handleClick(item.route)"
    >
      <view class="command-icon-wrapper">
        <AgentIcon :iconName="item.icon" :size="48" />
      </view>
      <view class="command-content">
        <text class="command-title">{{ item.title }}</text>
        <text class="command-desc">{{ item.desc }}</text>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { AgentIcon } from '@/components/base'

interface CommandItem {
  key: string
  title: string
  desc: string
  icon: string
  route: string
}

interface Props {
  commands?: CommandItem[]
}

// 在 withDefaults 中直接使用内联数组，避免引用局部变量
const props = withDefaults(defineProps<Props>(), {
  commands: () => [
    { key: 'persona', title: '我在起号', desc: '需要人设故事', icon: 'User', route: '/pages/copywriting/index' },
    { key: 'topic', title: '我在同城', desc: '需要泛流话题', icon: 'Platform', route: '' },
    { key: 'rewrite', title: '我有文案', desc: '需要深度改写', icon: 'Edit', route: '' },
    { key: 'script', title: '我有选题', desc: '需要口播文案', icon: 'ChatSquare', route: '' }
  ]
})

const emit = defineEmits<{
  click: [route: string]
}>()

function handleClick(route: string) {
  emit('click', route)
}
</script>

<style lang="scss" scoped>
@import '@/styles/_variables.scss';
@import '@/styles/_mixins.scss';

.quick-command-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: $spacing-md;
  margin-bottom: $spacing-lg;
  
  .command-card {
    @include card-style;
    padding: $spacing-md;
    display: flex;
    align-items: center;
    gap: 20rpx;
    transition: all $transition-base;
    
    &:active {
      transform: scale(0.98);
      background: $bg-light;
    }
    
    .command-icon-wrapper {
      :deep(.agent-icon) {
        box-shadow: 0 2rpx 8rpx rgba(0, 0, 0, 0.15);
      }
    }
    
    .command-content {
      display: flex;
      flex-direction: column;
      gap: 6rpx;
      flex: 1;
      min-width: 0;
      
      .command-title {
        font-size: $font-size-md;
        font-weight: 600;
        color: $text-main;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
      }
      
      .command-desc {
        font-size: $font-size-xs;
        color: $text-second;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
      }
    }
  }
}
</style>
