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
        <view class="field-textarea-box">
          <textarea
            v-model="content"
            class="field-textarea"
            placeholder="此刻在想什么?..."
            placeholder-class="field-placeholder-textarea"
            :maxlength="500"
            :auto-height="false"
            :adjust-position="true"
          />
        </view>
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

const suggestedTags = ['#视频脚本', '#文案想法', '#每日一记', '#工作']

const props = defineProps<{
  visible: boolean
}>()

const emit = defineEmits<{
  'update:visible': [value: boolean]
  saved: []
}>()

const content = ref('')
const selectedTags = ref<string[]>([])
const saving = ref(false)

const canSave = computed(() => content.value.trim().length > 0)

watch(
  () => props.visible,
  (v) => {
    if (!v) {
      content.value = ''
      selectedTags.value = []
    }
  }
)

function close() {
  emit('update:visible', false)
}

function handleTagClick(tag: string) {
  const index = selectedTags.value.indexOf(tag)
  if (index > -1) {
    selectedTags.value.splice(index, 1)
  } else {
    selectedTags.value.push(tag)
  }
}

async function handleSave() {
  if (!canSave.value || saving.value) return
  saving.value = true
  try {
    const projectStore = useProjectStore()
    const projectId = projectStore.activeProject?.id
      ? Number(projectStore.activeProject.id)
      : undefined
    await createInspiration({
      content: content.value.trim(),
      tags: [...selectedTags.value],
      project_id: projectId
    })
    uni.showToast({ title: '已收录到灵感夹', icon: 'success' })
    content.value = ''
    selectedTags.value = []
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

.field-textarea-box {
  padding: 20rpx 24rpx;
  background: #fdfbf7;
  border-radius: 16rpx;
  box-sizing: border-box;
  margin-bottom: 24rpx;
}

.field-textarea {
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

.tag-suggestions {
  display: flex;
  flex-wrap: wrap;
  gap: 16rpx;

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
</style>

<!-- placeholder-class 在微信小程序需非 scoped -->
<style lang="scss">
.field-placeholder-textarea {
  color: #c9cdd4;
  font-size: 28rpx;
  line-height: 1.6;
}
</style>
