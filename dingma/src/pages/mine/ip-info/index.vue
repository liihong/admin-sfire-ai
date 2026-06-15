<template>
  <!-- 常驻 IP：独立页编辑（导航栏标题在 pages.json 配置为 ip信息） -->
  <view class="page-ip-info">
    <PersonaProfileEditor
      dense-layout
      :default-name="defaultNickname"
      @saved="handleSaved"
    />
  </view>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useAuthStore } from '@/stores/auth'
import PersonaProfileEditor from '@/components/mine/PersonaProfileEditor.vue'

const authStore = useAuthStore()

/** 无档案时用微信昵称兜底填「姓名」 */
const defaultNickname = computed(() => authStore.userInfo?.nickname?.trim() || '')

/** 保存成功后关闭当前页，回到「我的」 */
function handleSaved() {
  uni.navigateBack()
}
</script>

<style scoped lang="scss">
@import '@/styles/_variables.scss';

.page-ip-info {
  height: 100vh;
  box-sizing: border-box;
  padding: 16rpx 32rpx;
  /** 底部与 Home 指示条留白 */
  padding-bottom: calc(24rpx + constant(safe-area-inset-bottom));
  padding-bottom: calc(24rpx + env(safe-area-inset-bottom));
  /** 燕麦灰底，与 PersonaProfileEditor 白卡主体形成层次 */
  background: $terracotta-bg;
  display: flex;
  flex-direction: column;
  overflow: hidden;

  :deep(.persona-editor) {
    flex: 1;
    min-height: 0;
  }

  :deep(.persona-editor__body) {
    flex: 1;
    min-height: 0;
  }
}
</style>
