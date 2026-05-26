<template>
  <view class="page-root">
    <scroll-view scroll-y class="page" :show-scrollbar="false">
      <HomeBannerSwiper :banners="homeBanners" />
      <QuoteMarquee :quotes="quoteList" />

      <view class="task-grid">
        <view v-if="loading && tools.length === 0" class="task-empty muted">加载中…</view>
        <view v-else-if="!loading && tools.length === 0" class="task-empty muted">
          暂无智能体，敬请期待
        </view>
        <template v-else>
          <view
            v-if="featuredTool"
            class="task-card task-card--span2"
            @tap="onToolTap(featuredTool.raw)"
          >
            <view
              class="icon-box icon-box--lg"
              :class="{ 'icon-box--dot': featuredTool.hot }"
              :style="{ background: featuredTool.iconWrapBg }"
            >
              <SvgIcon :name="featuredTool.icon" :size="40" :color="featuredTool.iconColor" />
            </view>
            <view class="task-card__row-main">
              <view class="task-card__texts">
                <text class="task-card__h">{{ featuredTool.title }}</text>
                <text class="task-card__p">{{ featuredTool.desc }}</text>
              </view>
              <view class="arrow-wrap">
                <text class="chev">›</text>
              </view>
            </view>
          </view>

          <view
            v-for="(vm, idx) in gridTools"
            :key="vm.raw.id ?? idx"
            class="task-card task-card--tile"
            @tap="onToolTap(vm.raw)"
          >
            <view class="task-card__tile-top">
              <view
                class="icon-box icon-box--sm"
                :class="{ 'icon-box--dot': vm.hot }"
                :style="{ background: vm.iconWrapBg }"
              >
                <SvgIcon :name="vm.icon" :size="34" :color="vm.iconColor" />
              </view>
              <text class="chev chev--sm">›</text>
            </view>
            <text class="task-card__tit">{{ vm.title }}</text>
            <text class="task-card__sub">{{ vm.desc }}</text>
          </view>
        </template>
      </view>

      <view class="page-bottom-space" />
    </scroll-view>

    <FloatingInspireFab @click="showInspireModal = true" />
    <InspirationRecordModal v-model:visible="showInspireModal" />
  </view>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import { getQuickEntries, type QuickEntry } from '@/api/quickEntry'
import { getHomeContent, type BannerItem } from '@/api/home'
import { useAgentStore } from '@/stores/agent'
import SvgIcon from '@/components/base/SvgIcon.vue'
import HomeBannerSwiper from '@/components/home/HomeBannerSwiper.vue'
import QuoteMarquee from '@/components/home/QuoteMarquee.vue'
import FloatingInspireFab from '@/components/home/FloatingInspireFab.vue'
import InspirationRecordModal from '@/components/home/InspirationRecordModal.vue'
import { quickEntrySvgGlyph } from '@/utils/quickEntrySvgIcon'

const agentStore = useAgentStore()

const loading = ref(true)
const entries = ref<QuickEntry[]>([])
const homeBanners = ref<BannerItem[]>([])
const quoteList = ref<string[]>([])
const showInspireModal = ref(false)

/** 无接口色时在印章红晕间轻微变化，保持参考稿温润艺匠观感 */
const COLOR_TINT_VARIANTS: Array<{ iconWrapBg: string; iconColor: string }> = [
  { iconWrapBg: 'rgba(217, 75, 54, 0.06)', iconColor: '#D94B36' },
  { iconWrapBg: 'rgba(217, 75, 54, 0.08)', iconColor: '#C43D2A' },
  { iconWrapBg: 'rgba(180, 83, 9, 0.08)', iconColor: '#B45309' },
  { iconWrapBg: 'rgba(217, 75, 54, 0.05)', iconColor: '#A03322' }
]

interface ToolCardVm {
  raw: QuickEntry
  title: string
  desc: string
  iconWrapBg: string
  icon: string
  iconColor: string
  hot: boolean
}

function normalizeHex(hex: string): string | null {
  let h = hex.trim().replace(/^#/, '')
  if (h.length === 3) {
    h = h
      .split('')
      .map((ch) => ch + ch)
      .join('')
  }
  if (!/^[0-9a-fA-F]{6}$/.test(h)) return null
  return '#' + h.toLowerCase()
}

function hexToRgb(hex: string): { r: number; g: number; b: number } | null {
  const full = normalizeHex(hex)
  if (!full) return null
  const n = parseInt(full.slice(1), 16)
  if (Number.isNaN(n)) return null
  return { r: (n >> 16) & 255, g: (n >> 8) & 255, b: n & 255 }
}

function iconName(item: QuickEntry): string {
  /** 仅用字形映射，不写死业务标题；对齐「我的」页同款 iconfont（含 Remix→小程序键） */
  return quickEntrySvgGlyph(item.icon_class)
}

function defaultSubtitle(item: QuickEntry): string {
  if (item.subtitle?.trim()) return item.subtitle.trim()
  if (item.agent_type_name) return item.agent_type_name
  const labels: Record<string, string> = {
    agent: '点击进入对话',
    skill: '技能能力',
    prompt: '一键复制提示词',
    url: '打开关联页面'
  }
  return labels[item.action_type] || '点击进入使用'
}

function colorsFromBgColor(bgColor: string | null): { iconWrapBg: string; iconColor: string } | null {
  const rgbFromApi = hexToRgb((bgColor || '').trim())
  if (rgbFromApi) {
    return {
      iconWrapBg: `rgba(${rgbFromApi.r},${rgbFromApi.g},${rgbFromApi.b},0.18)`,
      iconColor: normalizeHex(bgColor || '') || '#D94B36'
    }
  }
  return null
}

const tools = computed<ToolCardVm[]>(() =>
  entries.value.map((entry, index) => {
    const palette =
      COLOR_TINT_VARIANTS[index % COLOR_TINT_VARIANTS.length]

    const fromApi = colorsFromBgColor(entry.bg_color)
    return {
      raw: entry,
      title: entry.title,
      desc: defaultSubtitle(entry),
      iconWrapBg: fromApi?.iconWrapBg ?? palette.iconWrapBg,
      iconColor: fromApi?.iconColor ?? palette.iconColor,
      icon: iconName(entry),
      hot: entry.tag === 'hot' || entry.tag === 'new'
    }
  })
)

const featuredTool = computed(() => (tools.value.length > 0 ? tools.value[0] : null))
/** 参考稿：首条大卡 + 至多 4 个小格（2×2） */
const gridTools = computed(() => tools.value.slice(1, 5))

async function loadCommandEntries() {
  loading.value = true
  try {
    const res = await getQuickEntries('command')
    if (res.code === 200 && res.data?.entries) {
      entries.value = [...res.data.entries].sort((a, b) => (b.priority ?? 0) - (a.priority ?? 0))
    } else {
      entries.value = []
      if (res.msg) {
        uni.showToast({ title: res.msg, icon: 'none' })
      }
    }
  } finally {
    loading.value = false
  }
}

async function loadHomeExtras() {
  try {
    const res = await getHomeContent({ position: 'home_top' })
    if (res.code === 200 && res.data) {
      homeBanners.value = res.data.banners?.home_top ?? []
      const stories = res.data.founder_stories ?? []
      const announcements = res.data.announcements ?? []
      const fromArticles = [...stories, ...announcements]
        .map((a) => (a.summary || a.title || '').trim())
        .filter(Boolean)
      quoteList.value = fromArticles
    }
  } catch {
    /* 静默失败，使用组件内默认语录 */
  }
}

function navigateToChat(agentId: string, label: string, instructions?: string | null) {
  agentStore.setActiveAgent(
    {
      id: agentId,
      name: label,
      label,
      welcomeMessage: instructions?.trim() || undefined
    },
    { persist: true }
  )
  const q = [
    `agentId=${encodeURIComponent(agentId)}`,
    `label=${encodeURIComponent(label)}`
  ]
  if (instructions?.trim()) {
    q.push(`content=${encodeURIComponent(instructions.trim())}`)
  }
  uni.navigateTo({ url: `/pages/aichat/index?${q.join('&')}` })
}

function onToolTap(item: QuickEntry) {
  if (item.action_type === 'agent' && item.action_value) {
    navigateToChat(String(item.action_value), item.title || '智能体', item.instructions)
    return
  }
  if (item.action_type === 'url' && item.action_value) {
    uni.navigateTo({
      url: `/pages/common/webview?title=${encodeURIComponent(item.title)}&url=${encodeURIComponent(item.action_value)}`
    })
    return
  }
  if (item.action_type === 'prompt' && item.action_value) {
    uni.setClipboardData({
      data: item.instructions || item.action_value,
      success: () => {
        uni.showToast({ title: '已复制到剪贴板', icon: 'none' })
      }
    })
    return
  }
  uni.showToast({
    title: '该能力请使用其它终端或联系客服',
    icon: 'none',
    duration: 2200
  })
}

onShow(() => {
  loadCommandEntries()
  loadHomeExtras()
})

</script>

<style scoped lang="scss">
@import '@/styles/_variables.scss';

.page-root {
  min-height: 100vh;
  background: $bg-base;
}

.page {
  min-height: 100vh;
  box-sizing: border-box;
}

/* 主轴网格：1 张 span2 + 2×2 */
.task-grid {
  padding: 24rpx 36rpx 32rpx;
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 22rpx;
}

.task-empty {
  grid-column: 1 / -1;
  padding: 80rpx 24rpx;
  text-align: center;
  font-size: 28rpx;

  &.muted {
    color: $text-muted;
  }
}

/* 朱砂轻晕图标盒 + 热点红点 */
.icon-box {
  position: relative;
  border-radius: 28rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  border: 1rpx solid rgba(217, 75, 54, 0.1);
  box-sizing: border-box;
  /* 小图标容器微微浮起，呼应卡片立体感 */
  box-shadow:
    inset 0 2rpx 0 rgba(255, 255, 255, 0.85),
    0 6rpx 16rpx -6rpx rgba(44, 30, 26, 0.1),
    0 2rpx 6rpx -2rpx rgba(44, 30, 26, 0.05);

  &--lg {
    width: 88rpx;
    height: 88rpx;
  }

  &--sm {
    width: 72rpx;
    height: 72rpx;
    border-radius: 22rpx;
  }

  &--dot::after {
    content: '';
    position: absolute;
    top: -4rpx;
    right: -4rpx;
    width: 16rpx;
    height: 16rpx;
    background: $accent-gold;
    border-radius: 50%;
    border: 3rpx solid $white;
    box-shadow: 0 4rpx 12rpx rgba(217, 75, 54, 0.25);
  }
}

.task-card {
  background: $white;
  border: 1rpx solid rgba(44, 30, 26, 0.08);
  border-radius: 40rpx;
  box-shadow: $shadow-card-elevated;
  box-sizing: border-box;
  overflow: hidden;
  transition:
    opacity 0.2s ease,
    transform 0.22s cubic-bezier(0.33, 0.86, 0.42, 1),
    box-shadow 0.22s cubic-bezier(0.33, 0.86, 0.42, 1);

  &:active {
    opacity: 0.98;
    transform: translateY(2rpx) scale(0.992);
    box-shadow:
      inset 0 2rpx 0 rgba(255, 255, 255, 0.92),
      0 14rpx 32rpx -14rpx rgba(44, 30, 26, 0.1),
      0 6rpx 14rpx -6rpx rgba(44, 30, 26, 0.06);
  }

  /* 首张通栏大卡 */
  &--span2 {
    grid-column: span 2;
    display: flex;
    align-items: center;
    gap: 28rpx;
    padding: 32rpx 36rpx;
    min-height: auto;
  }

  /* 2×2 小砖 */
  &--tile {
    display: flex;
    flex-direction: column;
    padding: 28rpx 24rpx;
    min-height: 272rpx;
  }

  &__row-main {
    flex: 1;
    min-width: 0;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 16rpx;
  }

  &__texts {
    flex: 1;
    min-width: 0;
    display: flex;
    flex-direction: column;
    gap: 8rpx;
  }

  &__h {
    font-size: 30rpx;
    font-weight: 800;
    color: $text-main;
    line-height: 1.45;
  }

  &__p {
    font-size: 23rpx;
    color: $text-muted;
    font-weight: 500;
    line-height: 1.45;
  }

  &__tile-top {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    margin-bottom: 22rpx;
    width: 100%;
  }

  &__tit {
    font-size: 26rpx;
    font-weight: 800;
    color: $text-main;
    line-height: 1.38;
    margin-bottom: 8rpx;
    word-break: break-all;
  }

  &__sub {
    font-size: 21rpx;
    color: $text-muted;
    line-height: 1.42;
    font-weight: 500;
    overflow: hidden;
    display: -webkit-box;
    -webkit-box-orient: vertical;
    -webkit-line-clamp: 2;
    flex: 1;
    word-break: break-all;
  }
}

.arrow-wrap {
  flex-shrink: 0;
  width: 48rpx;
  height: 48rpx;
  display: flex;
  align-items: center;
  justify-content: center;
}

.chev {
  font-size: 40rpx;
  color: $accent-gold;
  opacity: 0.45;
  font-weight: 300;
  line-height: 1;

  &--sm {
    font-size: 34rpx;
  }
}

.page-bottom-space {
  height: calc(180rpx + env(safe-area-inset-bottom));
  height: calc(180rpx + constant(safe-area-inset-bottom));
}
</style>
