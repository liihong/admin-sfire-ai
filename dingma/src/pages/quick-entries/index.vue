<template>
  <view class="page">
    <SafeAreaTop />
   <scroll-view scroll-y class="list-wrap" :refresher-enabled="true" :refresher-triggered="refreshing"
      @refresherrefresh="onRefresh">
      <view class="hero">
        <view class="hero-orb">
          <image class="hero-logo" :src="entryListAvatarUrl" mode="aspectFill" />
        </view>
        <text class="hero-title">顶妈 AI</text>
        <text class="hero-sub">您的私人创富助理</text>
      </view>

      <view v-if="loading && entries.length === 0" class="state">加载中…</view>
     <view v-else-if="!loading && entries.length === 0" class="state muted">暂无进阶能力，敬请期待</view>
      <view v-else class="list">
        <view
v-for="(item, index) in entries"
          :key="item.id"
          class="card"
          @tap="onEntryTap(item)"
        >
         <view class="icon-tile" :style="{ background: iconBg(item, index) }">
            <SvgIcon :name="iconName(item)" :size="44" color="#FFFFFF" />
          </view>
          <view class="meta">
           <view class="row-title">
              <text class="card-title">{{ item.title }}</text>
             <text v-if="item.tag !== 'none'" class="tag" :class="'tag--' + item.tag">{{
                tagLabel(item.tag)
              }}</text>
            </view>
           <text class="card-sub">{{ item.subtitle || defaultSubtitle(item) }}</text>
          </view>
         <text class="chevron">›</text>
        </view>
      </view>
      <view class="bottom-gap" />
    </scroll-view>
  </view>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import { getQuickEntries, type QuickEntry } from '@/api/quickEntry'
import SafeAreaTop from '@/components/common/SafeAreaTop.vue'
import SvgIcon from '@/components/base/SvgIcon.vue'
import { DINGMA_AGENT_DEFAULT_AVATAR_URL } from '@/constants/tenant'

const entryListAvatarUrl = DINGMA_AGENT_DEFAULT_AVATAR_URL

/** 参考 KITTEN 类界面的图标强调色轮转（接口未下发 bg_color 时使用） */
const ACCENT_FALLBACK = ['#22C55E', '#F97316', '#14B8A6', '#15803D', '#2563EB']

const entries = ref<QuickEntry[]>([])
const loading = ref(true)
const refreshing = ref(false)

function tagLabel(tag: QuickEntry['tag']) {
  if (tag === 'new') return '新'
  if (tag === 'hot') return '热'
  return ''
}

function iconName(item: QuickEntry) {
  const raw = (item.icon_class || '').trim()
  if (raw) return raw
  return 'linggan'
}

function iconBg(item: QuickEntry, index: number) {
  const c = (item.bg_color || '').trim()
  if (c && /^#([0-9a-fA-F]{3}|[0-9a-fA-F]{6})$/.test(c)) return c
  if (c && c.startsWith('rgb')) return c
  return ACCENT_FALLBACK[index % ACCENT_FALLBACK.length]
}

function defaultSubtitle(item: QuickEntry) {
  if (item.agent_type_name) return item.agent_type_name
  const labels: Record<string, string> = {
    agent: '对话智能体',
    skill: '技能能力',
    prompt: '一键复制提示词',
    url: '打开关联页面'
  }
  return labels[item.action_type] || '点击进入使用'
}

async function loadList() {
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
    refreshing.value = false
  }
}

async function onRefresh() {
  refreshing.value = true
  await loadList()
}

function onEntryTap(item: QuickEntry) {
  if (item.action_type === 'agent' && item.action_value) {
    const label = encodeURIComponent(item.title || '智能体')
    const id = encodeURIComponent(String(item.action_value))
    uni.navigateTo({
      url: `/pages/aichat/index?agentId=${id}&label=${label}`
    })
    return
  }
  if (item.action_type === 'url' && item.action_value) {
    const url = encodeURIComponent(item.action_value)
    uni.navigateTo({
      url: `/pages/common/webview?title=${encodeURIComponent(item.title)}&url=${url}`
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
  loadList()
})
</script>

<style scoped lang="scss">
@import '@/styles/_variables.scss';

.page {
  min-height: 100vh;
  background-color: #ffffff;
    background-image: radial-gradient(circle, rgba(0, 0, 0, 0.06) 1rpx, transparent 1rpx);
    background-size: 28rpx 28rpx;
  display: flex;
  flex-direction: column;
}

.list-wrap {
  flex: 1;
  height: 0;
}

.hero {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 24rpx 32rpx 40rpx;
}

.hero-orb {
  width: 180rpx;
  height: 180rpx;
  border-radius: 50%;
  background: linear-gradient(160deg, #1e3a5f 0%, #0f172a 55%, #020617 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow:
    0 20rpx 56rpx rgba(15, 23, 42, 0.28),
    inset 0 2rpx 0 rgba(255, 255, 255, 0.12);
}

.hero-logo {
  width: 120rpx;
  height: 120rpx;
  border-radius: 50%;
  display: block;
}

.hero-title {
  margin-top: 28rpx;
  font-size: 44rpx;
  font-weight: 700;
  color: #000000;
  letter-spacing: 2rpx;
}

.hero-sub {
  margin-top: 12rpx;
  font-size: 28rpx;
  color: #888888;
  font-weight: 400;
}

.state {
  padding: 80rpx 32rpx;
  text-align: center;
  font-size: 28rpx;
  color: #1d2129;
}

.state.muted {
  color: #86909c;
}

.list {
  padding: 0 32rpx;
}

.card {
  display: flex;
  align-items: center;
  gap: 24rpx;
  padding: 28rpx 24rpx;
    margin-bottom: 24rpx;
    background: #ffffff;
    border-radius: 24rpx;
    border: 1rpx solid rgba(0, 0, 0, 0.06);
    box-shadow: 0 8rpx 32rpx rgba(15, 23, 42, 0.06);
}

.card:active {
  opacity: 0.92;
}

.icon-tile {
  flex-shrink: 0;
  width: 100rpx;
    height: 100rpx;
    border-radius: 22rpx;
    display: flex;
    align-items: center;
    justify-content: center;
}

.meta {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 10rpx;
}

.row-title {
  display: flex;
  align-items: center;
  gap: 12rpx;
}

.card-title {
  flex: 1;
  min-width: 0;
  font-size: 32rpx;
  font-weight: 600;
  color: #000000;
    line-height: 1.35;
}

.tag {
  flex-shrink: 0;
  font-size: 20rpx;
  padding: 4rpx 12rpx;
  border-radius: 8rpx;
  color: #fff;
  font-weight: 600;
}

.tag--new {
  background: #3b82f6;
}

.tag--hot {
  background: #ef4444;
}

.card-sub {
  font-size: 26rpx;
  color: #888888;
  line-height: 1.45;
  display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
}

.chevron {
  flex-shrink: 0;
  font-size: 36rpx;
  color: #c9cdd4;
  font-weight: 300;
    line-height: 1;
    padding-left: 8rpx;
}

.bottom-gap {
  height: 40rpx;
}
</style>
