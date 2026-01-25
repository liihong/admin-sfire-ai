<template>
  <view class="tool-library">
    <view
      v-for="item in tools"
      :key="item.key"
      class="tool-item"
      @tap="handleClick(item)"
    >
      <view class="tool-icon-wrapper">
        <SvgIcon :name="item.icon" :size="45" :color="item.color" />
      </view>
      <text class="tool-label">{{ item.label }}</text>
    </view>
  </view>
</template>

<script setup lang="ts">
import SvgIcon from '@/components/base/SvgIcon.vue'

// 工具项接口定义
interface ToolItem {
  key: string
  label: string
  icon: string
  color: string
  // 跳转类型：'miniProgram' 跳转其他小程序，'page' 跳转本小程序页面
  type: 'miniProgram' | 'page'
  // 跳转目标：小程序 appId 或页面路径
  target: string
  // 跳转其他小程序时的额外参数
  extraData?: Record<string, any>
  // 跳转其他小程序时的路径
  path?: string
}

interface Props {
  tools?: ToolItem[]
}

// 默认工具列表
const props = withDefaults(defineProps<Props>(), {
  tools: () => [
    {
      key: 'text-extract',
      label: '文案提取',
      icon: 'edit',
      color: '#3B82F6',
      type: 'page',
      target: '/pages/tools/text-extract/index'
    },
    {
      key: 'image-to-text',
      label: '图片转文字',
      icon: 'works',
      color: '#10B981',
      type: 'page',
      target: '/pages/tools/image-to-text/index'
    },
    {
      key: 'video-to-text',
      label: '视频转文字',
      icon: 'send',
      color: '#F59E0B',
      type: 'page',
      target: '/pages/tools/video-to-text/index'
    },
    {
      key: 'qr-code',
      label: '二维码生成',
      icon: 'qiehuan',
      color: '#EF4444',
      type: 'page',
      target: '/pages/tools/qr-code/index'
    },
    {
      key: 'timestamp',
      label: '时间戳转换',
      icon: 'tone',
      color: '#8B5CF6',
      type: 'page',
      target: '/pages/tools/timestamp/index'
    }
  ]
})

const emit = defineEmits<{
  click: [tool: ToolItem]
}>()

// 处理工具点击
function handleClick(tool: ToolItem) {
  emit('click', tool)
  
  if (tool.type === 'miniProgram') {
    // 跳转到其他小程序
    uni.navigateToMiniProgram({
      appId: tool.target,
      path: tool.path || '',
      extraData: tool.extraData || {},
      success: () => {
        console.log('跳转小程序成功')
      },
      fail: (err) => {
        console.error('跳转小程序失败:', err)
        uni.showToast({
          title: '跳转失败',
          icon: 'none'
        })
      }
    })
  } else if (tool.type === 'page') {
    // 跳转到本小程序页面
    if (tool.target) {
      uni.navigateTo({
        url: tool.target,
        fail: (err) => {
          console.error('页面跳转失败:', err)
          uni.showToast({
            title: '页面不存在',
            icon: 'none'
          })
        }
      })
    }
  }
}
</script>

<style lang="scss" scoped>
@import '@/styles/_variables.scss';

.tool-library {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: $spacing-sm;
  margin-bottom: $spacing-lg;
  
  .tool-item {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: $spacing-sm;
    transition: transform $transition-base;
    
    &:active {
      transform: scale(0.92);
    }
    
    .tool-icon-wrapper {
      border-radius: 20rpx;
      padding: 12rpx 24rpx;
      border: 1rpx solid #e5e7eb;
      box-shadow: 0 2rpx 8rpx rgba(0, 0, 0, 0.1);
      background: $white;
      
      :deep(.agent-icon) {
        box-shadow: 0 4rpx 12rpx rgba(0, 0, 0, 0.1);
      }
    }
    
    .tool-label {
      font-size: $font-size-sm;
      font-weight: 900;
      color: $text-main;
      text-align: center;
    }
  }
}
</style>

