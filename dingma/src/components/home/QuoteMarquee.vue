<template>
  <view v-if="displayQuotes.length > 0" class="quote-bar">
    <view class="quote-track" :class="{ 'quote-track--animate': displayQuotes.length > 0 }">
      <text v-for="(q, i) in marqueeItems" :key="'a-' + i" class="quote-text">{{ q }}</text>
      <text v-for="(q, i) in marqueeItems" :key="'b-' + i" class="quote-text">{{ q }}</text>
    </view>
  </view>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const DEFAULT_QUOTES = [
  '完美主义是拖延症的遮羞布，撕掉它，去干！',
  '做生意最怕的不是没客户，而是不敢开口。',
  '顶妈语录：先做起来，再慢慢变好。',
  '灵感不等人，想到就记下来。'
]

const props = defineProps<{
  quotes?: string[]
}>()

const displayQuotes = computed(() => {
  const fromProps = (props.quotes ?? []).map((s) => s.trim()).filter(Boolean)
  return fromProps.length > 0 ? fromProps : DEFAULT_QUOTES
})

const marqueeItems = computed(() =>
  displayQuotes.value.map((q) => {
    if (q.startsWith('顶妈语录')) return q
    if (q.startsWith('顶妈')) return q
    return `顶妈语录：${q}`
  })
)
</script>

<style scoped lang="scss">
@import '@/styles/_variables.scss';

.quote-bar {
  margin: 20rpx 28rpx 0;
  padding: 18rpx 0;
  background: #fff0f0;
  border-radius: 12rpx;
  overflow: hidden;
}

.quote-track {
  display: flex;
  flex-wrap: nowrap;
  white-space: nowrap;
  width: max-content;

  &--animate {
    animation: quote-scroll 28s linear infinite;
  }
}

.quote-text {
  flex-shrink: 0;
  padding: 0 48rpx;
  font-size: 26rpx;
  color: #e53935;
  line-height: 1.4;
}

@keyframes quote-scroll {
  0% {
    transform: translateX(0);
  }
  100% {
    transform: translateX(-50%);
  }
}
</style>
