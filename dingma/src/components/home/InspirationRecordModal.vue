<template>
  <view v-if="visible" class="inspire-modal">
    <view class="inspire-modal__mask" @tap="close" />
    <view class="inspire-modal__card" @tap.stop>
      <view class="inspire-modal__head">
        <view class="inspire-modal__title-row">
          <text class="inspire-modal__bulb">💡</text>
          <text class="inspire-modal__title">随时记录此刻灵感脑洞</text>
        </view>
        <view class="inspire-modal__close" @tap="close">
          <text class="inspire-modal__close-icon">×</text>
        </view>
      </view>

      <view class="inspire-modal__body">
        <view class="field">
          <text class="field-label">灵感主题（方便查找）</text>
          <view class="field-input-box">
            <input
              v-model="theme"
              class="field-input"
              placeholder="例如：香菇大肉包活动想法..."
              placeholder-class="field-placeholder-input"
              :maxlength="80"
              :adjust-position="true"
            />
          </view>
        </view>
        <view class="field">
          <text class="field-label">灵感文案/爆点细节</text>
          <view class="field-textarea-box">
            <textarea
              v-model="detail"
              class="field-textarea"
              placeholder="写下你此时脑子里闪现的新点子、好词好句、或者是想向AI咨询的灵感草稿..."
              placeholder-class="field-placeholder-textarea"
              :maxlength="2000"
              :auto-height="false"
              :adjust-position="true"
            />
          </view>
        </view>
      </view>

      <view
        class="inspire-modal__save"
        :class="{ 'inspire-modal__save--disabled': !canSave || saving }"
        @tap="handleSave"
      >
        <text class="inspire-modal__save-icon">💾</text>
        <text class="inspire-modal__save-text">保存并收录到灵感夹</text>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { createInspiration } from '@/api/inspiration'
import { useProjectStore } from '@/stores/project'

const props = defineProps<{
  visible: boolean
}>()

const emit = defineEmits<{
  'update:visible': [value: boolean]
  saved: []
}>()

const theme = ref('')
const detail = ref('')
const saving = ref(false)

const canSave = computed(() => theme.value.trim().length > 0 || detail.value.trim().length > 0)

watch(
  () => props.visible,
  (v) => {
    if (!v) {
      theme.value = ''
      detail.value = ''
    }
  }
)

function close() {
  emit('update:visible', false)
}

function buildContent(): string {
  const t = theme.value.trim()
  const d = detail.value.trim()
  if (t && d) return `【${t}】\n${d}`
  return t || d
}

async function handleSave() {
  if (!canSave.value || saving.value) return
  saving.value = true
  try {
    const projectStore = useProjectStore()
    const projectId = projectStore.activeProject?.id
      ? Number(projectStore.activeProject.id)
      : undefined
    const t = theme.value.trim()
    await createInspiration({
      content: buildContent(),
      tags: t ? [t] : [],
      project_id: projectId
    })
    uni.showToast({ title: '已收录到灵感夹', icon: 'success' })
    theme.value = ''
    detail.value = ''
    emit('saved')
    close()
  } catch (e: unknown) {
    const msg = e instanceof Error ? e.message : '保存失败'
    uni.showToast({ title: msg, icon: 'none' })
  } finally {
    saving.value = false
  }
}
</script>

<style lang="scss" scoped>
@import '@/styles/_variables.scss';

.inspire-modal {
  position: fixed;
  inset: 0;
  z-index: $z-index-modal-backdrop;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 48rpx 40rpx;

  &__mask {
    position: absolute;
    inset: 0;
    background: rgba(0, 0, 0, 0.45);
    backdrop-filter: blur(6px);
  }

  &__card {
    position: relative;
    z-index: 1;
    width: 100%;
    max-width: 640rpx;
    background: $white;
    border-radius: 32rpx;
    padding: 36rpx 32rpx 32rpx;
    box-shadow: 0 24rpx 64rpx rgba(0, 0, 0, 0.12);
  }

  &__head {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    margin-bottom: 28rpx;
  }

  &__title-row {
    display: flex;
    align-items: center;
    gap: 12rpx;
    flex: 1;
    padding-right: 16rpx;
  }

  &__bulb {
    font-size: 32rpx;
    flex-shrink: 0;
  }

  &__title {
    font-size: 30rpx;
    font-weight: 600;
    color: $primary-orange;
    line-height: 1.4;
  }

  &__close {
    width: 52rpx;
    height: 52rpx;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
  }

  &__close-icon {
    font-size: 44rpx;
    color: #9ca3af;
    line-height: 1;
  }

  &__body {
    margin-bottom: 28rpx;
  }

  &__save {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 12rpx;
    padding: 24rpx;
    border-radius: 20rpx;
    background: linear-gradient(135deg, $primary-orange 0%, $primary-orange-alt 100%);
    box-shadow: 0 8rpx 24rpx rgba($primary-orange, 0.35);

    &--disabled {
      opacity: 0.5;
    }

    &:active:not(&--disabled) {
      transform: scale(0.98);
    }
  }

  &__save-icon {
    font-size: 32rpx;
  }

  &__save-text {
    font-size: 30rpx;
    font-weight: 600;
    color: $white;
  }
}

.field {
  margin-bottom: 24rpx;

  &:last-child {
    margin-bottom: 0;
  }

  &-label {
    display: block;
    font-size: 24rpx;
    color: $text-second;
    margin-bottom: 12rpx;
  }

  &-input-box {
    display: flex;
    align-items: center;
    min-height: 88rpx;
    padding: 0 24rpx;
    background: #fdfbf7;
    border-radius: 16rpx;
    box-sizing: border-box;
  }

  &-input {
    flex: 1;
    width: 100%;
    height: 88rpx;
    min-height: 88rpx;
    line-height: 88rpx;
    padding: 0;
    margin: 0;
    font-size: 28rpx;
    color: $text-main;
    background: transparent;
    box-sizing: border-box;
  }

  &-textarea-box {
    padding: 20rpx 24rpx;
    background: #fdfbf7;
    border-radius: 16rpx;
    box-sizing: border-box;
  }

  &-textarea {
    display: block;
    width: 100%;
    min-height: 200rpx;
    padding: 0;
    margin: 0;
    font-size: 28rpx;
    line-height: 1.6;
    color: $text-main;
    background: transparent;
    box-sizing: border-box;
  }
}
</style>

<!-- placeholder-class 在微信小程序需非 scoped -->
<style lang="scss">
.field-placeholder-input {
  color: #c9cdd4;
  font-size: 28rpx;
  line-height: 88rpx;
}

.field-placeholder-textarea {
  color: #c9cdd4;
  font-size: 28rpx;
  line-height: 1.6;
}
</style>
