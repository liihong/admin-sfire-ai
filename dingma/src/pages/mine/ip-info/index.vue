<template>
  <!-- 常驻 IP：独立页编辑（导航栏标题在 pages.json 配置为 ip信息） -->
  <view class="page-ip-info">
    <PersonaProfileEditor :default-name="defaultNickname" />
  </view>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useAuthStore } from '@/stores/auth'
import PersonaProfileEditor from '@/components/mine/PersonaProfileEditor.vue'

const authStore = useAuthStore()

/** 无档案时用微信昵称兜底填「姓名」 */
const defaultNickname = computed(() => authStore.userInfo?.nickname?.trim() || '')
</script>

<style scoped lang="scss">
@import '@/styles/_variables.scss';

.page-ip-info {
  min-height: 100vh;
  box-sizing: border-box;
  padding: 24rpx 32rpx 32rpx;
  padding-bottom: calc(24rpx + env(safe-area-inset-bottom));
  padding-bottom: calc(24rpx + constant(safe-area-inset-bottom));
  background: $bg-base;
  display: flex;
  flex-direction: column;

  /** 铺满剩余屏高，便于 scroll-view 获得可滚动高度 */
  :deep(.persona-editor) {
    flex: 1;
    min-height: 720rpx;
  }

  :deep(.persona-editor__body) {
    flex: 1;
    min-height: 0;
  }
}
</style>
