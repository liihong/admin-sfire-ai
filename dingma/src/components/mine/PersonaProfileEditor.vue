<template>
  <view class="persona-editor" :class="{ 'persona-editor--compact': compactLayout }">
    <scroll-view scroll-y class="persona-editor__body" :show-scrollbar="false">
      <view class="persona-editor__surface" :class="{ 'persona-editor__surface--raised': !compactLayout }">
        <view class="field">
          <text class="field-label">姓名</text>
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
          <text class="field-label">所在地区</text>
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
          <text class="field-label">身份标签</text>
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
          <text class="field-label">经历介绍</text>
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
          <text class="field-label">产品介绍</text>
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
      </view>
      <view class="persona-editor__body-pad-bottom" aria-hidden="true" />
    </scroll-view>

    <view
      class="persona-editor__save"
      :class="{ 'persona-editor__save--disabled': !canSave || saving || loading }"
      @tap="handleSave"
    >
      <text class="persona-editor__save-icon">💾</text>
      <text class="persona-editor__save-text">保存锁定并同步全智能体</text>
    </view>
  </view>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { fetchProjects, createProject, updateProject, switchProject } from '@/api/project'
import { useProjectStore } from '@/stores/project'
import { modelToFormData, formDataToCreateRequest, formDataToUpdateRequest } from '@/utils/project'
import type { ProjectFormData } from '@/types/project'

const props = withDefaults(
  defineProps<{
    /** 昵称兜底（创建项目且无档案时填入姓名框） */
    defaultName?: string
    /** 弹窗内为 true：不套外层白卡片，避免与弹窗底色重复嵌套 */
    compactLayout?: boolean
  }>(),
  { compactLayout: false }
)

const emit = defineEmits<{
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
  () => props.defaultName,
  (name) => {
    if (!form.value.name.trim() && name?.trim()) {
      form.value.name = name.trim()
    }
  }
)

defineExpose({
  loadProfile,
  resetForm
})

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
  } catch (e: unknown) {
    const msg = e instanceof Error ? e.message : '保存失败'
    uni.showToast({ title: msg, icon: 'none' })
  } finally {
    saving.value = false
  }
}

/** 弹窗场景下父级使用 v-if 挂载本会话；页面场景仅挂载一次，均需拉档案 */
onMounted(() => {
  loadProfile()
})
</script>

<style lang="scss" scoped>
@import '@/styles/_variables.scss';

.persona-editor {
  display: flex;
  flex-direction: column;
  gap: 28rpx;
  min-height: 0;
  flex: 1;
  width: 100%;
  box-sizing: border-box;

  /** 独立页：保存条与组件底边留白；弹窗 compact 不占高度 */
  &:not(.persona-editor--compact) .persona-editor__save {
    margin-bottom: 24rpx;
  }
}

.persona-editor__surface {
  box-sizing: border-box;
  width: 100%;

  /** 独立页：白底主体卡，与外层灰底区分开 */
  &--raised {
    background: $white;
    border-radius: 28rpx;
    padding: 36rpx 30rpx 40rpx;
    border: 1rpx solid rgba(44, 30, 26, 0.08);
    box-shadow: $shadow-sm;
  }
}

.persona-editor__body {
  flex: 1;
  min-height: 0;
  width: 100%;
}

.persona-editor__body-pad-bottom {
  height: env(safe-area-inset-bottom);
  height: constant(safe-area-inset-bottom);
  min-height: 16rpx;
}

.persona-editor__save {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12rpx;
  margin-top: 0;
  padding: 26rpx;
  border-radius: 24rpx;
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

.persona-editor__save-icon {
  font-size: 32rpx;
}

.persona-editor__save-text {
  font-size: 28rpx;
  font-weight: 600;
  color: $white;
}

.field {
  margin-bottom: 44rpx;

  &:last-child {
    margin-bottom: 0;
  }

  &-label {
    display: block;
    font-size: 32rpx;
    font-weight: 700;
    color: $text-main;
    letter-spacing: 0.02em;
    margin-bottom: 18rpx;
  }

  &-input-box {
    display: flex;
    align-items: center;
    min-height: 88rpx;
    padding: 0 24rpx;
    background: #faf7f2;
    border-radius: 18rpx;
    box-sizing: border-box;
    border: 1rpx solid rgba(44, 30, 26, 0.08);
  }

  &-textarea-box {
    padding: 20rpx 24rpx;
    background: #faf7f2;
    border-radius: 18rpx;
    box-sizing: border-box;
    border: 1rpx solid rgba(44, 30, 26, 0.08);
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
