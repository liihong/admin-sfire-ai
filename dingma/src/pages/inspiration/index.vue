<template>
  <view class="inspiration-page">
    <!-- 顶部导航栏 -->
    <BaseHeader title="我的灵感" @back="goBack">
    </BaseHeader>
    
    <!-- 搜索框 -->
    <view class="search-section">
      <view class="search-box">
        <u-icon name="search" color="#86909C" size="18"></u-icon>
        <input
          class="search-input"
          v-model="searchKeyword"
          placeholder="搜索灵感内容..."
          @input="handleSearchInput"
        />
        <view v-if="searchKeyword" class="clear-btn" @tap="clearSearch">
          <u-icon name="close" color="#86909C" size="16"></u-icon>
        </view>
      </view>
    </view>
    
    <!-- 筛选菜单 -->
    <view v-if="showFilterMenu" class="filter-menu">
      <view class="filter-item" :class="{ active: filterStatus === 'all' }" @tap="setFilterStatus('all')">
        <text>全部</text>
      </view>
      <view class="filter-item" :class="{ active: filterStatus === 'active' }" @tap="setFilterStatus('active')">
        <text>活跃</text>
      </view>
      <view class="filter-item" :class="{ active: filterStatus === 'archived' }" @tap="setFilterStatus('archived')">
        <text>已归档</text>
      </view>
    </view>
    
    <!-- 列表区域 -->
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
      <view v-if="loading" class="loading-state">
        <u-loading-icon mode="spinner" color="#3B82F6"></u-loading-icon>
        <text class="loading-text">加载中...</text>
      </view>
      
      <!-- 加载更多提示 -->
      <view v-if="hasMore && !loading" class="load-more-hint">
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
import BaseHeader from '@/components/base/BaseHeader.vue'
import SvgIcon from '@/components/base/SvgIcon.vue'

// 状态
const inspirationList = ref<Inspiration[]>([])
const loading = ref(false)
const refreshing = ref(false)
const searchKeyword = ref('')
const filterStatus = ref<'all' | 'active' | 'archived'>('all')
const showFilterMenu = ref(false)
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

// 防抖定时器
let searchTimer: ReturnType<typeof setTimeout> | null = null

// 初始化
onMounted(() => {
  loadInspirationList()
})

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
      keyword: searchKeyword.value || undefined,
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

// 搜索输入处理（防抖）
function handleSearchInput() {
  if (searchTimer) {
    clearTimeout(searchTimer)
  }
  
  searchTimer = setTimeout(() => {
    loadInspirationList(true)
  }, 300)
}

// 清空搜索
function clearSearch() {
  searchKeyword.value = ''
  loadInspirationList(true)
}

// 设置筛选状态
function setFilterStatus(status: 'all' | 'active' | 'archived') {
  filterStatus.value = status
  showFilterMenu.value = false
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
    url: `/pages/copywriting/index?agentId=20&inspiration_id=${inspiration.id}&content=${encodeURIComponent(inspiration.content)}`,
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
  min-height: 100vh;
  background: $bg-color;
  
  .search-section {
    padding: $spacing-md $spacing-lg;
    background: $white;
    
    .search-box {
      display: flex;
      align-items: center;
      gap: $spacing-sm;
      padding: $spacing-sm $spacing-md;
      background: $bg-light;
      border-radius: $radius-xl;
      
      .search-input {
        flex: 1;
        font-size: $font-size-md;
        color: $text-main;
      }
      
      .clear-btn {
        width: 32rpx;
        height: 32rpx;
        display: flex;
        align-items: center;
        justify-content: center;
      }
    }
  }
  
  .filter-menu {
    display: flex;
    gap: $spacing-sm;
    padding: $spacing-sm $spacing-lg;
    background: $white;
    border-bottom: 1rpx solid $border-color;
    
    .filter-item {
      padding: 8rpx 16rpx;
      border-radius: $radius-md;
      font-size: $font-size-sm;
      color: $text-second;
      background: $bg-light;
      
      &.active {
        color: $primary-orange;
        background: rgba($primary-orange, 0.1);
      }
    }
  }
  
  .list-container {
    height: calc(100vh - 200rpx);
  }
  
  .inspiration-list {
    padding: $spacing-md $spacing-lg;
  }
  
  .empty-state {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: $spacing-xl * 2;
    
    .empty-icon {
      font-size: 80rpx;
      margin-bottom: $spacing-md;
    }
    
    .empty-text {
      font-size: $font-size-md;
      color: $text-second;
      margin-bottom: $spacing-sm;
    }
    
    .empty-hint {
      font-size: $font-size-sm;
      color: $text-placeholder;
    }
  }
  
  .loading-state {
    display: flex;
    flex-direction: column;
    align-items: center;
    padding: $spacing-xl;
    
    .loading-text {
      margin-top: $spacing-sm;
      font-size: $font-size-sm;
      color: $text-second;
    }
  }
  
  .load-more-hint,
  .no-more-hint {
    text-align: center;
    padding: $spacing-md;
    font-size: $font-size-xs;
    color: $text-placeholder;
  }
  
  .fab-wrapper {
    position: fixed;
    bottom: 120rpx;
    right: $spacing-lg;
    z-index: 99;
    
    .fab-btn {
      width: 112rpx;
      height: 112rpx;
      background: linear-gradient(135deg, $primary-orange 0%, $primary-orange-alt 100%);
      border-radius: $radius-circle;
      display: flex;
      align-items: center;
      justify-content: center;
      box-shadow: 0 8rpx 24rpx rgba($primary-orange, 0.4);
      
      &:active {
        transform: scale(0.95);
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
      background: $white;
      border-radius: $radius-lg;
      display: flex;
      flex-direction: column;
      
      .modal-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: $spacing-lg;
        border-bottom: 1rpx solid $border-color;
        
        .modal-title {
          font-size: $font-size-lg;
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
        padding: $spacing-lg;
        overflow: hidden;
        
        .generated-content {
          max-height: 60vh;
          
          .content-text {
            font-size: $font-size-md;
            color: $text-main;
            line-height: 1.8;
            white-space: pre-wrap;
          }
        }
      }
      
      .modal-footer {
        display: flex;
        gap: $spacing-md;
        padding: $spacing-lg;
        border-top: 1rpx solid $border-color;
        
        .modal-btn {
          flex: 1;
          padding: $spacing-md;
          text-align: center;
          border-radius: $radius-md;
          font-size: $font-size-md;
          
          &.secondary {
            background: $bg-light;
            color: $text-main;
          }
          
          &.primary {
            background: linear-gradient(135deg, $primary-orange 0%, $primary-orange-alt 100%);
            color: $white;
          }
        }
      }
    }
  }
  
  .bottom-safe-area {
    height: env(safe-area-inset-bottom);
  }
}
</style>

