<template>
  <view class="qm" @tap="onTapAdvance">
    <!-- 固定左侧喇叭，不参与滚动 -->
    <view class="qm__speaker" aria-hidden="true">
      <SvgIcon class="qm__speaker-glyph" name="notice" :size="36" color="#D94B36" />
    </view>
    <view class="qm__body">
      <view class="qm__track">
        <!-- 始终以向左无缝跑马灯滚动（双段克隆 + translate -50%） -->
        <view class="qm__scroll qm__scroll--marquee" :style="trackFadeStyle">
          <view class="qm__lane" :key="quoteIndex">
            <view class="qm__dup">
              <text class="qm__txt">{{ displayed }}</text>
              <view class="qm__gap" />
            </view>
            <view class="qm__dup">
              <text class="qm__txt">{{ displayed }}</text>
              <view class="qm__gap" />
            </view>
          </view>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted, onUnmounted, nextTick } from 'vue'
import SvgIcon from '@/components/base/SvgIcon.vue'

const REF_QUOTES = [
  '粗糙的开始就是最好的开始，先去做，做出一坨狗屎也比一直等准备完美强！',
  '哪有什么准备好？赚钱这件事，向来都是先上车，再补票。',
  '如果你觉得痛苦，说明你在成长；如果你觉得舒服，你正在掉队。',
  '别在朋友圈里自我感动，直接去收钱才是正经事。',
  '完美主义是拖延症的遮羞布，撕掉它，去干！',
  '在这个时代，没有行动力的认知，只能让你更焦虑。'
]

const props = defineProps<{
  quotes?: string[]
}>()

const list = computed(() => {
  const from = (props.quotes ?? []).map((s) => s.trim()).filter(Boolean)
  return from.length ? from : REF_QUOTES
})

const quoteIndex = ref(0)
const displayed = computed(() => list.value[quoteIndex.value] ?? '')
/** 0~1，整条文案轨道（含跑马灯）淡入淡出，换句更柔和 */
const opacity = ref(1)

/** 与下方 .qm__scroll 的 transition 时长一致（毫秒）：先淡出到位再换文案 */
const QUOTE_CROSSFADE_MS = 520

const trackFadeStyle = computed(() => ({
  opacity: opacity.value
}))

let rotateTimer: ReturnType<typeof setInterval> | null = null

/** 金句自动轮换间隔（毫秒）：与跑马灯单次循环时长配合观感 */
const QUOTE_ROTATE_MS = 6000

function bumpIndex() {
  if (list.value.length <= 1) return
  opacity.value = 0
  setTimeout(() => {
    quoteIndex.value = (quoteIndex.value + 1) % list.value.length
    nextTick(() => {
      opacity.value = 1
    })
  }, QUOTE_CROSSFADE_MS)
}

function onTapAdvance() {
  bumpIndex()
  uni.showToast({ title: '已切换干劲金句', icon: 'none', duration: 1200 })
}

watch(list, () => {
  quoteIndex.value = 0
})

onMounted(() => {
  /** 金句自动轮换：每 6 秒切换一条 */
  rotateTimer = setInterval(bumpIndex, QUOTE_ROTATE_MS)
})

onUnmounted(() => {
  if (rotateTimer) {
    clearInterval(rotateTimer)
    rotateTimer = null
  }
})
</script>

<style scoped lang="scss">
@import '@/styles/_variables.scss';

.qm {
  position: relative;
  /* 原 64rpx 在窄屏偏小，加高并略增纵向内边距，提升可读性与点击区域 */
  min-height: 88rpx;
  /*
   * 与白底页面区分：暖燕麦底 + 与任务栅格同宽的「横条卡片」视感
   * 左右 margin 与首页 task-grid 的 36rpx 对齐
   */
  margin: 12rpx 36rpx 16rpx;
  padding: 14rpx 28rpx;
  border-radius: 24rpx;
  box-sizing: border-box;
  background-color: $quote-marquee-strip-bg;
  border: 1rpx solid rgba(44, 30, 26, 0.07);
  box-shadow:
    inset 0 2rpx 0 rgba(255, 255, 255, 0.72),
    0 10rpx 28rpx -10rpx rgba(44, 30, 26, 0.1),
    0 4rpx 12rpx -4rpx rgba(44, 30, 26, 0.05);
  overflow: hidden;
  display: flex;
  flex-direction: row;
  align-items: center;
  gap: 10px;
}

.qm__speaker {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0;
  /* 与同条底色一致 */
  background-color: transparent;
  z-index: 3;
}

.qm__speaker-glyph {
  display: inline-flex;
  width: 36rpx;
  height: 36rpx;
  align-items: center;
  justify-content: center;
}

.qm__body {
  position: relative;
  flex: 1;
  min-width: 0;
  align-self: stretch;
  overflow: hidden;
}

.qm__track {
  position: relative;
  z-index: 1;
  height: 100%;
  overflow: hidden;
  display: flex;
  align-items: center;
  padding: 0 12rpx 0 0;
  box-sizing: border-box;
}

.qm__scroll--marquee {
  position: relative;
  z-index: 1;
  justify-content: flex-start;
  width: 100%;
  min-width: 0;
  overflow: hidden;
}

.qm__lane {
  display: flex;
  flex-direction: row;
  align-items: center;
  flex-wrap: nowrap;
  width: max-content;
  will-change: transform;
  animation: qm-marquee-shift 22s linear infinite;
}

.qm__dup {
  display: flex;
  flex-direction: row;
  align-items: center;
  flex-wrap: nowrap;
  flex-shrink: 0;
}

/* 两段文案之间的留白，首尾衔接更舒适 */
.qm__gap {
  width: 100rpx;
  flex-shrink: 0;
  height: 8rpx;
}

.qm__scroll {
  display: flex;
  flex-direction: row;
  align-items: center;
  flex-wrap: nowrap;
  white-space: nowrap;
  width: 100%;
  /* 换句时用柔和淡入淡出（与脚本 QUOTE_CROSSFADE_MS 保持一致） */
  transition: opacity 520ms cubic-bezier(0.33, 0.86, 0.42, 1);
}

/* 向左平移半程（两段完全一致），无缝循环跑马灯 */
@keyframes qm-marquee-shift {
  0% {
    transform: translate3d(0, 0, 0);
  }
  100% {
    transform: translate3d(-50%, 0, 0);
  }
}

.qm__txt {
  white-space: nowrap;
  font-size: 26rpx;
  font-weight: 800;
  color: $text-main;
  letter-spacing: 0.6rpx;
  line-height: 1.45;
}

</style>
