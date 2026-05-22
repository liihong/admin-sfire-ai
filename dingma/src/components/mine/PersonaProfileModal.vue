<template>
  <view v-if="visible" class="persona-modal">
    <view class="persona-modal__mask" @tap="close" />
    <view class="persona-modal__card" @tap.stop>
      <view class="persona-modal__head">
        <view class="persona-modal__title-row">
          <text class="persona-modal__gear">⚙</text>
          <text class="persona-modal__title">我的常驻 IP 专属信息档案（黄框）</text>
        </view>
        <view class="persona-modal__close" @tap="close">
          <text class="persona-modal__close-icon">×</text>
        </view>
      </view>

      <scroll-view scroll-y class="persona-modal__body" :show-scrollbar="false">
        <view class="field">
          <text class="field-label">A. 姓名</text>
          <view class="field-input-box">
            <input
              v-model="form.name"
              class="field-input"
              placeholder="例如：小辛妈妈"
              placeholder-class="persona-placeholder-input"
              :maxlength="20"
              :adjust-position="true"
            />
          </view>
        </view>

        <view class="field">
          <text class="field-label">B. 所在地区</text>
          <view class="field-input-box">
            <input
              v-model="form.ip_city"
              class="field-input"
              placeholder="例如：建业一号城邦 / 河南新乡"
              placeholder-class="persona-placeholder-input"
              :maxlength="50"
              :adjust-position="true"
            />
          </view>
        </view>

        <view class="field">
          <text class="field-label">C. 身份标签</text>
          <view class="field-input-box">
            <input
              v-model="form.ip_identityTag"
              class="field-input"
              placeholder="例如：宝妈，二胎妈妈，前HR"
              placeholder-class="persona-placeholder-input"
              :maxlength="100"
              :adjust-position="true"
            />
          </view>
        </view>

        <view class="field">
          <text class="field-label">D. 经历介绍</text>
          <view class="field-textarea-box">
            <textarea
              v-model="form.ip_experience"
              class="field-textarea"
              placeholder="请涵盖：过往职业、转折点、从业初衷、最大挑战..."
              placeholder-class="persona-placeholder-textarea"
              :maxlength="2000"
              :auto-height="false"
              :adjust-position="true"
            />
          </view>
        </view>

        <view class="field">
          <text class="field-label">E. 产品介绍</text>
          <view class="field-textarea-box">
            <textarea
              v-model="form.cl_mainProducts"
              class="field-textarea field-textarea--sm"
              placeholder="例如：芝士秋葵玉米拉丝馄饨和手炒藤椒米线"
              placeholder-class="persona-placeholder-textarea"
              :maxlength="500"
              :auto-height="false"
              :adjust-position="true"
            />
          </view>
        </view>
      </scroll-view>

      <view
        class="persona-modal__save"
        :class="{ 'persona-modal__save--disabled': !canSave || saving || loading }"
        @tap="handleSave"
      >
        <text class="persona-modal__save-icon">💾</text>
        <text class="persona-modal__save-text">保存锁定并同步全智能体</text>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { fetchProjects, createProject, updateProject, switchProject } from '@/api/project'
import { useProjectStore } from '@/stores/project'
import { modelToFormData, formDataToCreateRequest, formDataToUpdateRequest } from '@/utils/project'
import type { ProjectFormData } from '@/types/project'

const props = defineProps<{
  visible: boolean
  defaultName?: string
}>()

const emit = defineEmits<{
  'update:visible': [value: boolean]
  saved: []
}>()

const projectStore = useProjectStore()
const loading = ref(false)
const saving = ref(false)
const projectId = ref<string | null>(null)

const form = ref({
  name: '',
  ip_city: '',
  ip_identityTag: '',
  ip_experience: '',
  cl_mainProducts: ''
})

const canSave = computed(() => form.value.name.trim().length > 0)

function resetForm() {
  form.value = {
    name: '',
    ip_city: '',
    ip_identityTag: '',
    ip_experience: '',
    cl_mainProducts: ''
  }
  projectId.value = null
}

function applyFormData(data: ProjectFormData) {
  form.value = {
    name: data.name || data.ip_name || '',
    ip_city: data.ip_city || '',
    ip_identityTag: data.ip_identityTag || '',
    ip_experience: data.ip_experience || '',
    cl_mainProducts: data.cl_mainProducts || ''
  }
}

async function loadProfile() {
  loading.value = true
  try {
    const res = await fetchProjects()
    projectStore.setProjectList(res.projects, res.active_project_id)

    const active = projectStore.activeProject || res.projects[0]
    if (active) {
      projectId.value = String(active.id)
      applyFormData(modelToFormData(active))
      return
    }

    resetForm()
    if (props.defaultName?.trim()) {
      form.value.name = props.defaultName.trim()
    }
  } catch (e: unknown) {
    resetForm()
    if (props.defaultName?.trim()) {
      form.value.name = props.defaultName.trim()
    }
    const msg = e instanceof Error ? e.message : '加载人设信息失败'
    uni.showToast({ title: msg, icon: 'none' })
  } finally {
    loading.value = false
  }
}

watch(
  () => props.visible,
  (v) => {
    if (v) {
      loadProfile()
    } else {
      resetForm()
    }
  }
)

function close() {
  emit('update:visible', false)
}

function buildFormData(): ProjectFormData {
  const base = modelToFormData(projectStore.activeProject)
  const name = form.value.name.trim()
  return {
    ...base,
    name,
    ip_name: name,
    ip_city: form.value.ip_city.trim(),
    ip_identityTag: form.value.ip_identityTag.trim(),
    ip_experience: form.value.ip_experience.trim(),
    cl_mainProducts: form.value.cl_mainProducts.trim()
  }
}

async function handleSave() {
  if (!canSave.value || saving.value || loading.value) return

  saving.value = true
  try {
    const formData = buildFormData()
    let project = null

    if (projectId.value) {
      project = await updateProject(projectId.value, formDataToUpdateRequest(formData))
    } else {
      project = await createProject(formDataToCreateRequest(formData))
      await switchProject(project.id)
      projectId.value = String(project.id)
    }

    projectStore.upsertProject(project)
    projectStore.setActiveProjectLocal(project)
    projectStore.setNeedRefresh(true)

    uni.showToast({ title: '已保存并同步', icon: 'success' })
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

.persona-modal {
  position: fixed;
  inset: 0;
  z-index: $z-index-modal-backdrop;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 40rpx 32rpx;

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
    max-width: 660rpx;
    max-height: 86vh;
    display: flex;
    flex-direction: column;
    background: $white;
    border-radius: 32rpx;
    padding: 32rpx 28rpx 28rpx;
    box-shadow: 0 24rpx 64rpx rgba(0, 0, 0, 0.12);
  }

  &__head {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    margin-bottom: 24rpx;
    flex-shrink: 0;
  }

  &__title-row {
    display: flex;
    align-items: center;
    gap: 10rpx;
    flex: 1;
    padding-right: 12rpx;
  }

  &__gear {
    font-size: 30rpx;
    color: #9ca3af;
    flex-shrink: 0;
    line-height: 1;
  }

  &__title {
    font-size: 28rpx;
    font-weight: 600;
    color: #9a6b3f;
    line-height: 1.45;
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
    flex: 1;
    min-height: 0;
    max-height: 58vh;
    margin-bottom: 24rpx;
  }

  &__save {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 12rpx;
    padding: 24rpx;
    border-radius: 20rpx;
    background: linear-gradient(135deg, #a66b2e 0%, #8b5a24 100%);
    box-shadow: 0 8rpx 24rpx rgba(139, 90, 36, 0.35);
    flex-shrink: 0;

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
    font-size: 28rpx;
    font-weight: 600;
    color: $white;
  }
}

.field {
  margin-bottom: 22rpx;

  &:last-child {
    margin-bottom: 0;
  }

  &-label {
    display: block;
    font-size: 24rpx;
    color: #8b7355;
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
    min-height: 160rpx;
    padding: 0;
    margin: 0;
    font-size: 28rpx;
    line-height: 1.6;
    color: $text-main;
    background: transparent;
    box-sizing: border-box;

    &--sm {
      min-height: 120rpx;
    }
  }
}
</style>

<style lang="scss">
.persona-placeholder-input {
  color: #c9cdd4;
  font-size: 28rpx;
  line-height: 88rpx;
}

.persona-placeholder-textarea {
  color: #c9cdd4;
  font-size: 28rpx;
  line-height: 1.6;
}
</style>
