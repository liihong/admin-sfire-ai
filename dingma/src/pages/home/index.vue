<template>
  <scroll-view scroll-y class="page" enhanced :show-scrollbar="false">
    <view class="top-bar" :style="{ paddingTop: topInsetPx + 'px' }">
      <text class="app-title">顶顶妈AI分身</text>
      <view class="toggle-pill" @tap="onHeaderToggle">
        <view class="toggle-dot toggle-dot--outline" />
        <view class="toggle-dot toggle-dot--solid" />
      </view>
    </view>

    <view class="banner-wrap" :style="bannerWrapStyle">
      <view class="banner-mask" />
      <view class="banner-inner">
        <view class="banner-copy">
          <text class="banner-title">顶妈 AI 爆款助手</text>
          <text class="banner-sub">✨ 你身边不停歇的私人创业导师</text>
        </view>
        <view class="price-pill">
          <text class="price-pill-text">¥ 365/年 · 让创业更简单一点</text>
        </view>
      </view>
    </view>

    <view class="section">
      <view class="section-head">
        <text class="section-title">⚡️ 核心工具箱</text>
        <text class="section-hint">SELECT TOOL</text>
      </view>

      <view v-if="loading && tools.length === 0" class="tool-state muted">加载中…</view>
      <view v-else-if="!loading && tools.length === 0" class="tool-state muted">
        暂无快捷指令，敬请期待
      </view>
      <view v-else class="tool-grid">
        <view
v-for="(vm, idx) in tools" :key="vm.raw.id ?? idx"
          class="tool-card"
:style="{ background: vm.bg }"
          @tap="onToolTap(vm.raw)"
        >
          <view v-if="vm.hot" class="hot-badge">
            <text class="hot-badge-text">HOT</text>
          </view>
          <view class="tool-icon-wrap" :style="{ background: vm.iconWrapBg }">
            <SvgIcon :name="vm.icon" :size="44" :color="vm.iconColor" />
          </view>
          <text class="tool-title">{{ vm.title }}</text>
          <text class="tool-desc">{{ vm.desc }}</text>
        </view>
      </view>
    </view>

    <view class="page-bottom-space" />
  </scroll-view>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import { getQuickEntries, type QuickEntry } from '@/api/quickEntry'
import { DINGMA_HOME_BANNER_URL } from '@/constants/tenant'
import { useSafeArea } from '@/composables/useSafeArea'
import SvgIcon from '@/components/base/SvgIcon.vue'

const bannerUrl = DINGMA_HOME_BANNER_URL

/** 背景图置顶对齐（aspectFill 默认居中裁剪） */
const bannerWrapStyle = computed(() => ({
  backgroundImage: `url("${bannerUrl}")`
}))
const { safeArea, updateSafeArea } = useSafeArea()
const topInsetPx = ref(12)

const loading = ref(true)
const entries = ref<QuickEntry[]>([])

/** 与原先静态卡片一致的浅色底（接口无 bg_color 时按序号轮转） */
const CARD_PALETTE: Array<{ bg: string; iconWrapBg: string; iconColor: string }> = [
  { bg: '#FFF7E6', iconWrapBg: 'rgba(234, 88, 12, 0.18)', iconColor: '#EA580C' },
  { bg: '#F5F3FF', iconWrapBg: 'rgba(124, 58, 237, 0.2)', iconColor: '#7C3AED' },
  { bg: '#E8F4FC', iconWrapBg: 'rgba(59, 130, 246, 0.2)', iconColor: '#2563EB' },
  { bg: '#ECF5FF', iconWrapBg: 'rgba(37, 99, 235, 0.16)', iconColor: '#1D4ED8' },
  { bg: '#FFFBEB', iconWrapBg: 'rgba(245, 158, 11, 0.22)', iconColor: '#D97706' },
  { bg: '#FDF2F8', iconWrapBg: 'rgba(219, 39, 119, 0.16)', iconColor: '#DB2777' }
]

interface ToolCardVm {
  raw: QuickEntry
  title: string
  desc: string
  bg: string
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

function rgbToHex(r: number, g: number, b: number): string {
  return (
    '#' +
    [r, g, b]
      .map((x) =>
        Math.max(0, Math.min(255, x))
          .toString(16)
          .padStart(2, '0')
      )
      .join('')
  )
}

function mixRgbWhite(rgb: { r: number; g: number; b: number }, t: number): { r: number; g: number; b: number } {
  return {
    r: Math.round(rgb.r + (255 - rgb.r) * t),
    g: Math.round(rgb.g + (255 - rgb.g) * t),
    b: Math.round(rgb.b + (255 - rgb.b) * t)
  }
}

function colorsFromBgColor(bgColor: string | null): { bg: string; iconWrapBg: string; iconColor: string } | null {
  const c = (bgColor || '').trim()
  const rgbFromApi = hexToRgb(c)
  if (rgbFromApi) {
    const light = mixRgbWhite(rgbFromApi, 0.88)
    return {
      bg: rgbToHex(light.r, light.g, light.b),
      iconWrapBg: `rgba(${rgbFromApi.r},${rgbFromApi.g},${rgbFromApi.b},0.2)`,
      iconColor: normalizeHex(c) || rgbToHex(rgbFromApi.r, rgbFromApi.g, rgbFromApi.b)
    }
  }
  if (c.startsWith('rgb')) {
    return { bg: '#F8FAFC', iconWrapBg: 'rgba(100,116,139,0.18)', iconColor: '#475569' }
  }
  return null
}

/** SvgIcon 使用 icon- 前缀内的名字，与快捷入口列表一致 */
function iconName(item: QuickEntry): string {
  let raw = (item.icon_class || '').trim()
  if (raw.startsWith('icon-')) raw = raw.slice(5)
  if (!raw) return 'linggan'
  return raw
}

function defaultSubtitle(item: QuickEntry): string {
  if (item.agent_type_name) return item.agent_type_name
  const labels: Record<string, string> = {
    agent: '对话智能体',
    skill: '技能能力',
    prompt: '一键复制提示词',
    url: '打开关联页面'
  }
  return labels[item.action_type] || '点击进入使用'
}

const tools = computed<ToolCardVm[]>(() =>
  entries.value.map((entry, index) => {
    const palette = CARD_PALETTE[index % CARD_PALETTE.length]
    const fromApi = colorsFromBgColor(entry.bg_color)
    return {
      raw: entry,
      title: entry.title,
      desc: entry.subtitle || defaultSubtitle(entry),
      bg: fromApi?.bg ?? palette.bg,
      iconWrapBg: fromApi?.iconWrapBg ?? palette.iconWrapBg,
      iconColor: fromApi?.iconColor ?? palette.iconColor,
      icon: iconName(entry),
      hot: entry.tag === 'hot'
    }
  })
)

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

function onHeaderToggle() {
  uni.showToast({ title: '更多设置即将上线', icon: 'none' })
}

function onToolTap(item: QuickEntry) {
  if (item.action_type === 'agent' && item.action_value) {
    const label = encodeURIComponent(item.title || '智能体')
    const id = encodeURIComponent(String(item.action_value))
    uni.navigateTo({
      url: `/pages/aichat/index?agentId=${id}&label=${label}`
    })
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
})

onMounted(() => {
  updateSafeArea()
  const top =
    typeof safeArea.value.top === 'number' && safeArea.value.top > 0
      ? safeArea.value.top
      : safeArea.value.statusBarHeight || 0
  topInsetPx.value = Math.ceil(top > 0 ? top + 8 : 12)
  // 与 onShow 互补：部分机型/首进 Tab 时仅 onShow 请求偶发失败，挂载后再拉一次保障可见
  loadCommandEntries()
})
</script>

<style scoped lang="scss">
.page {
  min-height: 100vh;
  background: #ffffff;
    box-sizing: border-box;
  }
  
  .top-bar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding-left: 32rpx;
    padding-right: 28rpx;
    padding-bottom: 20rpx;
    box-sizing: border-box;
  }
  
  .app-title {
    font-size: 40rpx;
    font-weight: 700;
    color: #1d2129;
    letter-spacing: 0.02em;
  }
  
  .toggle-pill {
    display: flex;
    align-items: center;
    gap: 14rpx;
    padding: 12rpx 22rpx;
    border-radius: 999rpx;
    background: #f3f4f6;
    flex-shrink: 0;
  }
  
  .toggle-pill:active {
    opacity: 0.88;
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
.banner-wrap {
  position: relative;
  margin: 0 28rpx;
  height: 360rpx;
  border-radius: 40rpx;
  overflow: hidden;
  box-shadow: 0 12rpx 40rpx rgba(33, 37, 41, 0.1);
    background-size: cover;
    background-position: top center;
    background-repeat: no-repeat;
}

.banner-mask {
  position: absolute;
  inset: 0;
  background: linear-gradient(
    180deg,
    rgba(0, 0, 0, 0.22) 0%,
      rgba(0, 0, 0, 0.42) 100%
  );
}

.banner-inner {
  position: relative;
  z-index: 2;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  box-sizing: border-box;
  height: 100%;
  padding: 40rpx 32rpx 32rpx;
}

.banner-copy {
  display: flex;
  flex-direction: column;
    gap: 16rpx;
    align-items: flex-start;
}

.banner-title {
  font-size: 44rpx;
  font-weight: 700;
  color: #fff;
  letter-spacing: 0.02em;
  text-shadow: 0 4rpx 16rpx rgba(0, 0, 0, 0.28);
}

.banner-sub {
  font-size: 26rpx;
  color: rgba(255, 255, 255, 0.95);
  line-height: 1.4;
  text-shadow: 0 2rpx 12rpx rgba(0, 0, 0, 0.2);
}

.price-pill {
  align-self: flex-start;
  padding: 14rpx 28rpx;
  border-radius: 999rpx;
  background: rgba(255, 255, 255, 0.88);
    backdrop-filter: blur(8px);
}

.price-pill-text {
  font-size: 24rpx;
  font-weight: 600;
  color: #334155;
}

.section {
  margin-top: 44rpx;
  padding: 0 28rpx 24rpx;
}

.section-head {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  margin-bottom: 28rpx;
}

.section-title {
  font-size: 34rpx;
  font-weight: 700;
  color: #1d2129;
}

.section-hint {
  font-size: 20rpx;
  font-weight: 500;
  color: #c0c4cc;
  letter-spacing: 0.12em;
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

.tool-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20rpx;
}

.tool-card {
  position: relative;
  border-radius: 28rpx;
    padding: 28rpx 24rpx;
    min-height: 208rpx;
  box-sizing: border-box;
  overflow: hidden;
  box-shadow: 0 4rpx 20rpx rgba(0, 0, 0, 0.04);
}

.tool-card:active {
  opacity: 0.92;
}

.hot-badge {
  position: absolute;
  top: 16rpx;
  right: 16rpx;
    padding: 4rpx 12rpx;
    border-radius: 10rpx;
    background: linear-gradient(135deg, #f87171 0%, #ef4444 100%);
    box-shadow: 0 4rpx 10rpx rgba(239, 68, 68, 0.3);
}

.hot-badge-text {
  font-size: 18rpx;
  font-weight: 800;
  color: #fff;
  letter-spacing: 0.06em;
}

.tool-icon-wrap {
  width: 64rpx;
  height: 64rpx;
  border-radius: 18rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 20rpx;
}

.tool-title {
  display: block;
  font-size: 30rpx;
  font-weight: 700;
  color: #1d2129;
  margin-bottom: 10rpx;
}

.tool-desc {
  display: block;
  font-size: 22rpx;
  color: #64748b;
  line-height: 1.45;
}

.page-bottom-space {
  height: calc(28rpx + env(safe-area-inset-bottom));
  height: calc(28rpx + constant(safe-area-inset-bottom));
}
</style>
