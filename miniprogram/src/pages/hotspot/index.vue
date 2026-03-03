<template>
  <view class="hotspot-page">
    <!-- 顶部导航栏 -->
    <view class="nav-header">
      <SafeAreaTop />
      <view class="nav-content">
        <view class="nav-left" @tap="goBack">
          <text class="back-icon">‹</text>
        </view>
        <view class="nav-center">
         <view class="nav-title">抖音热点榜单</view>
          <view class="update-time" v-if="updateTime">{{ updateTime }}</view>
        </view>
      </view>
    </view>
    
    <!-- 列表区域 -->
    <scroll-view
      class="list-container"
      scroll-y
      :refresher-enabled="true"
      :refresher-triggered="refreshing"
      @refresherrefresh="handleRefresh"
    >
      <!-- 热点列表 -->
      <view v-if="hotspotList.length > 0" class="hotspot-list">
        <view
          v-for="item in hotspotList"
          :key="item.rank"
          class="hotspot-item"
        >
          <view class="hotspot-content">
            <view class="hotspot-rank">
              <text class="rank-number">{{ item.rank }}</text>
            </view>
            <view class="hotspot-info">
              <text class="hotspot-title">{{ item.title }}</text>
              <view class="hotspot-meta">
                <text v-if="item.hot_value" class="hot-value">
                  🔥 {{ formatHotValue(item.hot_value) }}
                </text>
                <text v-if="item.label" class="hotspot-label">{{ item.label }}</text>
              </view>
            </view>
          </view>
          <view class="hotspot-action">
            <view class="action-btn" @tap="handleUseHotspot(item)">
              <text class="btn-text">蹭热点</text>
            </view>
          </view>
        </view>
      </view>
      
      <!-- 空状态 -->
      <view v-else-if="!loading" class="empty-state">
        <view class="empty-icon">📊</view>
        <text class="empty-text">暂无热点数据</text>
        <text class="empty-hint">下拉刷新试试</text>
      </view>
      
      <!-- 加载中 -->
      <view v-if="loading" class="loading-state">
        <u-loading-icon mode="spinner" color="#3B82F6"></u-loading-icon>
        <text class="loading-text">加载中...</text>
      </view>
      
      <!-- 底部安全区 -->
      <view class="bottom-safe-area"></view>
    </scroll-view>
  </view>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { getHotspotList, type HotspotItem } from '@/api/hotspot'
import { getQuickEntries, type QuickEntry } from '@/api/quickEntry'
import { useProjectStore } from '@/stores/project'
import { useAuthStore } from '@/stores/auth'
import { useAgentStore } from '@/stores/agent'
import SafeAreaTop from '@/components/common/SafeAreaTop.vue'

// Store
const projectStore = useProjectStore()
const authStore = useAuthStore()
const agentStore = useAgentStore()

// 状态
const hotspotList = ref<HotspotItem[]>([])
const loading = ref(false)
const refreshing = ref(false)
const updateTime = ref('')
const hotspotAgentId = ref<string | null>(null) // 热点功能对应的智能体ID

/**
 * 加载热点功能配置（获取智能体ID）
 */
async function loadHotspotConfig() {
  try {
    const response = await getQuickEntries('category')
    
    if (response.code === 200 && response.data?.entries) {
      // 查找 unique_key 为 'hotspot' 的条目
      const hotspotEntry = response.data.entries.find(
        (entry: QuickEntry) => entry.unique_key === 'hotspot'
      )
      
      if (hotspotEntry && hotspotEntry.action_value) {
        hotspotAgentId.value = hotspotEntry.action_value
      }
    }
  } catch (error) {
    console.error('加载热点配置失败:', error)
  }
}

// 初始化
onMounted(() => {
  loadHotspotList()
  loadHotspotConfig()
})

/**
 * 加载热点榜单
 */
async function loadHotspotList() {
  if (loading.value) return
  
  loading.value = true
  
  try {
    const response = await getHotspotList('hot')
    
    if (response.code === 200 && response.data?.list) {
      hotspotList.value = response.data.list
      updateTime.value = response.data.update_time || ''
    } else {
      uni.showToast({
        title: response.msg || '加载失败',
        icon: 'none',
      })
    }
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

/**
 * 下拉刷新
 */
function handleRefresh() {
  refreshing.value = true
  loadHotspotList()
}

/**
 * 格式化热度值
 */
function formatHotValue(value: number): string {
  if (value >= 10000) {
    return `${(value / 10000).toFixed(1)}万`
  }
  return String(value)
}

/**
 * 处理蹭热点
 */
async function handleUseHotspot(item: HotspotItem) {
  // 检查登录状态
  const loggedIn = await authStore.requireLogin()
  if (!loggedIn) return
  
  // 检查是否有激活的IP项目
  if (!projectStore.activeProject) {
    uni.showModal({
      title: '提示',
      content: '请先创建或激活一个IP项目',
      showCancel: false,
      success: () => {
        uni.switchTab({
          url: '/pages/project/index'
        })
      }
    })
    return
  }
  
  // 使用接口返回的 action_value 字段作为智能体ID
  if (!hotspotAgentId.value) {
    uni.showToast({
      title: '智能体配置未找到',
      icon: 'none'
    })
    return
  }
  
  // 自动生成快捷指令文案
  const ipName = projectStore.activeProject?.name || '我的IP'
  const quickCommand = `请根据热点"${item.title}"，结合我的IP信息（${ipName}），创作一条30秒的抖音口播文案。要求：1. 开头吸引眼球；2. 结合热点和IP特色；3. 结尾有行动号召。`
  
  // 跳转到AI对话页面
  agentStore.setActiveAgent({
    id: String(hotspotAgentId.value),
    name: '蹭热点',
    label: '蹭热点',
    icon: '',
    description: ''
  })
  uni.navigateTo({
    url: `/pages/copywriting/index?agentId=${hotspotAgentId.value}&content=${encodeURIComponent(quickCommand)}`,
    fail: (err) => {
      console.error('页面跳转失败:', err)
      uni.showToast({
        title: '页面跳转失败',
        icon: 'none'
      })
    }
  })
}

/**
 * 返回
 */
function goBack() {
  uni.navigateBack({
    fail: () => {
      uni.switchTab({ url: '/pages/index/index' })
    },
  })
}
</script>

<style lang="scss" scoped>
@import '@/styles/_variables.scss';

.hotspot-page {
  min-height: 100vh;
  background: $bg-color;
  
  .nav-header {
    background: $white;
    position: sticky;
    top: 0;
    z-index: 100;
    
    .nav-content {
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: $spacing-md $spacing-lg;
      
      .nav-left {
        width: 60rpx;
        
        .back-icon {
          font-size: 48rpx;
          color: $text-main;
          line-height: 1;
        }
      }
      
      .nav-center {
        flex: 1;
        text-align: center;
        
        .nav-title {
          font-size: $font-size-lg;
          font-weight: 600;
          color: $text-main;
        }
      }
      
      
    .update-time {
        font-size: $font-size-xs;
        color: $text-placeholder;
        }
    }
  }
  
  .list-container {
    height: calc(100vh - 200rpx);
  }
  
  .hotspot-list {
    padding: $spacing-md $spacing-lg;
  }
  
  .hotspot-item {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: $spacing-md;
    margin-bottom: $spacing-md;
    background: $white;
    border-radius: $radius-lg;
    box-shadow: 0 2rpx 8rpx rgba(0, 0, 0, 0.05);
    
    .hotspot-content {
      display: flex;
      align-items: flex-start;
      gap: $spacing-md;
      flex: 1;
      min-width: 0;
      
      .hotspot-rank {
        flex-shrink: 0;
        width: 60rpx;
        height: 60rpx;
        display: flex;
        align-items: center;
        justify-content: center;
        background: linear-gradient(135deg, $primary-orange 0%, $primary-orange-alt 100%);
        border-radius: $radius-md;
        
        .rank-number {
          font-size: $font-size-lg;
          font-weight: 700;
          color: $white;
        }
      }
      
      .hotspot-info {
        flex: 1;
        min-width: 0;
        display: flex;
        flex-direction: column;
        gap: $spacing-xs;
        
        .hotspot-title {
          font-size: $font-size-md;
          font-weight: 600;
          color: $text-main;
          line-height: 1.5;
          overflow: hidden;
          text-overflow: ellipsis;
          display: -webkit-box;
          -webkit-line-clamp: 2;
          -webkit-box-orient: vertical;
        }
        
        .hotspot-meta {
          display: flex;
          align-items: center;
          gap: $spacing-sm;
          
          .hot-value {
            font-size: $font-size-sm;
            color: $primary-orange;
            font-weight: 600;
          }
          
          .hotspot-label {
            font-size: $font-size-xs;
            color: $text-second;
            padding: 2rpx 8rpx;
            background: $bg-light;
            border-radius: $radius-sm;
          }
        }
      }
    }
    
    .hotspot-action {
      flex-shrink: 0;
      margin-left: $spacing-md;
      
      .action-btn {
        padding: $spacing-sm $spacing-md;
        background: linear-gradient(135deg, $primary-orange 0%, $primary-orange-alt 100%);
        border-radius: $radius-md;
        box-shadow: 0 2rpx 8rpx rgba($primary-orange, 0.3);
        
        .btn-text {
          font-size: $font-size-sm;
          color: $white;
          font-weight: 600;
        }
        
        &:active {
          transform: scale(0.95);
          opacity: 0.8;
        }
      }
    }
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
  
  .bottom-safe-area {
    height: env(safe-area-inset-bottom);
  }
}
</style>

