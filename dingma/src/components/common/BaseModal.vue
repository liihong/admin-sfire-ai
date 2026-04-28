<template>
  <view class="modal-overlay" v-if="visible" @tap="handleClose">
    <view class="modal-content" :class="customClass" @tap.stop>
      <view class="modal-header" v-if="title || $slots.header">
        <slot name="header">
          <text class="modal-title">{{ title }}</text>
        </slot>
        <view class="modal-close" @tap="handleClose" v-if="showClose">
          <text class="close-icon">×</text>
        </view>
      </view>
      
      <view class="modal-body">
        <slot></slot>
      </view>
      
      <view class="modal-footer" v-if="$slots.footer">
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
  customClass?: string
}

const props = withDefaults(defineProps<Props>(), {
  visible: false,
  title: '',
  showClose: true,
  customClass: ''
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

// 弹窗样式（从 _components.scss 复制，因为 scoped 无法使用全局类）
.modal-overlay {
  @include fixed-fullscreen;
  background: rgba(0, 0, 0, 0.5);
  backdrop-filter: blur(4px);
  z-index: $z-index-modal-backdrop;
  @include flex-center;
  padding: $spacing-lg;
  animation: fadeIn $transition-base ease;
}

.modal-content {
  width: 100%;
  max-width: 640rpx;
  background: $white;
  border-radius: $radius-xl;
  overflow: hidden;
  animation: slideUp $transition-slow ease;
  
  .modal-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: $spacing-lg;
    border-bottom: 1rpx solid $border-color;
    
    .modal-title {
      font-size: $font-size-lg;
      font-weight: 600;
      color: $text-main;
    }
    
    .modal-close {
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
  
  .modal-body {
    padding: $spacing-lg;
  }
  
  .modal-footer {
    display: flex;
    gap: $spacing-md;
    padding: $spacing-md $spacing-lg $spacing-lg;
  }
}
</style>
