<template>
  <view class="page-root">
    <scroll-view scroll-y class="page" :show-scrollbar="false">
      <view class="top-bar" :style="{ paddingTop: topInsetPx + 'px' }">
        <text class="app-title">顶妈AI分身-你身边的营销大脑</text>

      </view>

      <HomeBannerSwiper :banners="homeBanners" />
      <QuoteMarquee :quotes="quoteList" />

      <view class="section">
        <view v-if="loading && tools.length === 0" class="tool-state muted">加载中…</view>
        <view v-else-if="!loading && tools.length === 0" class="tool-state muted">
          暂无智能体，敬请期待
        </view>
        <template v-else>
          <view
v-if="featuredTool" class="agent-card agent-card--featured" @tap="onToolTap(featuredTool.raw)">
            <view class="agent-card__icon-wrap" :style="{ background: featuredTool.iconWrapBg }">
              <SvgIcon :name="featuredTool.icon" :size="48" :color="featuredTool.iconColor" />
              <view v-if="featuredTool.hot" class="agent-card__dot" />
            </view>
            <view class="agent-card__body">
              <text class="agent-card__title">{{ featuredTool.title }}</text>
              <text class="agent-card__desc">{{ featuredTool.desc }}</text>
            </view>
            <text class="agent-card__arrow">›</text>
          </view>

          <view v-if="gridTools.length > 0" class="agent-grid">
            <view v-for="(vm, idx) in gridTools" :key="vm.raw.id ?? idx" class="agent-card agent-card--grid"
              @tap="onToolTap(vm.raw)">
              <view class="agent-card__top">
                <view class="agent-card__icon-wrap agent-card__icon-wrap--sm" :style="{ background: vm.iconWrapBg }">
                  <SvgIcon :name="vm.icon" :size="40" :color="vm.iconColor" />
                  <view v-if="vm.hot" class="agent-card__dot" />
                </view>
                <text class="agent-card__arrow agent-card__arrow--sm">›</text>
              </view>
              <text class="agent-card__title">{{ vm.title }}</text>
              <text class="agent-card__desc">{{ vm.desc }}</text>
            </view>
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
import { ref, computed, onMounted } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import { getQuickEntries, type QuickEntry } from '@/api/quickEntry'
import { getHomeContent, type BannerItem } from '@/api/home'
import { useSafeArea } from '@/composables/useSafeArea'
import { useAgentStore } from '@/stores/agent'
import SvgIcon from '@/components/base/SvgIcon.vue'
import HomeBannerSwiper from '@/components/home/HomeBannerSwiper.vue'
import QuoteMarquee from '@/components/home/QuoteMarquee.vue'
import FloatingInspireFab from '@/components/home/FloatingInspireFab.vue'
import InspirationRecordModal from '@/components/home/InspirationRecordModal.vue'

const { safeArea, updateSafeArea } = useSafeArea()
const agentStore = useAgentStore()
const topInsetPx = ref(12)

const loading = ref(true)
const entries = ref<QuickEntry[]>([])
const homeBanners = ref<BannerItem[]>([])
const quoteList = ref<string[]>([])
const showInspireModal = ref(false)

const CARD_PALETTE: Array<{ iconWrapBg: string; iconColor: string }> = [
  { iconWrapBg: 'rgba(243, 112, 33, 0.15)', iconColor: '#F37021' },
  { iconWrapBg: 'rgba(124, 58, 237, 0.15)', iconColor: '#7C3AED' },
  { iconWrapBg: 'rgba(59, 130, 246, 0.15)', iconColor: '#2563EB' },
  { iconWrapBg: 'rgba(37, 99, 235, 0.14)', iconColor: '#1D4ED8' },
  { iconWrapBg: 'rgba(245, 158, 11, 0.18)', iconColor: '#D97706' },
  { iconWrapBg: 'rgba(219, 39, 119, 0.14)', iconColor: '#DB2777' }
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
  let raw = (item.icon_class || '').trim()
  if (raw.startsWith('icon-')) raw = raw.slice(5)
  if (!raw) return 'linggan'
  return raw
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
      iconColor: normalizeHex(bgColor || '') || '#F37021'
    }
  }
  return null
}

const tools = computed<ToolCardVm[]>(() =>
  entries.value.map((entry, index) => {
    const palette = CARD_PALETTE[index % CARD_PALETTE.length]
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
const gridTools = computed(() => tools.value.slice(1))

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

onMounted(() => {
  updateSafeArea()
  const top =
    typeof safeArea.value.top === 'number' && safeArea.value.top > 0
      ? safeArea.value.top
      : safeArea.value.statusBarHeight || 0
  topInsetPx.value = Math.ceil(top > 0 ? top + 8 : 12)
})
</script>

<style scoped lang="scss">
@import '@/styles/_variables.scss';

.page-root {
  min-height: 100vh;
  background: #faf8f5;
}

.page {
  min-height: 100vh;
  box-sizing: border-box;
}

.top-bar {
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  padding-left: 32rpx;
  padding-right: 28rpx;
  padding-bottom: 20rpx;
  box-sizing: border-box;
}

.app-title {
  font-size: 36rpx;
  font-weight: 700;
  color: #1d2129;
  letter-spacing: 0.04em;
}

.toggle-pill {
  position: absolute;
  right: 28rpx;
  display: flex;
  align-items: center;
  gap: 14rpx;
  padding: 12rpx 22rpx;
  border-radius: 999rpx;
  background: #f3f4f6;
  flex-shrink: 0;

  &:active {
    opacity: 0.88;
  }
}

.toggle-dot {
  width: 20rpx;
  height: 20rpx;
  border-radius: 50%;
  box-sizing: border-box;
}

.toggle-dot--outline {
  border: 3rpx solid #9ca3af;
  background: transparent;
}

.toggle-dot--solid {
  background: #6b7280;
}

.section {
  margin-top: 28rpx;
  padding: 0 28rpx 24rpx;
}

.tool-state {
  padding: 48rpx 24rpx;
  text-align: center;
  font-size: 28rpx;
  color: #64748b;

  &.muted {
    color: #94a3b8;
  }
}

.agent-card {
  background: $white;
  border-radius: 24rpx;
  box-shadow: 0 4rpx 24rpx rgba(0, 0, 0, 0.05);
  box-sizing: border-box;

  &:active {
    opacity: 0.92;
  }

  &--featured {
    display: flex;
    align-items: center;
    padding: 28rpx 24rpx;
    margin-bottom: 20rpx;
    gap: 20rpx;
  }

  &--grid {
    padding: 24rpx 20rpx;
    min-height: 200rpx;
  }

  &__top {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    margin-bottom: 16rpx;
  }

  &__icon-wrap {
    position: relative;
    width: 88rpx;
    height: 88rpx;
    border-radius: 20rpx;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;

    &--sm {
      width: 72rpx;
      height: 72rpx;
      border-radius: 18rpx;
    }
  }

  &__dot {
    position: absolute;
    top: 6rpx;
    right: 6rpx;
    width: 14rpx;
    height: 14rpx;
    border-radius: 50%;
    background: #3b82f6;
    border: 2rpx solid $white;
  }

  &__body {
    flex: 1;
    min-width: 0;
  }

  &__title {
    display: block;
    font-size: 30rpx;
    font-weight: 700;
    color: #1d2129;
    line-height: 1.35;
    margin-bottom: 8rpx;
  }

  &__desc {
    display: block;
    font-size: 24rpx;
    color: #86909c;
    line-height: 1.45;
  }

  &__arrow {
    font-size: 40rpx;
    color: #c9cdd4;
    font-weight: 300;
    flex-shrink: 0;
    line-height: 1;

    &--sm {
      font-size: 36rpx;
    }
  }
}

.agent-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20rpx;
}

.page-bottom-space {
  height: calc(160rpx + env(safe-area-inset-bottom));
  height: calc(160rpx + constant(safe-area-inset-bottom));
}
</style>
