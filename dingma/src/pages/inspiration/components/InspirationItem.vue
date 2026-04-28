<template>
  <view class="inspiration-item" :class="{ pinned: inspiration.is_pinned }">
    <!-- 置顶标识 -->
    <view v-if="inspiration.is_pinned" class="pinned-badge">
      <u-icon name="pin" color="#FF8800" size="16"></u-icon>
      <text class="pinned-text">置顶</text>
    </view>
    
    <!-- 内容区域 -->
    <view class="item-content" @tap="handleItemClick">
      <view class="content-text">{{ displayContent }}</view>
      
      <!-- 标签区域 -->
      <view v-if="inspiration.tags && inspiration.tags.length > 0" class="tags-wrapper">
        <view
          v-for="tag in inspiration.tags"
          :key="tag"
          class="tag-item"
        >
          <text class="tag-text">{{ tag }}</text>
        </view>
      </view>
      
      <!-- 项目关联 -->
      <view v-if="inspiration.project_name" class="project-info">
        <u-icon name="folder" color="#86909C" size="14"></u-icon>
        <text class="project-name">{{ inspiration.project_name }}</text>
      </view>
      
      <!-- 底部信息 -->
      <view class="item-footer">
        <text class="time-text">{{ formatTime(inspiration.created_at) }}</text>
        <view v-if="inspiration.generated_content" class="generated-badge">
          <u-icon name="checkmark-circle" color="#10B981" size="14"></u-icon>
          <text class="generated-text">已生成</text>
        </view>
      </view>
    </view>
    
    <!-- 操作按钮 -->
    <InspirationActions
      :inspiration="inspiration"
      @generate="handleGenerate"
      @chat="handleChat"
      @edit="handleEdit"
      @delete="handleDelete"
      @pin="handlePin"
      @archive="handleArchive"
    />
  </view>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { Inspiration } from '@/api/inspiration'
import InspirationActions from './InspirationActions.vue'

interface Props {
  inspiration: Inspiration
}

const props = defineProps<Props>()

const emit = defineEmits<{
  generate: [inspiration: Inspiration]
  chat: [inspiration: Inspiration]
  edit: [inspiration: Inspiration]
  delete: [inspiration: Inspiration]
  pin: [inspiration: Inspiration]
  archive: [inspiration: Inspiration]
  click: [inspiration: Inspiration]
}>()

// 内容预览（前100字符）
const displayContent = computed(() => {
  const content = props.inspiration.content
  if (content.length <= 100) {
    return content
  }
  return content.substring(0, 100) + '...'
})

// 格式化时间
function formatTime(timeStr: string): string {
  const date = new Date(timeStr)
  const now = new Date()
  const diff = now.getTime() - date.getTime()
  const minutes = Math.floor(diff / 60000)
  const hours = Math.floor(diff / 3600000)
  const days = Math.floor(diff / 86400000)
  
  if (minutes < 1) {
    return '刚刚'
  } else if (minutes < 60) {
    return `${minutes}分钟前`
  } else if (hours < 24) {
    return `${hours}小时前`
  } else if (days < 7) {
    return `${days}天前`
  } else {
    return date.toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' })
  }
}

function handleItemClick() {
  emit('click', props.inspiration)
}

function handleGenerate() {
  emit('generate', props.inspiration)
}

function handleChat() {
  emit('chat', props.inspiration)
}

function handleEdit() {
  emit('edit', props.inspiration)
}

function handleDelete() {
  emit('delete', props.inspiration)
}

function handlePin() {
  emit('pin', props.inspiration)
}

function handleArchive() {
  emit('archive', props.inspiration)
}
</script>

<style lang="scss" scoped>
@import '@/styles/_variables.scss';

.inspiration-item {
  background: $white;
  border-radius: $radius-lg;
  padding: $spacing-md;
  margin-bottom: $spacing-md;
  box-shadow: $card-shadow;
  position: relative;
  transition: all $transition-base;
  
  &.pinned {
    border-left: 4rpx solid $primary-orange;
  }
  
  .pinned-badge {
    position: absolute;
    top: $spacing-sm;
    right: $spacing-sm;
    display: flex;
    align-items: center;
    gap: 4rpx;
    padding: 4rpx 8rpx;
    background: rgba($primary-orange, 0.1);
    border-radius: $radius-sm;
    
    .pinned-text {
      font-size: $font-size-xs;
      color: $primary-orange;
    }
  }
  
  .item-content {
    padding-right: 80rpx;
    
    .content-text {
      font-size: $font-size-md;
      color: $text-main;
      line-height: 1.6;
      margin-bottom: $spacing-sm;
    }
    
    .tags-wrapper {
      display: flex;
      flex-wrap: wrap;
      gap: $spacing-xs;
      margin-bottom: $spacing-sm;
      
      .tag-item {
        padding: 4rpx 12rpx;
        background: rgba($primary-orange, 0.1);
        border-radius: $radius-sm;
        
        .tag-text {
          font-size: $font-size-xs;
          color: $primary-orange;
        }
      }
    }
    
    .project-info {
      display: flex;
      align-items: center;
      gap: 4rpx;
      margin-bottom: $spacing-sm;
      
      .project-name {
        font-size: $font-size-xs;
        color: $text-second;
      }
    }
    
    .item-footer {
      display: flex;
      align-items: center;
      justify-content: space-between;
      
      .time-text {
        font-size: $font-size-xs;
        color: $text-placeholder;
      }
      
      .generated-badge {
        display: flex;
        align-items: center;
        gap: 4rpx;
        
        .generated-text {
          font-size: $font-size-xs;
          color: $color-success;
        }
      }
    }
  }
}
</style>

