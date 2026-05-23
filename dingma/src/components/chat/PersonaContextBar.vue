<template>
  <view class="persona-bar">
    <view class="persona-bar__info" @tap="onInfoTap">
      <view class="persona-bar__dot" />
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
@import '@/styles/_variables.scss';

.persona-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16rpx;
  padding: 24rpx 40rpx;
  background: $bg-card;
  border-top: none;
  border-bottom: 1rpx solid rgba(51, 37, 30, 0.02);

  &__info {
    flex: 1;
    min-width: 0;
    display: flex;
    align-items: center;
    flex-wrap: nowrap;
    gap: 8rpx;
  }

  &__dot {
    width: 10rpx;
    height: 10rpx;
    border-radius: 50%;
    background: $accent-gold;
    flex-shrink: 0;
    box-shadow: 0 0 10rpx rgba(217, 75, 54, 0.35);
  }

  &__prefix {
    font-size: 21rpx;
    color: $text-muted;
    flex-shrink: 0;
    white-space: nowrap;
  }

  &__label {
    flex: 1;
    font-size: 21rpx;
    color: $text-main;
    font-weight: 800;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    min-width: 0;
  }

  &__empty {
    flex: 1;
    font-size: 21rpx;
    color: $text-muted;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    min-width: 0;
  }

  &__action {
    display: flex;
    align-items: center;
    gap: 8rpx;
    flex-shrink: 0;
    padding: 0;
    border-radius: 0;
    background: transparent;

    &:active {
      opacity: 0.75;
    }
  }

  &__action-icon {
    font-size: 22rpx;
    color: $accent-gold;
    line-height: 1;
  }

  &__action-text {
    font-size: 21rpx;
    color: $accent-gold;
    font-weight: 700;
    white-space: nowrap;
  }
}
</style>
