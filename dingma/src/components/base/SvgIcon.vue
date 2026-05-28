<template>
  <!-- Lucide 矢量：data URI + image，支持微信小程序动态着色 -->
  <image
    v-if="lucideSrc"
    class="svg-icon svg-icon--lucide"
    :src="lucideSrc"
    :style="lucideStyle"
    mode="aspectFit"
  />
  <!-- 回退：iconfont 单色字形 -->
  <view
    v-else
    class="svg-icon iconfont"
    :class="name ? `icon-${name}` : ''"
    :style="{ color: iconColor, fontSize: iconSize }"
  />
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { buildLucideDataUri } from '@/utils/lucideIconPaths'

/** 微信小程序等环境下 inherit 常为灰/不可见：统一默认印章红，重要处请显式传 color（如白色按钮内） */
const DEFAULT_ICON_BRAND_HEX = '#D94B36'

const props = defineProps({
  name: String, // Lucide 键或 iconfont 名（无前缀）：如 'sparkles' / 'send'
  size: { type: [Number, String], default: 32 },
  color: { type: String, default: DEFAULT_ICON_BRAND_HEX }
})

/** 纯数字或数字字符串统一补 rpx，避免小程序 image 无尺寸约束被放大 */
function normalizeIconSize(size: number | string | undefined): string {
  const fallback = '32rpx'
  if (size == null || size === '') return fallback
  if (typeof size === 'number' && Number.isFinite(size)) return `${size}rpx`
  const s = String(size).trim()
  if (/^\d+(\.\d+)?$/.test(s)) return `${s}rpx`
  return s
}

const iconSize = computed(() => normalizeIconSize(props.size))
const iconColor = computed(() => props.color)

const lucideSrc = computed(() => {
  if (!props.name) return null
  return buildLucideDataUri(props.name, props.color || DEFAULT_ICON_BRAND_HEX)
})

const lucideStyle = computed(() => ({
  width: iconSize.value,
  height: iconSize.value
}))
</script>

<style scoped>
.svg-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  line-height: 1;
  vertical-align: middle;
  flex-shrink: 0;
}

.svg-icon--lucide {
  /* image 标签默认 inline，对齐 iconfont 观感 */
  display: block;
}
</style>