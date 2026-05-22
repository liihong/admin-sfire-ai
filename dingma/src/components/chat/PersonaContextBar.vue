<template>
  <view class="persona-bar">
    <view class="persona-bar__info" @tap="onInfoTap">
      <text class="persona-bar__prefix">IP 实时关联：</text>
      <text v-if="label" class="persona-bar__label">{{ label }}</text>
      <text v-else class="persona-bar__empty">暂未绑定人设，点击完善</text>
    </view>
    <view v-if="showNewSession" class="persona-bar__action" @tap.stop="$emit('new-session')">
      <text class="persona-bar__action-icon">↻</text>
      <text class="persona-bar__action-text">新开会话</text>
    </view>
  </view>
</template>

<script setup lang="ts">
defineProps<{
  label: string
  showNewSession?: boolean
}>()

const emit = defineEmits<{
  'new-session': []
  setup: []
}>()

function onInfoTap() {
  emit('setup')
}
</script>

<style lang="scss" scoped>
.persona-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16rpx;
  padding: 12rpx 24rpx 16rpx;
  border-top: 1rpx solid rgba(0, 0, 0, 0.04);

  &__info {
    flex: 1;
    min-width: 0;
    display: flex;
    align-items: center;
    flex-wrap: wrap;
    gap: 4rpx;
  }

  &__prefix {
    font-size: 22rpx;
    color: #9a6b3f;
    flex-shrink: 0;
  }

  &__label {
    font-size: 22rpx;
    color: #8b5a24;
    font-weight: 600;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  &__empty {
    font-size: 22rpx;
    color: #c4a882;
  }

  &__action {
    display: flex;
    align-items: center;
    gap: 6rpx;
    flex-shrink: 0;
    padding: 8rpx 16rpx;
    border-radius: 999rpx;
    background: rgba(154, 107, 63, 0.08);

    &:active {
      opacity: 0.75;
    }
  }

  &__action-icon {
    font-size: 24rpx;
    color: #9a6b3f;
    line-height: 1;
  }

  &__action-text {
    font-size: 22rpx;
    color: #9a6b3f;
    white-space: nowrap;
  }
}
</style>
