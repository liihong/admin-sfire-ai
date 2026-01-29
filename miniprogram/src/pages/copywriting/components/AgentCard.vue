<template>
  <view class="persona-card-container">
    <!-- IP 档案卡片 -->
    <view v-if="project" class="system-card">
    <view class="card-header">
      <view class="card-avatar" :style="{ background: project.avatar_color }">
        <text class="avatar-letter">{{ project.avatar_letter ?  project.name[0] : project.avatar_letter}}</text>
      </view>
      <view class="card-title-group">
        <text class="card-title">{{ project.name }}</text>
        <text class="card-subtitle">IP 档案 · AI 已就位</text>
      </view>
      <view class="card-status">
        <view class="status-pulse"></view>
        <text class="status-text">在线</text>
      </view>
    </view>
      <!-- <view class="card-body">
        <view class="info-row">
        <text class="info-label">
          <SvgIcon name="agent" size="20" color="#3B82F6" /> 当前智能体
        </text>
         <text class="info-value agent-value">{{ currentAgentName }}</text>

      </view> 
         <view class="info-row" v-if="project.industry">
        <text class="info-label">
          <SvgIcon name="industry" size="20" color="#666" /> 行业领域
        </text>
        <text class="info-value">{{ project.industry }}</text>
      </view>
      <view class="info-row" v-if="personaSettings.tone">
        <text class="info-label">
          <SvgIcon name="tone" size="20" color="#666" /> 风格标签
        </text>
        <text class="info-value">{{ formatStyleTags(personaSettings.tone) }}</text>
      </view>
      <view class="info-row" v-if="personaSettings.target_audience">
        <text class="info-label">
          <SvgIcon name="target_audience" size="20" color="#666" /> 目标受众
        </text>
        <text class="info-value">{{ personaSettings.target_audience }}</text>
      </view> 
     </view>-->





  </view>

  <!-- 无项目提示卡片 -->
  <view v-else class="empty-project-card">
    <view class="empty-icon">
      <SvgIcon name="works" size="80" color="#999" />
    </view>
    <text class="empty-title">尚未选择 IP 项目</text>
    <text class="empty-desc">请先创建或选择一个 IP 项目，以便 AI 更好地理解您的创作需求</text>
    <button class="create-btn" @tap="handleGoToProjectList">
      <text>选择项目</text>
    </button>
  </view>
  </view>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import SvgIcon from '@/components/base/SvgIcon.vue'
import { useAgentStore } from '@/stores/agent'

// ============== Store ==============
const agentStore = useAgentStore()

interface Project {
  id: string
  name: string
  avatar_color: string
  avatar_letter: string
  industry?: string
}

interface PersonaSettings {
  tone?: string
  target_audience?: string
}

interface Props {
  project: Project | null
  personaSettings: PersonaSettings
}

const props = defineProps<Props>()

// 从 store 获取当前智能体名称
const currentAgentName = computed(() => agentStore.activeAgent?.name || '未选择')

/**
 * 格式化风格标签
 */
function formatStyleTags(tone: string): string {
  if (!tone) return ''
  // 如果已经是数组格式的字符串，尝试解析
  try {
    const parsed = JSON.parse(tone)
    if (Array.isArray(parsed)) {
      return parsed.join(', ')
    }
  } catch {
    // 不是 JSON，直接返回
  }
  return tone
}

/**
 * 跳转到项目列表
 */
function handleGoToProjectList() {
  uni.navigateTo({ url: '/pages/project/index' })
}
</script>

<style lang="scss" scoped>
// ============== 变量定义 ==============
$primary-orange: #FF6B35;
$primary-orange-light: #FF8C5A;
$accent-blue: #4FACFE;
$accent-cyan: #00F2FE;
$bg-card: rgba(255, 255, 255, 0.95);
$text-primary: #1A1A2E;
$text-secondary: #666;
$text-muted: #999;

// ============== 容器 ==============
.persona-card-container {
  width: 100%;
  flex-shrink: 0;
}

// ============== IP 档案卡片 ==============
.system-card {
  background: $bg-card;
  border-radius: 28rpx;
  padding: 32rpx;
  margin: 24rpx;
  margin-bottom: 32rpx;
  border: 2rpx solid transparent;
  background-clip: padding-box;
  position: relative;
  box-shadow: 0 8rpx 32rpx rgba(79, 172, 254, 0.1);

  &::before {
    content: '';
    position: absolute;
    inset: -2rpx;
    border-radius: 30rpx;
    background: linear-gradient(135deg, $accent-blue, $accent-cyan, $primary-orange);
    z-index: -1;
    opacity: 0.6;
  }

  .card-header {
    display: flex;
    align-items: center;
    // padding-bottom: 20rpx;
      // border-bottom: 1rpx dashed rgba(0, 0, 0, 0.08);

    .card-avatar {
      width: 88rpx;
      height: 88rpx;
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
      box-shadow: 0 4rpx 16rpx rgba(0, 0, 0, 0.15);

      .avatar-letter {
        font-size: 40rpx;
        font-weight: 700;
        color: #fff;
      }
    }

    .card-title-group {
      flex: 1;
      margin-left: 20rpx;

      .card-title {
        font-size: 36rpx;
        font-weight: 700;
        color: $text-primary;
        display: block;
      }

      .card-subtitle {
        font-size: 24rpx;
        color: $text-muted;
        margin-top: 4rpx;
      }
    }

    .card-status {
      display: flex;
      align-items: center;
      gap: 8rpx;
      padding: 8rpx 16rpx;
      background: rgba(76, 175, 80, 0.1);
      border-radius: 20rpx;

      .status-pulse {
        width: 16rpx;
        height: 16rpx;
        border-radius: 50%;
        background: #4CAF50;
        animation: pulse 2s infinite;
      }

      .status-text {
        font-size: 22rpx;
        color: #4CAF50;
        font-weight: 500;
      }
    }
  }

  .card-body {
    .info-row {
      display: flex;
      align-items: center;
      padding: 10rpx 0;

      .info-label {
        font-size: 26rpx;
        color: $text-secondary;
        width: 180rpx;
        display: flex;
        align-items: center;
        gap: 8rpx;
      }

      .info-value {
        flex: 1;
        font-size: 26rpx;
        color: $text-primary;
        font-weight: 500;

        &.agent-value {
          color: $primary-orange;
        }
      }
    }
  }

  .card-footer {
    margin-top: 20rpx;
    padding-top: 20rpx;
    border-top: 1rpx dashed rgba(0, 0, 0, 0.08);

    .footer-hint {
      font-size: 24rpx;
      color: $text-muted;
      text-align: center;
      display: block;
    }
  }
}

@keyframes pulse {
  0%, 100% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.6; transform: scale(0.9); }
}

// ============== 空项目卡片 ==============
.empty-project-card {
  background: $bg-card;
  border-radius: 28rpx;
  padding: 60rpx 40rpx;
  margin: 24rpx;
  margin-bottom: 32rpx;
  text-align: center;
  box-shadow: 0 8rpx 32rpx rgba(0, 0, 0, 0.06);

  .empty-icon {
    display: flex;
    align-items: center;
    justify-content: center;
    margin-bottom: 24rpx;
  }

  .empty-title {
    font-size: 32rpx;
    font-weight: 600;
    color: $text-primary;
    display: block;
    margin-bottom: 16rpx;
  }

  .empty-desc {
    font-size: 26rpx;
    color: $text-muted;
    display: block;
    margin-bottom: 32rpx;
    line-height: 1.6;
  }

  .create-btn {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    padding: 20rpx 48rpx;
    background: linear-gradient(135deg, $primary-orange, $primary-orange-light);
    border-radius: 40rpx;
    border: none;
    color: #fff;
    font-size: 28rpx;
    font-weight: 500;
    box-shadow: 0 8rpx 24rpx rgba(255, 107, 53, 0.3);

    &::after {
      border: none;
    }
  }
}
</style>

