<template>
  <view class="input-section">
    <view class="input-card">
      <input
        class="inspiration-input"
        :value="modelValue"
        placeholder="记录此刻灵感瞬间..."
        placeholder-class="input-placeholder"
        @input="handleInput"
      />
      <view class="input-actions">
        <view class="action-icon mic-icon" @tap="$emit('mic-click')">
         <u-icon name="mic" color="#6C757D" size="20"></u-icon>
        </view>
        <view class="action-icon send-btn" @tap="handleSend">
         <u-icon name="arrow-right" color="#FFFFFF" size="20"></u-icon>
        </view>
      </view>
    </view>
    <text class="input-hint">{{ hint }}</text>
  </view>
</template>

<script setup lang="ts">
interface Props {
  modelValue?: string
  hint?: string
}

const props = withDefaults(defineProps<Props>(), {
  modelValue: '',
  hint: '每一个灵感瞬间都将成为你的优秀选题'
})

const emit = defineEmits<{
  'update:modelValue': [value: string]
  send: [value: string]
  'mic-click': []
}>()

function handleInput(e: any) {
  emit('update:modelValue', e.detail.value)
}

function handleSend() {
  if (props.modelValue.trim()) {
    emit('send', props.modelValue)
  }
}
</script>

<style lang="scss" scoped>
@import '@/styles/_variables.scss';

.input-section {
  margin-bottom: $spacing-lg;
  
  .input-card {
    display: flex;
    align-items: center;
    justify-content: space-between;
    background: $bg-light;
    border-radius: $radius-xl;
    padding: 12rpx 12rpx 12rpx $spacing-lg;
    margin-bottom: $spacing-sm;
    transition: all $transition-base;
    border: 1rpx solid rgba(0, 0, 0, 0.02);
    box-shadow: $card-shadow;
    
    &:focus-within {
      background: $white;
      border-color: rgba($primary-orange, 0.2);
    }
    
    .inspiration-input {
      flex: 1;
      font-size: $font-size-md;
      color: $text-main;
      height: 64rpx;
    }
    
    .input-placeholder {
      color: $text-placeholder;
    }
    
    .input-actions {
      display: flex;
      gap: $spacing-sm;
      
      .action-icon {
        width: 52rpx;
          height: 52rpx;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        background: transparent;
        transition: all $transition-base;
        
        &.mic-icon {
          &:active {
            background: rgba(0, 0, 0, 0.05);
          }
        }
        
        &.send-btn {
          background: linear-gradient(135deg, $primary-orange 0%, $primary-orange-alt 100%);
          box-shadow: 0 4rpx 12rpx rgba($primary-orange, 0.3);
          
          &:active {
            transform: scale(0.92);
            box-shadow: 0 2rpx 8rpx rgba($primary-orange, 0.3);
          }
        }
      }
    }
  }
  
  .input-hint {
    font-size: $font-size-xs;
    color: $text-second;
    display: block;
    padding-left: 8rpx;
  }
}
</style>
