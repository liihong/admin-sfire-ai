<template>
  <view class="inspiration-page">
    <!-- 顶部导航 -->
    <view class="page-nav" :style="{ paddingTop: safeArea.top + 'px' }">
      <view class="nav-bar">
        <view class="nav-back" @tap="goBack">
          <text class="nav-back-icon">‹</text>
        </view>
        <text class="nav-title">我的灵感夹</text>
        <view class="nav-more" @tap="onMoreTap">
          <text class="nav-more-dots">••</text>
        </view>
      </view>
    </view>

    <!-- 有列表时固定在顶栏下方，仅下列表滚动 -->
    <view v-if="inspirationList.length > 0" class="section-head-strip">
      <view class="section-head">
        <text class="section-icon">💡</text>
        <text class="section-text">灵感备忘夹列表 (共 {{ total }} 条)</text>
      </view>
    </view>

    <!-- 列表区域（仅正文滚动） -->
    <scroll-view
      class="list-container"
      scroll-y
      :refresher-enabled="true"
      :refresher-triggered="refreshing"
      @refresherrefresh="handleRefresh"
      @scrolltolower="handleLoadMore"
    >
      <!-- 灵感列表 -->
      <view v-if="inspirationList.length > 0" class="inspiration-list">
        <InspirationItem
          v-for="item in inspirationList"
          :key="item.id"
          :inspiration="item"
          @generate="handleGenerate"
          @chat="handleChat"
          @edit="handleEdit"
          @delete="handleDelete"
          @pin="handlePin"
          @archive="handleArchive"
          @click="handleItemClick"
        />
      </view>

      <!-- 空状态 -->
      <view v-else-if="!loading" class="empty-state">
        <view class="empty-icon">💡</view>
        <text class="empty-text">还没有灵感记录</text>
        <text class="empty-hint">点击右下角按钮添加灵感</text>
      </view>

      <!-- 加载中 -->
      <view v-if="loading && inspirationList.length === 0" class="loading-state">
        <u-loading-icon mode="spinner" color="#b8864d"></u-loading-icon>
        <text class="loading-text">加载中...</text>
      </view>

      <!-- 加载更多提示 -->
      <view v-if="hasMore && !loading && inspirationList.length > 0" class="load-more-hint">
        <text>上拉加载更多</text>
      </view>

      <!-- 没有更多 -->
      <view v-if="!hasMore && inspirationList.length > 0" class="no-more-hint">
        <text>没有更多了</text>
      </view>

      <!-- 底部安全区 -->
      <view class="bottom-safe-area"></view>
    </scroll-view>
    
    <!-- 底部悬浮按钮 -->
    <view class="fab-wrapper">
      <view class="fab-btn" @tap="showInspirationCard = true">
        <u-icon name="plus" color="#FFFFFF" size="24"></u-icon>
      </view>
    </view>
    
    <!-- 灵感输入卡片 -->
    <InspirationCard
      :visible="showInspirationCard"
      v-model="inspirationText"
      @update:visible="showInspirationCard = $event"
      @send="handleInspirationSend"
    />
    
    <!-- 生成预览弹窗 -->
    <view v-if="showGenerateModal" class="modal-overlay" @tap="closeGenerateModal">
      <view class="modal-content" @tap.stop>
        <view class="modal-header">
          <text class="modal-title">生成的口播文案</text>
          <view class="modal-close" @tap="closeGenerateModal">
            <u-icon name="close" color="#86909C" size="20"></u-icon>
          </view>
        </view>
        <view class="modal-body">
          <scroll-view class="generated-content" scroll-y>
            <text class="content-text">{{ generatedContent }}</text>
          </scroll-view>
        </view>
        <view class="modal-footer">
          <view class="modal-btn secondary" @tap="closeGenerateModal">
            <text>关闭</text>
          </view>
          <view class="modal-btn primary" @tap="copyGeneratedContent">
            <text>复制</text>
          </view>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import type { Inspiration } from '@/api/inspiration'
import {
  getInspirationList,
  createInspiration,
  deleteInspiration,
  pinInspiration,
  archiveInspiration,
  generateScript,
} from '@/api/inspiration'
import { getBalance } from '@/api/coin'
import { useProjectStore } from '@/stores/project'
import InspirationItem from './components/InspirationItem.vue'
import InspirationCard from '@/components/inspiration/InspirationCard.vue'
import { useSafeArea } from '@/composables/useSafeArea'

const { safeArea, updateSafeArea } = useSafeArea()

// 状态
const inspirationList = ref<Inspiration[]>([])
const loading = ref(false)
const refreshing = ref(false)
const filterStatus = ref<'all' | 'active' | 'archived'>('active')
const showInspirationCard = ref(false)
const inspirationText = ref('')
const showGenerateModal = ref(false)
const generatedContent = ref('')
const currentInspiration = ref<Inspiration | null>(null)

// 分页
const pageNum = ref(1)
const pageSize = ref(10)
const total = ref(0)
const hasMore = computed(() => {
  return inspirationList.value.length < total.value
})

// 初始化
onMounted(() => {
  updateSafeArea()
  loadInspirationList()
})

function onMoreTap() {
  uni.showActionSheet({
    itemList: ['刷新列表', '全部', '活跃', '已归档'],
    success: (res) => {
      if (res.tapIndex === 0) {
        handleRefresh()
        return
      }
      const statusMap = ['all', 'active', 'archived'] as const
      setFilterStatus(statusMap[res.tapIndex - 1])
    },
  })
}

// 加载灵感列表
async function loadInspirationList(reset = false) {
  if (loading.value) return
  
  loading.value = true
  
  try {
    if (reset) {
      pageNum.value = 1
    }
    
    const params = {
      pageNum: pageNum.value,
      pageSize: pageSize.value,
      status: filterStatus.value === 'all' ? undefined : filterStatus.value,
    }
    
    const response = await getInspirationList(params)
    
    if (reset) {
      inspirationList.value = response.data.list
    } else {
      inspirationList.value.push(...response.data.list)
    }
    
    total.value = response.data.total
    pageNum.value++
  } catch (error: any) {
    uni.showToast({
      title: error.message || '加载失败',
      icon: 'none',
    })
  } finally {
    loading.value = false
    refreshing.value = false
  }
}

// 设置筛选状态
function setFilterStatus(status: 'all' | 'active' | 'archived') {
  filterStatus.value = status
  loadInspirationList(true)
}

// 下拉刷新
function handleRefresh() {
  refreshing.value = true
  loadInspirationList(true)
}

// 上拉加载更多
function handleLoadMore() {
  if (hasMore.value && !loading.value) {
    loadInspirationList(false)
  }
}

// 返回
function goBack() {
  uni.navigateBack({
    fail: () => {
      uni.switchTab({ url: '/pages/home/index' })
    },
  })
}

// 处理灵感发送
async function handleInspirationSend(text: string, tags: string[]) {
  try {
    const projectStore = useProjectStore()
    
    // 转换 project_id 为 number 类型（如果存在）
    const projectId = projectStore.activeProject?.id 
      ? Number(projectStore.activeProject.id) 
      : undefined
    
    await createInspiration({
      content: text,
      tags,
      project_id: projectId,
    })
    
    uni.showToast({ title: '灵感已保存', icon: 'success' })
    inspirationText.value = ''
    showInspirationCard.value = false
    
    // 刷新列表
    loadInspirationList(true)
  } catch (error: any) {
    uni.showToast({
      title: error.message || '保存失败',
      icon: 'none',
    })
  }
}

// 生成文案
async function handleGenerate(inspiration: Inspiration) {
  // 检查余额
  try {
    const balanceResponse = await getBalance()
    if (balanceResponse.data.available_balance <= 0) {
      uni.showModal({
        title: '提示',
        content: '余额不足，请充值后再试',
        showCancel: false,
      })
      return
    }
  } catch (error) {
    console.error('获取余额失败:', error)
  }
  
  // 如果已有生成内容，询问是否覆盖
  if (inspiration.generated_content) {
    const res = await uni.showModal({
      title: '提示',
      content: '该灵感已有生成内容，是否覆盖？',
      confirmText: '覆盖',
      cancelText: '取消',
    })
    
    if (!res.confirm) {
      // 显示已有内容
      generatedContent.value = inspiration.generated_content
      showGenerateModal.value = true
      return
    }
  }
  
  // 显示加载中
  uni.showLoading({ title: '生成中...' })
  
  try {
    const response = await generateScript({
      inspiration_id: inspiration.id,
      agent_type: 'ip_collector',
    })
    
    generatedContent.value = response.content
    currentInspiration.value = inspiration
    showGenerateModal.value = true
    
    // 刷新列表
    loadInspirationList(true)
  } catch (error: any) {
    uni.showToast({
      title: error.message || '生成失败',
      icon: 'none',
    })
  } finally {
    uni.hideLoading()
  }
}

// 跳转AI对话
function handleChat(inspiration: Inspiration) {
  uni.navigateTo({
    url: `/pages/copywriting/index?agentId=35&inspiration_id=${inspiration.id}&content=${encodeURIComponent(inspiration.content)}`,
  })
}

// 编辑灵感
function handleEdit(inspiration: Inspiration) {
  uni.showToast({ title: '编辑功能开发中', icon: 'none' })
}

// 删除灵感
async function handleDelete(inspiration: Inspiration) {
  const res = await uni.showModal({
    title: '确认删除',
    content: '确定要删除这条灵感吗？',
    confirmText: '删除',
    cancelText: '取消',
  })
  
  if (!res.confirm) return
  
  try {
    await deleteInspiration(inspiration.id)
    uni.showToast({ title: '删除成功', icon: 'success' })
    loadInspirationList(true)
  } catch (error: any) {
    uni.showToast({
      title: error.message || '删除失败',
      icon: 'none',
    })
  }
}

// 置顶/取消置顶
async function handlePin(inspiration: Inspiration) {
  try {
    await pinInspiration(inspiration.id, !inspiration.is_pinned)
    uni.showToast({
      title: inspiration.is_pinned ? '已取消置顶' : '已置顶',
      icon: 'success',
    })
    loadInspirationList(true)
  } catch (error: any) {
    uni.showToast({
      title: error.message || '操作失败',
      icon: 'none',
    })
  }
}

// 归档/取消归档
async function handleArchive(inspiration: Inspiration) {
  try {
    const newStatus = inspiration.status === 'archived' ? 'active' : 'archived'
    await archiveInspiration(inspiration.id, newStatus)
    uni.showToast({
      title: newStatus === 'archived' ? '已归档' : '已取消归档',
      icon: 'success',
    })
    loadInspirationList(true)
  } catch (error: any) {
    uni.showToast({
      title: error.message || '操作失败',
      icon: 'none',
    })
  }
}

// 点击灵感项
function handleItemClick(inspiration: Inspiration) {
  // 跳转到详情页或展开详情（功能待实现）
}

// 关闭生成预览弹窗
function closeGenerateModal() {
  showGenerateModal.value = false
  generatedContent.value = ''
  currentInspiration.value = null
}

// 复制生成内容
function copyGeneratedContent() {
  uni.setClipboardData({
    data: generatedContent.value,
    success: () => {
      uni.showToast({ title: '已复制', icon: 'success' })
    },
  })
}
</script>

<style lang="scss" scoped>
@import '@/styles/_variables.scss';

.inspiration-page {
  height: 100vh;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  box-sizing: border-box;
  /** 与设计稿一致的暖燕麦底 */
  background: $quote-marquee-strip-bg;
}

.page-nav {
  flex-shrink: 0;
  background: $quote-marquee-strip-bg;
}

.nav-bar {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  height: 88rpx;
  padding: 0 32rpx;
}

.nav-back {
  position: absolute;
  left: 24rpx;
  width: 64rpx;
  height: 64rpx;
  display: flex;
  align-items: center;
  justify-content: center;

  &:active {
    opacity: 0.6;
  }
}

.nav-back-icon {
  font-size: 48rpx;
  font-weight: 300;
  color: $text-main;
  line-height: 1;
}

.nav-title {
  font-size: 34rpx;
  font-weight: 800;
  color: $text-main;
}

.nav-more {
  position: absolute;
  right: 32rpx;
  min-width: 72rpx;
  height: 56rpx;
  padding: 0 20rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(255, 255, 255, 0.85);
  border: 1rpx solid rgba(44, 30, 26, 0.08);
  border-radius: 999rpx;

  &:active {
    opacity: 0.75;
  }
}

.nav-more-dots {
  font-size: 22rpx;
  letter-spacing: 2rpx;
  color: $text-muted;
  line-height: 1;
}

.section-head-strip {
  flex-shrink: 0;
  box-sizing: border-box;
  width: 100%;
  padding: 20rpx 40rpx 24rpx;
  background: $quote-marquee-strip-bg;
  border-bottom: 1rpx solid rgba(44, 30, 26, 0.04);
}

.list-container {
  flex: 1;
  height: 0;
  min-height: 0;
  box-sizing: border-box;
  padding: 8rpx 40rpx 0;
}

.section-head {
  display: flex;
  align-items: center;
  gap: 10rpx;
  padding: 0;
}

.section-icon {
  font-size: 28rpx;
  line-height: 1;
}

.section-text {
  font-size: 28rpx;
  font-weight: 800;
  color: $text-main;
}

.inspiration-list {
  display: flex;
  flex-direction: column;
  gap: 24rpx;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 160rpx 32rpx;

  .empty-icon {
    font-size: 80rpx;
    margin-bottom: 24rpx;
  }

  .empty-text {
    font-size: 28rpx;
    color: $text-muted-warm;
    margin-bottom: 12rpx;
  }

  .empty-hint {
    font-size: 24rpx;
    color: $text-muted-warm;
    opacity: 0.85;
    text-align: center;
    line-height: 1.6;
  }
}

.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 160rpx 32rpx;

  .loading-text {
    margin-top: 16rpx;
    font-size: 24rpx;
    color: $text-muted-warm;
  }
}

.load-more-hint,
.no-more-hint {
  text-align: center;
  padding: 32rpx;
  font-size: 24rpx;
  color: $text-muted;
  opacity: 0.75;
}

.fab-wrapper {
  position: fixed;
  right: 40rpx;
  bottom: calc(48rpx + env(safe-area-inset-bottom));
  z-index: 99;

  .fab-btn {
    width: 96rpx;
    height: 96rpx;
    background: linear-gradient(135deg, $accent-gold 0%, #b45309 100%);
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    border: 1rpx solid rgba(255, 255, 255, 0.25);
    box-shadow: 0 16rpx 42rpx rgba(217, 75, 54, 0.28);

    &:active {
      transform: scale(0.94);
      opacity: 0.94;
    }
  }
}

.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;

  .modal-content {
    width: 90%;
    max-height: 80vh;
    background: #fff;
    border-radius: 24rpx;
    display: flex;
    flex-direction: column;

    .modal-header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 32rpx;
      border-bottom: 1rpx solid $border-color;

      .modal-title {
        font-size: 32rpx;
        font-weight: 600;
        color: $text-main;
      }

      .modal-close {
        width: 48rpx;
        height: 48rpx;
        display: flex;
        align-items: center;
        justify-content: center;
      }
    }

    .modal-body {
      flex: 1;
      padding: 32rpx;
      overflow: hidden;

      .generated-content {
        max-height: 60vh;

        .content-text {
          font-size: 28rpx;
          color: $text-main;
          line-height: 1.8;
          white-space: pre-wrap;
        }
      }
    }

    .modal-footer {
      display: flex;
      gap: 24rpx;
      padding: 32rpx;
      border-top: 1rpx solid $border-color;

      .modal-btn {
        flex: 1;
        padding: 24rpx;
        text-align: center;
        border-radius: 16rpx;
        font-size: 28rpx;

        &.secondary {
          background: #f5f0ea;
          color: $text-main;
        }

        &.primary {
          background: linear-gradient(135deg, #d4a574 0%, #b8864d 100%);
          color: #fff;
        }
      }
    }
  }
}

.bottom-safe-area {
  /** 留白：列表末条与 FAB、Home 指示条不挤 */
  height: calc(200rpx + env(safe-area-inset-bottom));
}
</style>

