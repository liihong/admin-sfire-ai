<template>
  <view class="drawer-overlay" v-if="visible" @tap="handleClose">
    <view class="drawer-content" @tap.stop>
      <view class="drawer-handle" v-if="showHandle"></view>
      
      <view class="drawer-header" v-if="title || $slots.header">
        <slot name="header">
          <text class="drawer-title">{{ title }}</text>
        </slot>
        <view class="drawer-close" @tap="handleClose" v-if="showClose">
          <text class="close-icon">×</text>
        </view>
      </view>
      
      <scroll-view class="drawer-body" scroll-y>
        <slot></slot>
      </scroll-view>
      
      <view class="drawer-footer" v-if="$slots.footer">
        <slot name="footer"></slot>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
interface Props {
  visible: boolean
  title?: string
  showClose?: boolean
  showHandle?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  visible: false,
  title: '',
  showClose: true,
  showHandle: true
})

const emit = defineEmits<{
  'update:visible': [value: boolean]
  close: []
}>()

function handleClose() {
  emit('update:visible', false)
  emit('close')
}
</script>

<style lang="scss" scoped>
@import '@/styles/_variables.scss';
@import '@/styles/_mixins.scss';
@import '@/styles/_animations.scss';

// 抽屉样式（从 _components.scss 复制，因为 scoped 无法使用全局类）
.drawer-overlay {
  @include fixed-fullscreen;
  background: rgba(0, 0, 0, 0.4);
  backdrop-filter: blur(4px);
  z-index: $z-index-modal-backdrop;
  animation: fadeIn $transition-base ease;
}

.drawer-content {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  max-height: 85vh;
  background: $white;
  border-radius: $radius-xl $radius-xl 0 0;
  display: flex;
  flex-direction: column;
  animation: slideUp $transition-slow ease;
  
  .drawer-handle {
    width: 80rpx;
    height: 8rpx;
    background: #e0e0e0;
    border-radius: 4rpx;
    margin: 20rpx auto;
  }
  
  .drawer-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: $spacing-sm $spacing-lg $spacing-md;
    border-bottom: 1rpx solid $border-color;
    
    .drawer-title {
      font-size: $font-size-lg;
      font-weight: 600;
      color: $text-main;
    }
    
    .drawer-close {
      width: 56rpx;
      height: 56rpx;
      background: $bg-light;
      border-radius: $radius-circle;
      @include flex-center;
      
      .close-icon {
        font-size: 40rpx;
        color: $text-second;
        line-height: 1;
      }
    }
  }
  
  .drawer-body {
    flex: 1;
    overflow-y: auto;
    padding: $spacing-md $spacing-lg;
  }
  
  .drawer-footer {
    padding: $spacing-md $spacing-lg;
    padding-bottom: calc(#{$spacing-md} + env(safe-area-inset-bottom));
    border-top: 1rpx solid $border-color;
  }
}
</style>
