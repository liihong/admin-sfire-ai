<template>
  <view class="page">
    <SafeAreaTop />
    <view class="header">
      <text class="slogan">今天你在做什么？来和顶顶妈的AI分身对话把~</text>
    </view>

    <scroll-view scroll-y class="list-wrap" :refresher-enabled="true" :refresher-triggered="refreshing" @refresherrefresh="onRefresh">
      <view v-if="loading && entries.length === 0" class="state">加载中…</view>
      <view v-else-if="!loading && entries.length === 0" class="state muted">暂无快捷指令</view>
      <view v-else class="list">
        <view
          v-for="item in entries"
          :key="item.id"
          class="card"
          @tap="onEntryTap(item)"
        >
          <view class="icon-col">
            <view class="icon-wrap">
              <image class="icon-img" :src="entryListAvatarUrl" mode="aspectFill" />
            </view>
          </view>
          <view class="meta">
            <view class="row-top">
              <text class="card-title">{{ item.title }}</text>
              <text v-if="item.tag !== 'none'" class="tag" :class="'tag--' + item.tag">{{ tagLabel(item.tag) }}</text>
            </view>
            <text v-if="item.subtitle" class="card-sub">{{ item.subtitle }}</text>
            <view class="row-bottom">
              <text class="type-pill">{{ actionLabel(item.action_type) }}</text>
              <text v-if="item.agent_type_name" class="hint">{{ item.agent_type_name }}</text>
            </view>
          </view>
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
import { DINGMA_AGENT_DEFAULT_AVATAR_URL } from '@/constants/tenant'

const entryListAvatarUrl = DINGMA_AGENT_DEFAULT_AVATAR_URL

const entries = ref<QuickEntry[]>([])
const loading = ref(true)
const refreshing = ref(false)

function tagLabel(tag: QuickEntry['tag']) {
  if (tag === 'new') return '新'
  if (tag === 'hot') return '热'
  return ''
}

function actionLabel(t: QuickEntry['action_type']) {
  const m: Record<string, string> = {
    agent: '智能体',
    skill: '技能',
    prompt: '提示词',
    url: '链接'
  }
  return m[t] || t
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
  background: #f5f7fa;
  display: flex;
  flex-direction: column;
}

.header {
  padding: 8rpx 32rpx 24rpx;
  background: $white;
  border-bottom: 1rpx solid #f0f0f0;
}

.slogan {
  display: block;
  font-size: 30rpx;
  font-weight: 600;
  color: #1d2129;
  line-height: 1.55;
}

.list-wrap {
  flex: 1;
  height: 0;
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
  padding: 24rpx;
}

.card {
  display: flex;
  gap: 24rpx;
  padding: 28rpx;
  margin-bottom: 20rpx;
  background: $white;
  border-radius: 20rpx;
  box-shadow: 0 4rpx 20rpx rgba(0, 0, 0, 0.06);
}

.card:active {
  opacity: 0.92;
}

.icon-col {
  flex-shrink: 0;
}

.icon-wrap {
  width: 96rpx;
  height: 96rpx;
  border-radius: 20rpx;
  overflow: hidden;
  flex-shrink: 0;
  background: #f5f5f5;
  box-shadow: 0 2rpx 12rpx rgba(0, 0, 0, 0.06);
}

.icon-img {
  width: 100%;
  height: 100%;
  display: block;
}

.meta {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 10rpx;
}

.row-top {
  display: flex;
  align-items: center;
  gap: 12rpx;
}

.card-title {
  flex: 1;
  min-width: 0;
  font-size: 32rpx;
  font-weight: 600;
  color: #1d2129;
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
  color: #86909c;
  line-height: 1.45;
}

.row-bottom {
  display: flex;
  align-items: center;
  gap: 16rpx;
  flex-wrap: wrap;
}

.type-pill {
  font-size: 22rpx;
  color: #f37021;
  background: rgba(243, 112, 33, 0.12);
  padding: 6rpx 16rpx;
  border-radius: 999rpx;
}

.hint {
  font-size: 22rpx;
  color: #c9cdd4;
}

.bottom-gap {
  height: 40rpx;
}
</style>
