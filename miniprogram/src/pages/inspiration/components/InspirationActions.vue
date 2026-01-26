<template>
  <view class="actions-wrapper">
    <!-- 主操作按钮 -->
    <view class="main-actions">
      <view class="action-btn generate-btn" @tap="handleGenerate">
        <u-icon name="edit-pen" color="#FFFFFF" size="18"></u-icon>
        <text class="action-text">生成文案</text>
      </view>
      <view class="action-btn chat-btn" @tap="handleChat">
        <u-icon name="chat" color="#86909C" size="18"></u-icon>
        <text class="action-text">AI对话</text>
      </view>
    </view>
    
    <!-- 更多操作菜单 -->
    <view class="more-menu" @tap="showMoreMenu = !showMoreMenu">
      <u-icon name="more-dot-fill" color="#86909C" size="20"></u-icon>
    </view>
    
    <!-- 更多操作弹窗 -->
    <view v-if="showMoreMenu" class="more-menu-popup" @tap.stop>
      <view class="menu-item" @tap="handlePin">
        <u-icon :name="inspiration.is_pinned ? 'pushpin-fill' : 'pushpin'" color="#86909C" size="16"></u-icon>
        <text class="menu-text">{{ inspiration.is_pinned ? '取消置顶' : '置顶' }}</text>
      </view>
      <view class="menu-item" @tap="handleArchive">
        <u-icon name="attach" color="#86909C" size="16"></u-icon>
        <text class="menu-text">{{ inspiration.status === 'archived' ? '取消归档' : '归档' }}</text>
      </view>
      <view class="menu-item" @tap="handleEdit">
        <u-icon name="edit-pen" color="#86909C" size="16"></u-icon>
        <text class="menu-text">编辑</text>
      </view>
      <view class="menu-item danger" @tap="handleDelete">
        <u-icon name="trash" color="#EF4444" size="16"></u-icon>
        <text class="menu-text">删除</text>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import type { Inspiration } from '@/api/inspiration'

interface Props {
  inspiration: Inspiration
}

const props = defineProps<Props>()

const emit = defineEmits<{
  generate: []
  chat: []
  edit: []
  delete: []
  pin: []
  archive: []
}>()

const showMoreMenu = ref(false)

function handleGenerate() {
  showMoreMenu.value = false
  emit('generate')
}

function handleChat() {
  showMoreMenu.value = false
  emit('chat')
}

function handleEdit() {
  showMoreMenu.value = false
  emit('edit')
}

function handleDelete() {
  showMoreMenu.value = false
  emit('delete')
}

function handlePin() {
  showMoreMenu.value = false
  emit('pin')
}

function handleArchive() {
  showMoreMenu.value = false
  emit('archive')
}
</script>

<style lang="scss" scoped>
@import '@/styles/_variables.scss';

.actions-wrapper {
  position: absolute;
  bottom: $spacing-md;
  right: $spacing-md;
  display: flex;
  align-items: center;
  gap: $spacing-sm;
  
  .main-actions {
    display: flex;
    gap: $spacing-sm;
    
    .action-btn {
      display: flex;
      align-items: center;
      gap: 4rpx;
      padding: 8rpx 16rpx;
      border-radius: $radius-md;
      transition: all $transition-base;
      
      &.generate-btn {
        background: linear-gradient(135deg, $primary-orange 0%, $primary-orange-alt 100%);
        box-shadow: 0 4rpx 12rpx rgba($primary-orange, 0.3);
        
        .action-text {
          color: $white;
          font-size: $font-size-sm;
        }
        
        &:active {
          transform: scale(0.95);
        }
      }
      
      &.chat-btn {
        background: $bg-light;
        
        .action-text {
          color: $text-second;
          font-size: $font-size-sm;
        }
        
        &:active {
          background: rgba(0, 0, 0, 0.05);
        }
      }
    }
  }
  
  .more-menu {
    width: 56rpx;
    height: 56rpx;
    display: flex;
    align-items: center;
    justify-content: center;
    background: $bg-light;
    border-radius: $radius-circle;
    
    &:active {
      background: rgba(0, 0, 0, 0.05);
    }
  }
  
  .more-menu-popup {
    position: absolute;
    bottom: 70rpx;
    right: 0;
    background: $white;
    border-radius: $radius-md;
    box-shadow: 0 8rpx 24rpx rgba(0, 0, 0, 0.1);
    padding: $spacing-xs 0;
    min-width: 200rpx;
    z-index: 100;
    
    .menu-item {
      display: flex;
      align-items: center;
      gap: $spacing-sm;
      padding: $spacing-sm $spacing-md;
      transition: all $transition-base;
      
      .menu-text {
        font-size: $font-size-sm;
        color: $text-main;
      }
      
      &:active {
        background: $bg-light;
      }
      
      &.danger {
        .menu-text {
          color: $color-error;
        }
      }
    }
  }
}
</style>

