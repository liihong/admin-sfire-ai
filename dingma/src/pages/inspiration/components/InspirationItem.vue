<template>
  <view
    class="inspiration-card"
    :class="{ pinned: inspiration.is_pinned }"
    @longpress="handleLongPress"
  >
    <view class="card-accent" />

    <view class="card-body">
      <view class="card-top">
        <view class="card-title-row">
          <text v-if="inspiration.is_pinned" class="pin-tag">置顶</text>
          <text class="card-title">{{ displayTitle }}</text>
        </view>
        <text class="card-action" @tap.stop="handleChat">去AI沟通 ›</text>
      </view>

      <text v-if="displayDescription" class="card-desc">{{ displayDescription }}</text>

      <view class="card-footer">
        <view v-if="inspiration.tags?.length || inspiration.generated_content" class="card-meta">
          <view v-if="inspiration.tags?.length" class="tags-row">
            <text
              v-for="tag in inspiration.tags.slice(0, 3)"
              :key="tag"
              class="tag-chip"
            >{{ tag }}</text>
          </view>
          <text v-if="inspiration.generated_content" class="generated-tag">已生成文案</text>
        </view>

        <view class="delete-btn" @tap.stop="handleDelete">
          <u-icon name="trash" color="#c47a6a" size="16"></u-icon>
          <text class="delete-text">删除</text>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { Inspiration } from '@/api/inspiration'

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

const parsedContent = computed(() => parseContent(props.inspiration.content))

const displayTitle = computed(() => parsedContent.value.title)

const displayDescription = computed(() => {
  const desc = parsedContent.value.description
  if (!desc) return ''
  if (desc.length <= 120) return desc
  return `${desc.slice(0, 120)}...`
})

function parseContent(content: string) {
  const trimmed = content.trim()
  if (!trimmed) {
    return { title: '未命名灵感', description: '' }
  }

  const lines = trimmed.split('\n').map((line) => line.trim()).filter(Boolean)
  if (lines.length >= 2) {
    return {
      title: lines[0],
      description: lines.slice(1).join('\n'),
    }
  }

  const sentenceMatch = trimmed.match(/^(.{2,24}?[，。！？、：:])\s*(.+)$/s)
  if (sentenceMatch?.[2] && sentenceMatch[2].length >= 8) {
    return {
      title: sentenceMatch[1].replace(/[，。！？、：:]$/, ''),
      description: sentenceMatch[2].trim(),
    }
  }

  if (trimmed.length <= 20) {
    return { title: trimmed, description: '' }
  }

  const splitAt = Math.min(16, trimmed.length)
  return {
    title: `${trimmed.slice(0, splitAt)}…`,
    description: trimmed,
  }
}

function handleChat() {
  emit('chat', props.inspiration)
}

function handleDelete() {
  emit('delete', props.inspiration)
}

function handleLongPress() {
  const pinLabel = props.inspiration.is_pinned ? '取消置顶' : '置顶'
  const archiveLabel = props.inspiration.status === 'archived' ? '取消归档' : '归档'

  uni.showActionSheet({
    itemList: [pinLabel, archiveLabel, '编辑'],
    success: (res) => {
      switch (res.tapIndex) {
        case 0:
          emit('pin', props.inspiration)
          break
        case 1:
          emit('archive', props.inspiration)
          break
        case 2:
          emit('edit', props.inspiration)
          break
      }
    },
  })
}
</script>

<style lang="scss" scoped>
@import '@/styles/_variables.scss';

$text-primary: #332d2b;
$text-muted: #998b82;
$accent: #b8864d;

.inspiration-card {
  position: relative;
  display: flex;
  background: $white;
  border: 1rpx solid rgba(44, 30, 26, 0.08);
  border-radius: 36rpx;
  overflow: hidden;
  box-sizing: border-box;
  box-shadow: $shadow-card-elevated-list;
  transition:
    opacity 0.2s ease,
    transform 0.22s cubic-bezier(0.33, 0.86, 0.42, 1),
    box-shadow 0.22s cubic-bezier(0.33, 0.86, 0.42, 1);

  &.pinned {
    border-color: rgba($accent, 0.45);
  }

  &:active {
    opacity: 0.98;
    transform: translateY(2rpx) scale(0.992);
    box-shadow: $shadow-card-elevated-list-active;
  }
}

.card-accent {
  flex-shrink: 0;
  width: 10rpx;
  margin: 24rpx 0 24rpx 0;
  background: linear-gradient(180deg, #d4a574 0%, #b8864d 100%);
  border-radius: 0 8rpx 8rpx 0;
}

.card-body {
  flex: 1;
  min-width: 0;
  padding: 28rpx 28rpx 28rpx 20rpx;
}

.card-top {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 20rpx;
  margin-bottom: 12rpx;
}

.card-title-row {
  flex: 1;
  min-width: 0;
  display: flex;
  align-items: center;
  gap: 10rpx;
}

.pin-tag {
  flex-shrink: 0;
  padding: 2rpx 10rpx;
  font-size: 20rpx;
  color: $accent;
  background: rgba($accent, 0.12);
  border-radius: 999rpx;
}

.card-title {
  flex: 1;
  min-width: 0;
  font-size: 30rpx;
  font-weight: 700;
  color: $text-primary;
  line-height: 1.4;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.card-action {
  flex-shrink: 0;
  padding-top: 4rpx;
  font-size: 24rpx;
  color: $accent;
  white-space: nowrap;

  &:active {
    opacity: 0.7;
  }
}

.card-desc {
  display: block;
  font-size: 26rpx;
  color: $text-muted;
  line-height: 1.65;
  word-break: break-all;
}

.card-meta {
  flex: 1;
  min-width: 0;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16rpx;
}

.card-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16rpx;
  margin-top: 20rpx;
}

.delete-btn {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  gap: 6rpx;
  margin-left: auto;
  padding: 8rpx 12rpx;
  border-radius: 999rpx;

  &:active {
    background: rgba(196, 122, 106, 0.12);
  }
}

.delete-text {
  font-size: 22rpx;
  color: #c47a6a;
}

.tags-row {
  display: flex;
  flex-wrap: wrap;
  gap: 8rpx;
}

.tag-chip {
  padding: 4rpx 12rpx;
  font-size: 20rpx;
  color: $accent;
  background: rgba($accent, 0.1);
  border-radius: 999rpx;
}

.generated-tag {
  flex-shrink: 0;
  font-size: 20rpx;
  color: #7a9b6e;
}
</style>
