<template>
  <view class="persona-card" @tap="$emit('click')">
    <view class="persona-card-content">
      <view class="persona-left">
       <!-- 项目头像 -->
        <view class="persona-avatar" :style="{ background: avatarColor }">
          <text class="avatar-letter">{{ avatarLetter }}</text>
        </view>
        <view class="persona-info">
         <text class="project-label">当前IP档案</text>
          <!-- <text class="project-name">{{ displayProjectName }}</text> -->
          <view class="tags-wrapper">
            <view class="tag-item tag-industry">
              <SvgIcon name="target_audience" :size="24" />
              <text class="tag-text">{{ industry }}</text>
            </view>
           <view class="tag-item tag-tone">
              <SvgIcon name="tone" :size="24" />
              <text class="tag-text">{{ displayTone }}</text>
           </view>
         </view>
        </view>
      </view>
      <view class="persona-edit-btn">
        <view class="edit-icon-wrapper">
          <u-icon name="setting" color="#6C757D" size="28"></u-icon>
        </view>
        <text class="edit-label">编辑人设</text>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { DEFAULT_PERSONA_SETTINGS, DEFAULT_INDUSTRY } from '@/stores/project'
import type { Project } from '@/api/project'
import SvgIcon from '@/components/base/SvgIcon.vue'

interface Props {
  project?: Project | null
  projectName?: string
  tone?: string
}

const props = withDefaults(defineProps<Props>(), {
  project: null,
  projectName: '',
  tone: DEFAULT_PERSONA_SETTINGS.tone
})

// 从 project 对象中读取 industry，如果没有则使用默认值
const industry = computed(() => {
  return props.project?.industry || DEFAULT_INDUSTRY
})

// 从 project 对象中读取 projectName，如果没有则使用传入的 projectName prop
const displayProjectName = computed(() => {
  return props.project?.name || props.projectName || '选择人设'
})

// 从 project 对象中读取 tone，如果没有则使用传入的 tone prop
const displayTone = computed(() => {
  return props.project?.persona_settings?.tone || props.tone || DEFAULT_PERSONA_SETTINGS.tone
})

// 从 project 对象中读取 avatar_letter，如果没有则使用项目名称首字母
const avatarLetter = computed(() => {
  if (props.project?.avatar_letter) {
    return props.project.avatar_letter
  }
  // 如果没有 avatar_letter，使用项目名称的首字母
  const name = props.project?.name || props.projectName
  return name ? name[0].toUpperCase() : 'P'
})

// 从 project 对象中读取 avatar_color，如果没有则使用默认颜色
const avatarColor = computed(() => {
  return props.project?.avatar_color || '#3B82F6'
})

defineEmits<{
  click: []
}>()
</script>

<style lang="scss" scoped>
@import '@/styles/_variables.scss';

.persona-card {
  background-color: rgb(255 247 237 / 0.5);
  border-radius: $radius-lg;
  border-color: rgb(255 237 213 / 0.5);
  padding: $spacing-lg;
  margin-bottom: $spacing-lg;
  box-shadow: 0 4rpx 24rpx rgba(59, 130, 246, 0.1);
  transition: all $transition-base;
  position: relative;
  overflow: hidden;

  &:active {
    transform: scale(0.98);
    box-shadow: 0 2rpx 12rpx rgba(59, 130, 246, 0.15);
  }

  .persona-card-content {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    gap: $spacing-md;
    position: relative;
    z-index: 2;
  }

  .persona-left {
    flex: 1;
    min-width: 0;
    display: flex;
    align-items: flex-start;
    gap: $spacing-md;

    .persona-avatar {
      width: 96rpx;
      height: 96rpx;
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
      flex-shrink: 0;
      box-shadow: 0 4rpx 16rpx rgba(0, 0, 0, 0.15);

      .avatar-letter {
        font-size: 40rpx;
        font-weight: 700;
        color: #fff;
      }
    }

    .persona-info {
      display: flex;
      flex-direction: column;
      gap: $spacing-sm;
      flex: 1;
      min-width: 0;

      .project-label {
        font-size: $font-size-sm;
        color: #64748B;
        font-weight: 400;
        line-height: 1.2;
        margin-bottom: 8rpx;
      }

      .project-name {
        font-size: 40rpx;
        font-weight: 700;
        color: #1E40AF;
        line-height: 1.2;
        letter-spacing: -0.5rpx;
        margin-bottom: 16rpx;
      }

      .tags-wrapper {
        display: flex;
        flex-wrap: wrap;
        gap: 12rpx;

        .tag-item {
          display: flex;
          align-items: center;
          gap: 6rpx;
          padding: 8rpx 16rpx;
          background: rgba(255, 255, 255, 0.7);
          border-radius: 20rpx;

          &.tag-industry {
            :deep(.iconfont) {
              color: $color-error;
            }
          }

          &.tag-tone {
            :deep(.iconfont) {
              color: $color-info;
            }
          }

          .tag-text {
            font-size: 22rpx;
            color: #475569;
            line-height: 1.2;
          }
        }
      }
    }
  }

  .persona-edit-btn {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 8rpx;
    flex-shrink: 0;

    .edit-icon-wrapper {
      width: 96rpx;
      height: 96rpx;
      background: $white;
      border-radius: $radius-md;
      display: flex;
      align-items: center;
      justify-content: center;
      box-shadow: $shadow-sm;
      border: 1rpx solid $border-light;
      transition: all $transition-base;

      &:active {
        transform: scale(0.95);
        box-shadow: $shadow-md;
      }
    }

    .edit-label {
      font-size: 20rpx;
      color: #64748B;
      line-height: 1.2;
    }
  }
}
</style>
