<template>
  <BaseDrawer 
    :visible="visible" 
    :max-height="'60vh'"
    @update:visible="$emit('update:visible', $event)"
  >
    <template #header>
      <view class="inspiration-header">
        <view class="header-left">
          <view class="header-icon">💡</view>
          <text class="header-title">捕捉灵感</text>
        </view>
      </view>
    </template>
    
    <view class="inspiration-content">
      <!-- 输入框 -->
      <textarea
        class="inspiration-textarea"
        :value="modelValue"
        placeholder="此刻在想什么?..."
        placeholder-class="textarea-placeholder"
        :maxlength="500"
@input="handleInput"
      />
      
      <!-- 标签建议 -->
      <view class="tag-suggestions">
        <view
          v-for="tag in suggestedTags"
          :key="tag"
          class="tag-item"
          :class="{ active: selectedTags.includes(tag) }"
          @tap="handleTagClick(tag)"
        >
          <text class="tag-text">{{ tag }}</text>
        </view>
      </view>
    </view>
    
    <template #footer>
      <view class="inspiration-footer">
        <!-- <view class="voice-btn" @tap="$emit('mic-click')">
          <u-icon name="mic" color="#86909C" size="20"></u-icon>
          <text class="voice-text">语音</text>
        </view> -->
        <view 
          class="save-btn" 
          :class="{ disabled: !canSave }"
          @tap="handleSave"
        >
          <u-icon name="file-text" color="#FFFFFF" size="20"></u-icon>
          <text class="save-text">保存灵感</text>
        </view>
      </view>
    </template>
  </BaseDrawer>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import BaseDrawer from '@/components/common/BaseDrawer.vue'

interface Props {
  visible: boolean
  modelValue?: string
  suggestedTags?: string[]
}

const props = withDefaults(defineProps<Props>(), {
  visible: false,
  modelValue: '',
  suggestedTags: () => ['#视频脚本', '#文案想法', '#每日一记', '#工作']
})

const emit = defineEmits<{
  'update:visible': [value: boolean]
  'update:modelValue': [value: string]
  send: [value: string, tags: string[]]
  'mic-click': []
}>()

const selectedTags = ref<string[]>([])

const canSave = computed(() => {
  return props.modelValue.trim().length > 0
})

function handleInput(e: any) {
  emit('update:modelValue', e.detail.value)
}

function handleTagClick(tag: string) {
  const index = selectedTags.value.indexOf(tag)
  if (index > -1) {
    selectedTags.value.splice(index, 1)
  } else {
    selectedTags.value.push(tag)
  }
}

function handleSave() {
  if (canSave.value) {
    emit('send', props.modelValue, selectedTags.value)
    emit('update:visible', false)
    // 清空选中标签
    selectedTags.value = []
  }
}
</script>

<style lang="scss" scoped>
@import '@/styles/_variables.scss';

.inspiration-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: $spacing-sm $spacing-lg $spacing-md;
  
  .header-left {
    display: flex;
    align-items: center;
    gap: $spacing-sm;
    
    .header-icon {
      font-size: 36rpx;
    }
    
    .header-title {
      font-size: $font-size-lg;
      font-weight: 600;
      color: $text-main;
    }
  }
  
  .drawer-close {
    width: 56rpx;
    height: 56rpx;
    background: $bg-light;
    border-radius: $radius-circle;
    display: flex;
    align-items: center;
    justify-content: center;
    
    .close-icon {
      font-size: 40rpx;
      color: $text-second;
      line-height: 1;
    }
  }
}

.inspiration-content {
  
  .inspiration-textarea {
    width: 100%;
    min-height: 200rpx;
    max-height: 400rpx;
    font-size: $font-size-md;
    color: $text-main;
    line-height: 1.6;
    margin-bottom: $spacing-lg;
    background: transparent;
  }
  
  .textarea-placeholder {
    color: $text-placeholder;
  }
  
  .tag-suggestions {
    display: flex;
    flex-wrap: wrap;
    gap: $spacing-sm;
    
    .tag-item {
      padding: 12rpx 24rpx;
      background: $bg-light;
      border-radius: $radius-md;
      font-size: $font-size-sm;
      color: $text-second;
      transition: all $transition-base;
      
      &.active {
        background: rgba($primary-orange, 0.1);
        color: $primary-orange;
      }
      
      .tag-text {
        font-size: $font-size-sm;
      }
    }
  }
}

.inspiration-footer {
  display: flex;
  align-items: center;
  gap: $spacing-md;
  padding: $spacing-md $spacing-lg;
  
  .voice-btn {
    display: flex;
    align-items: center;
    gap: 8rpx;
    padding: 20rpx 32rpx;
    background: $bg-light;
    border-radius: $radius-md;
    
    .voice-text {
      font-size: $font-size-md;
      color: $text-second;
    }
  }
  
  .save-btn {
    flex: 1;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 8rpx;
    padding: 20rpx 32rpx;
    background: linear-gradient(135deg, $primary-orange 0%, $primary-orange-alt 100%);
    border-radius: $radius-md;
    box-shadow: 0 4rpx 12rpx rgba($primary-orange, 0.3);
    transition: all $transition-base;
    
    &.disabled {
      opacity: 0.5;
    }
    
    &:active:not(.disabled) {
      transform: scale(0.98);
    }
    
    .save-text {
      font-size: $font-size-md;
      font-weight: 600;
      color: $white;
    }
  }
}
</style>

