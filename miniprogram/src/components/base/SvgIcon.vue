<template>
  <text 
    :class="['iconfont', `icon-${name}`]" 
    :style="{ color: iconColor, fontSize: iconSize }"
  ></text>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps({
  name: String, // 传入 'book'
  size: { type: [Number, String], default: 32 },
  color: { type: String, default: 'inherit' } // 默认继承父级颜色
})

const iconSize = computed(() => typeof props.size === 'number' ? `${props.size}rpx` : props.size)
const iconColor = computed(() => props.color)
</script>

<style>
/* 确保你在全局引入了 iconfont.css */
/* .iconfont { ... } */
</style>