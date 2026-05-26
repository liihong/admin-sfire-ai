<template>
  <view
    class="inspiration-card-premium"
    :class="{ 'inspiration-card-premium--pinned': inspiration.is_pinned }"
    @longpress="handleLongPress"
  >
    <!-- 首行：标题 + 去AI沟通（对齐参考稿 inspiration-card-premium） -->
    <view class="premium-head">
      <view class="premium-title-wrap">
        <text v-if="inspiration.is_pinned" class="premium-pin">置顶</text>
        <text class="premium-title">{{ displayTitle }}</text>
      </view>
      <text class="premium-cta" @tap.stop="handleChat">去AI沟通 ›</text>
    </view>

    <!-- 正文：多行、温润行距 -->
    <text v-if="bodyText" class="premium-body">{{ bodyText }}</text>

    <!-- 底栏：标签胶囊 + 删除 -->
    <view class="premium-foot">
      <view class="premium-foot-left">
        <text class="premium-tag">{{ displayTag }}</text>
        <text v-if="inspiration.generated_content" class="premium-generated">已生成</text>
      </view>
      <view class="premium-del" @tap.stop="handleDelete">
        <u-icon name="trash" color="#8A7E78" size="14"></u-icon>
        <text class="premium-del-txt">删除</text>
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

/** 卡片正文：完整展示解析后的说明（与参考稿一致，支持多段） */
const bodyText = computed(() => {
  const desc = parsedContent.value.description?.trim()
  if (desc) return desc
  const raw = props.inspiration.content?.trim() || ''
  if (!raw) return ''
  if (raw === displayTitle.value) return ''
  return raw
})

/** 底栏标签：优先接口 tags，否则默认「故事碎片」 */
const displayTag = computed(() => {
  const t = props.inspiration.tags?.find((x) => x?.trim())
  if (!t) return '故事碎片'
  return t.replace(/^#+/, '').trim() || '故事碎片'
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

/**
 * 灵感备忘卡：对齐设计稿 .inspiration-card-premium
 * 白卡 + 微米边框 + 左侧朱红粗条 + 空气感阴影
 */
.inspiration-card-premium {
  width: 100%;
  box-sizing: border-box;
  background: $white;
  border: 1rpx solid rgba(44, 30, 26, 0.04);
  border-left: 10rpx solid $accent-gold;
  border-radius: 32rpx;
  padding: 32rpx;
  box-shadow: $shadow-premium;
  transition:
    opacity 0.2s ease,
    transform 0.22s cubic-bezier(0.33, 0.86, 0.42, 1),
    box-shadow 0.22s cubic-bezier(0.33, 0.86, 0.42, 1);

  &--pinned {
    border-color: rgba(217, 75, 54, 0.12);
    border-left-color: $accent-gold;
  }

  &:active {
    opacity: 0.98;
    transform: translateY(2rpx) scale(0.992);
    box-shadow: $shadow-active;
  }
}

.premium-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 24rpx;
  width: 100%;
  margin-bottom: 20rpx;
}

.premium-title-wrap {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: row;
  align-items: flex-start;
  gap: 12rpx;
}

.premium-pin {
  flex-shrink: 0;
  margin-top: 4rpx;
  padding: 2rpx 12rpx;
  font-size: 20rpx;
  font-weight: 800;
  color: $accent-gold;
  background: $accent-gold-light;
  border-radius: 999rpx;
}

.premium-title {
  flex: 1;
  min-width: 0;
  font-size: 28rpx;
  font-weight: 900;
  color: $text-main;
  line-height: 1.42;
  word-break: break-all;
}

.premium-cta {
  flex-shrink: 0;
  font-size: 22rpx;
  font-weight: 800;
  color: $accent-gold;
  white-space: nowrap;
  padding-top: 4rpx;

  &:active {
    opacity: 0.72;
  }
}

.premium-body {
  display: block;
  width: 100%;
  font-size: 24rpx;
  font-weight: 500;
  color: $text-muted-warm;
  line-height: 1.65;
  white-space: pre-wrap;
  word-break: break-all;
  text-align: justify;
  margin-bottom: 24rpx;
}

.premium-foot {
  display: flex;
  flex-direction: row;
  align-items: center;
  justify-content: space-between;
  width: 100%;
  padding-top: 20rpx;
  border-top: 1rpx dashed rgba(44, 30, 26, 0.08);
}

.premium-foot-left {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: row;
  align-items: center;
  flex-wrap: wrap;
  gap: 12rpx;
}

.premium-tag {
  font-size: 20rpx;
  font-weight: 800;
  color: $accent-gold;
  background: #fff5f2;
  padding: 8rpx 20rpx;
  border-radius: 999rpx;
  border: 1rpx solid rgba(217, 75, 54, 0.08);
}

.premium-generated {
  font-size: 20rpx;
  font-weight: 700;
  color: rgba(44, 30, 26, 0.45);
}

.premium-del {
  flex-shrink: 0;
  display: flex;
  flex-direction: row;
  align-items: center;
  gap: 8rpx;
  padding: 8rpx 12rpx;
  margin-left: 12rpx;

  &:active {
    opacity: 0.65;
  }
}

.premium-del-txt {
  font-size: 22rpx;
  font-weight: 800;
  color: $text-muted-warm;
}
</style>
