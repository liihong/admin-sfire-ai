<template>
  <view class="quick-command-grid">
    <view v-for="entry in quickEntryList" :key="entry.id" class="command-card" @tap="handleClick(entry)">
      <view class="command-icon-wrapper">
        <SvgIcon :name="entry.icon_class" :size="40" />
      </view>
      <view class="command-content">
        <text class="command-title">{{ entry.title }}</text>
        <text class="command-desc">{{ entry.subtitle || '' }}</text>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import SvgIcon from '@/components/base/SvgIcon.vue'
import { type QuickEntry } from '@/api/quickEntry'
import { useQuickEntryStore } from '@/stores/quickEntry'

// ============== Props ==============
interface Props {
  entries?: QuickEntry[]
}

const props = withDefaults(defineProps<Props>(), {
  entries: () => []
})

// ============== Store ==============
const quickEntryStore = useQuickEntryStore()

// 使用传入的快捷入口列表数据
const quickEntryList = computed(() => props.entries || [])

const emit = defineEmits<{
  click: [route: string]
}>()

/**
 * 处理点击事件，根据 action_type 跳转到相应页面
 */
function handleClick(entry: QuickEntry) {
  let route = ''

  // 根据 action_type 构建路由
  if (entry.action_type === 'agent') {
    // 设置选中的快捷指令到 store（自动保存到 storage）
    quickEntryStore.setActiveQuickEntry(entry)
    // 跳转到 copywriting 页面，只传递 agentId（智能体信息由目标页面自行处理）
    route = `/pages/copywriting/index?agentId=${entry.action_value}`
  } else if (entry.action_type === 'skill') {
    // 跳转到 skill 页面（功能待实现）
    route = ''
  } else if (entry.action_type === 'prompt') {
    // 处理 prompt 类型（功能待实现）
    route = ''
  }

  if (route) {
    emit('click', route)
  }
}
</script>

<style lang="scss" scoped>
@import '@/styles/_variables.scss';
@import '@/styles/_mixins.scss';

.quick-command-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: $spacing-md;
  margin-bottom: $spacing-lg;

  .command-card {
    @include card-style;
    padding: $spacing-md;
    display: flex;
    align-items: center;
    gap: 20rpx;
    transition: all $transition-base;

    &:active {
      transform: scale(0.98);
      background: $bg-light;
    }

    .command-icon-wrapper {
      :deep(.agent-icon) {
        box-shadow: 0 2rpx 8rpx rgba(0, 0, 0, 0.15);
      }
    }

    .command-content {
      display: flex;
      flex-direction: column;
      gap: 6rpx;
      flex: 1;
      min-width: 0;

      .command-title {
        font-size: $font-size-md;
        font-weight: 600;
        color: $text-main;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
      }

      .command-desc {
        font-size: $font-size-xs;
        color: $text-second;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        max-width: 240rpx; // 设置固定最大宽度，超出显示省略号
      }
    }
  }
}
</style>
