<template>
  <view class="ip-statement-card">
    <text class="statement-text">
      我是一个 
      <text class="statement-placeholder" :class="{ filled: adjective }">
        {{ adjective || '[形容词]' }}
      </text>
      的 
      <text class="statement-placeholder" :class="{ filled: role }">
        {{ role || '[角色定位]' }}
      </text>
      ，专注为 
      <text class="statement-placeholder" :class="{ filled: targetAudience }">
        {{ targetAudience || '[目标受众]' }}
      </text>
      解决 
      <text class="statement-placeholder" :class="{ filled: problem }">
        {{ problem || '[问题]' }}
      </text>
      。
    </text>
  </view>
</template>

<script setup lang="ts">
interface Props {
  adjective: string
  role: string
  targetAudience: string
  problem: string
}

defineProps<Props>()
</script>

<style lang="scss" scoped>
@import '@/styles/_variables.scss';

.ip-statement-card {
  background: linear-gradient(135deg, rgba($primary-orange, 0.05) 0%, rgba($primary-orange, 0.02) 100%);
  border-radius: $radius-md;
  padding: $spacing-lg;
  margin-bottom: $spacing-lg;
  border: 2rpx solid rgba($primary-orange, 0.1);
  
  .statement-text {
    font-size: $font-size-md;
    color: $text-main;
    line-height: 1.8;
    
    .statement-placeholder {
      color: $primary-orange;
      font-weight: 600;
      padding: 0 8rpx;
      
      &.filled {
        background: rgba($primary-orange, 0.1);
        border-radius: 4rpx;
      }
    }
  }
}
</style>

