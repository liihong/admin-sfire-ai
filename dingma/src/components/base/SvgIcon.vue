<template>
  <!-- 微信小程序里 text + iconfont 的 ::before 易被裁切不全，统一用 view 承载字形 -->
  <view
    class="svg-icon iconfont"
    :class="name ? `icon-${name}` : ''"
    :style="{ color: iconColor, fontSize: iconSize }"
  />
</template>

<script setup lang="ts">
import { computed } from 'vue'

/** 微信小程序等环境下 inherit 常为灰/不可见：统一默认印章红，重要处请显式传 color（如白色按钮内） */
const DEFAULT_ICON_BRAND_HEX = '#D94B36'

const props = defineProps({
  name: String, // 传入 iconfont 名（无前缀）：如 'send'
  size: { type: [Number, String], default: 32 },
  color: { type: String, default: DEFAULT_ICON_BRAND_HEX }
})

const iconSize = computed(() => (typeof props.size === 'number' ? `${props.size}rpx` : props.size))
const iconColor = computed(() => props.color)
</script>

<style scoped>
.svg-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  line-height: 1;
  vertical-align: middle;
}
</style>