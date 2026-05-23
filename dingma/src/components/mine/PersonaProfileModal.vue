<template>
  <view v-if="visible" class="persona-modal">
    <view class="persona-modal__mask" @tap="close" />
    <view class="persona-modal__card" @tap.stop>
      <view class="persona-modal__head">
        <view class="persona-modal__title-row">
          <text class="persona-modal__gear">⚙</text>
          <text class="persona-modal__title">常驻 IP 信息</text>
        </view>
        <view class="persona-modal__close" @tap="close">
          <text class="persona-modal__close-icon">×</text>
        </view>
      </view>

      <PersonaProfileEditor class="persona-modal__editor" :default-name="defaultName" @saved="onEditorSaved" />
    </view>
  </view>
</template>

<script setup lang="ts">
import PersonaProfileEditor from '@/components/mine/PersonaProfileEditor.vue'

defineProps<{
  visible: boolean
  defaultName?: string
}>()

const emit = defineEmits<{
  'update:visible': [value: boolean]
  saved: []
}>()

function close() {
  emit('update:visible', false)
}

function onEditorSaved() {
  emit('saved')
  close()
}
</script>

<style lang="scss" scoped>
@import '@/styles/_variables.scss';

.persona-modal {
  position: fixed;
  inset: 0;
  z-index: $z-index-modal-backdrop;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 40rpx 32rpx;

  &__mask {
    position: absolute;
    inset: 0;
    background: rgba(0, 0, 0, 0.45);
    backdrop-filter: blur(6px);
  }

  &__card {
    position: relative;
    z-index: 1;
    width: 100%;
    max-width: 660rpx;
    max-height: 86vh;
    display: flex;
    flex-direction: column;
    background: $white;
    border-radius: 32rpx;
    padding: 32rpx 28rpx 28rpx;
    box-shadow: 0 24rpx 64rpx rgba(0, 0, 0, 0.12);
  }

  &__head {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    margin-bottom: 24rpx;
    flex-shrink: 0;
  }

  &__title-row {
    display: flex;
    align-items: center;
    gap: 10rpx;
    flex: 1;
    padding-right: 12rpx;
  }

  &__gear {
    font-size: 30rpx;
    color: #9ca3af;
    flex-shrink: 0;
    line-height: 1;
  }

  &__title {
    font-size: 28rpx;
    font-weight: 600;
    color: #9a6b3f;
    line-height: 1.45;
  }

  &__close {
    width: 52rpx;
    height: 52rpx;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
  }

  &__close-icon {
    font-size: 44rpx;
    color: #9ca3af;
    line-height: 1;
  }

  /** 编辑器在弹窗内：内部滚动区限定高度（与旧版 modal body 一致） */
  &__editor {
    flex: 1;
    min-height: 0;
    max-height: calc(86vh - 200rpx);
    display: flex;
    flex-direction: column;

    :deep(.persona-editor__body) {
      max-height: 58vh;
    }
  }
}
</style>

