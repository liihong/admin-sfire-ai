<template>
  <view class="library-page">
    <BaseHeader title="文案库" :subtitle="projectSubtitle" @back="goBack" />

    <!-- 状态筛选 -->
    <view class="filter-bar">
      <view
        v-for="item in statusTabs"
        :key="item.value"
        class="tab-item"
        :class="{ active: currentStatus === item.value }"
        @tap="switchStatus(item.value)"
      >
        <text class="tab-text">{{ item.label }}</text>
      </view>
    </view>

    <!-- 搜索 -->
    <view class="search-section">
      <view class="search-box">
        <u-icon name="search" color="#86909C" size="18"></u-icon>
        <input
          class="search-input"
          v-model="keyword"
          placeholder="搜索文案内容..."
          @input="handleKeywordInput"
        />
        <view v-if="keyword" class="clear-btn" @tap="clearKeyword">
          <u-icon name="close" color="#86909C" size="16"></u-icon>
        </view>
      </view>
    </view>

    <!-- 列表 -->
    <scroll-view
      class="list-container"
      scroll-y
      :refresher-enabled="true"
      :refresher-triggered="refreshing"
      @refresherrefresh="refreshList"
      @scrolltolower="loadMore"
    >
      <view v-if="items.length > 0" class="entry-list">
        <view v-for="entry in items" :key="entry.id" class="entry-card">
          <view class="card-top">
            <view class="status-pill" :class="entry.status">
              <text class="pill-text">{{ statusLabel(entry.status) }}</text>
            </view>
            <view class="card-actions">
              <view class="action-btn" @tap="openEdit(entry)">
                <u-icon name="edit-pen" color="#86909C" size="16"></u-icon>
              </view>
              <view class="action-btn danger" @tap="confirmDelete(entry)">
                <u-icon name="trash" color="#EF4444" size="16"></u-icon>
              </view>
            </view>
          </view>

          <view class="content" @tap="openEdit(entry)">
            <text class="content-text">{{ entry.content }}</text>
          </view>

          <view v-if="entry.tags?.length" class="tags">
            <view v-for="t in entry.tags" :key="t" class="tag">
              <text class="tag-text">{{ t }}</text>
            </view>
          </view>

          <view class="metrics">
            <view class="metric-item">
              <text class="metric-label">播放</text>
              <text class="metric-value">{{ entry.views ?? '-' }}</text>
            </view>
            <view class="metric-item">
              <text class="metric-label">点赞</text>
              <text class="metric-value">{{ entry.likes ?? '-' }}</text>
            </view>
            <view class="metric-item">
              <text class="metric-label">评论</text>
              <text class="metric-value">{{ entry.comments ?? '-' }}</text>
            </view>
            <view class="metric-item">
              <text class="metric-label">转发</text>
              <text class="metric-value">{{ entry.shares ?? '-' }}</text>
            </view>
          </view>

          <view class="card-bottom">
            <text class="time-text">{{ formatTime(entry.created_at) }}</text>
            <view class="bottom-actions">
              <view class="mini-btn" @tap="copyText(entry.content)">
                <text class="mini-btn-text">复制</text>
              </view>
              <view class="mini-btn primary" @tap="openPublish(entry)">
                <text class="mini-btn-text">补录数据</text>
              </view>
              <view class="mini-btn" @tap="toggleArchive(entry)">
                <text class="mini-btn-text">{{ entry.status === 'archived' ? '取消归档' : '归档' }}</text>
              </view>
            </view>
          </view>
        </view>
      </view>

      <view v-else-if="!loading" class="empty">
        <text class="empty-title">暂无文案</text>
        <text class="empty-subtitle">点击右下角“+”新建一条文案</text>
      </view>

      <view v-if="loading" class="loading">
        <u-loading-icon mode="spinner" color="#3B82F6"></u-loading-icon>
        <text class="loading-text">加载中...</text>
      </view>

      <view class="bottom-safe-area"></view>
    </scroll-view>

    <!-- 新建按钮 -->
    <view class="fab-wrapper">
      <view class="fab-btn" @tap="openCreate">
        <u-icon name="plus" color="#FFFFFF" size="24"></u-icon>
      </view>
    </view>

    <!-- 新建/编辑弹窗 -->
    <view v-if="showEditModal" class="modal-overlay" @tap="closeEditModal">
      <view class="modal" @tap.stop>
        <view class="modal-header">
          <text class="modal-title">{{ editingId ? '编辑文案' : '新建文案' }}</text>
          <view class="modal-close" @tap="closeEditModal">
            <u-icon name="close" color="#86909C" size="20"></u-icon>
          </view>
        </view>

        <view class="modal-body">
          <view class="field">
            <text class="field-label">文案内容</text>
            <textarea v-model="formContent" class="textarea" placeholder="粘贴或输入一段文案..." :maxlength="200000" />
          </view>

          <view class="field">
            <text class="field-label">标签（逗号分隔）</text>
            <input v-model="formTagsText" class="input" placeholder="例如：开场，反转，干货" />
          </view>

          <view class="field">
            <text class="field-label">状态</text>
            <picker :range="statusPickerLabels" :value="statusPickerIndex" @change="onStatusPickerChange">
              <view class="picker">
                <text class="picker-text">{{ statusLabel(formStatus) }}</text>
                <u-icon name="arrow-down" color="#86909C" size="14"></u-icon>
              </view>
            </picker>
          </view>
        </view>

        <view class="modal-footer">
          <view class="btn secondary" @tap="closeEditModal"><text>取消</text></view>
          <view class="btn primary" @tap="submitEdit"><text>保存</text></view>
        </view>
      </view>
    </view>

    <!-- 补录发布数据弹窗 -->
    <view v-if="showPublishModal" class="modal-overlay" @tap="closePublishModal">
      <view class="modal" @tap.stop>
        <view class="modal-header">
          <text class="modal-title">补录发布数据</text>
          <view class="modal-close" @tap="closePublishModal">
            <u-icon name="close" color="#86909C" size="20"></u-icon>
          </view>
        </view>

        <view class="modal-body">
          <view class="field grid">
            <view class="grid-item">
              <text class="field-label">播放</text>
              <input v-model="publishViews" type="number" class="input" placeholder="0" />
            </view>
            <view class="grid-item">
              <text class="field-label">点赞</text>
              <input v-model="publishLikes" type="number" class="input" placeholder="0" />
            </view>
            <view class="grid-item">
              <text class="field-label">评论</text>
              <input v-model="publishComments" type="number" class="input" placeholder="0" />
            </view>
            <view class="grid-item">
              <text class="field-label">转发</text>
              <input v-model="publishShares" type="number" class="input" placeholder="0" />
            </view>
          </view>
          <view class="hint">
            <text class="hint-text">保存后将自动把状态标记为“已发布”。</text>
          </view>
        </view>

        <view class="modal-footer">
          <view class="btn secondary" @tap="closePublishModal"><text>取消</text></view>
          <view class="btn primary" @tap="submitPublish"><text>保存</text></view>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import BaseHeader from '@/components/base/BaseHeader.vue'
import { useProjectStore } from '@/stores/project'
import type { CopywritingEntry, CopywritingEntryStatus } from '@/api/copywritingLibrary'
import {
  createCopywritingEntry,
  getCopywritingEntryList,
  updateCopywritingEntry,
  deleteCopywritingEntry,
  updateCopywritingPublishData,
} from '@/api/copywritingLibrary'

const projectStore = useProjectStore()

const activeProjectId = computed(() => {
  const id = projectStore.activeProject?.id
  return id ? Number(id) : undefined
})

const projectSubtitle = computed(() => {
  const p = projectStore.activeProject
  if (!p) return '未选择IP'
  return `当前IP：${p.name || ''}`
})

const statusTabs: Array<{ label: string; value: CopywritingEntryStatus | 'all' }> = [
  { label: '全部', value: 'all' },
  { label: '草稿', value: 'draft' },
  { label: '待拍摄', value: 'todo' },
  { label: '已发布', value: 'published' },
  { label: '归档', value: 'archived' },
]

const statusPickerOptions: CopywritingEntryStatus[] = ['draft', 'todo', 'published', 'archived']
const statusPickerLabels = ['草稿', '待拍摄', '已发布', '归档']

const currentStatus = ref<CopywritingEntryStatus | 'all'>('all')
const keyword = ref('')
let keywordTimer: ReturnType<typeof setTimeout> | null = null

const items = ref<CopywritingEntry[]>([])
const loading = ref(false)
const refreshing = ref(false)
const pageNum = ref(1)
const pageSize = ref(10)
const total = ref(0)

const hasMore = computed(() => items.value.length < total.value)

function goBack() {
  uni.navigateBack({
    fail: () => uni.switchTab({ url: '/pages/project/index' }),
  })
}

function ensureProjectReady(): boolean {
  if (!activeProjectId.value) {
    uni.showToast({ title: '请先选择一个IP项目', icon: 'none' })
    return false
  }
  return true
}

function statusLabel(status: CopywritingEntryStatus): string {
  switch (status) {
    case 'draft':
      return '草稿'
    case 'todo':
      return '待拍摄'
    case 'published':
      return '已发布'
    case 'archived':
      return '归档'
    default:
      return status
  }
}

function formatTime(timeStr: string): string {
  const date = new Date(timeStr)
  const now = new Date()
  const diff = now.getTime() - date.getTime()
  const minutes = Math.floor(diff / 60000)
  const hours = Math.floor(diff / 3600000)
  const days = Math.floor(diff / 86400000)

  if (minutes < 1) return '刚刚'
  if (minutes < 60) return `${minutes}分钟前`
  if (hours < 24) return `${hours}小时前`
  if (days < 7) return `${days}天前`
  return date.toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' })
}

async function fetchList(reset = false) {
  if (!ensureProjectReady()) return
  if (loading.value) return

  loading.value = true
  try {
    if (reset) {
      pageNum.value = 1
    }
    const resp = await getCopywritingEntryList({
      pageNum: pageNum.value,
      pageSize: pageSize.value,
      project_id: activeProjectId.value as number,
      status: currentStatus.value === 'all' ? undefined : currentStatus.value,
      keyword: keyword.value || undefined,
    })

    if (reset) {
      items.value = resp.data.list
    } else {
      items.value.push(...resp.data.list)
    }
    total.value = resp.data.total
    pageNum.value++
  } catch (e: any) {
    uni.showToast({ title: e?.message || '加载失败', icon: 'none' })
  } finally {
    loading.value = false
    refreshing.value = false
  }
}

function switchStatus(v: CopywritingEntryStatus | 'all') {
  currentStatus.value = v
  fetchList(true)
}

function handleKeywordInput() {
  if (keywordTimer) clearTimeout(keywordTimer)
  keywordTimer = setTimeout(() => fetchList(true), 300)
}

function clearKeyword() {
  keyword.value = ''
  fetchList(true)
}

function refreshList() {
  refreshing.value = true
  fetchList(true)
}

function loadMore() {
  if (hasMore.value && !loading.value) {
    fetchList(false)
  }
}

function copyText(text: string) {
  uni.setClipboardData({
    data: text,
    success: () => uni.showToast({ title: '已复制', icon: 'success' }),
  })
}

// ===== 新建/编辑 =====
const showEditModal = ref(false)
const editingId = ref<number | null>(null)
const formContent = ref('')
const formTagsText = ref('')
const formStatus = ref<CopywritingEntryStatus>('todo')

const statusPickerIndex = computed(() => statusPickerOptions.indexOf(formStatus.value))

function openCreate() {
  if (!ensureProjectReady()) return
  editingId.value = null
  formContent.value = ''
  formTagsText.value = ''
  formStatus.value = 'todo'
  showEditModal.value = true
}

function openEdit(entry: CopywritingEntry) {
  editingId.value = entry.id
  formContent.value = entry.content
  formTagsText.value = (entry.tags || []).join('，')
  formStatus.value = entry.status
  showEditModal.value = true
}

function closeEditModal() {
  showEditModal.value = false
}

function parseTagsFromText(v: string): string[] {
  if (!v) return []
  const parts = v
    .split(/[,，\n]/)
    .map(s => s.trim())
    .filter(Boolean)
  // 去重（保持顺序）
  const seen = new Set<string>()
  const out: string[] = []
  for (const p of parts) {
    if (seen.has(p)) continue
    seen.add(p)
    out.push(p)
  }
  return out
}

function onStatusPickerChange(e: any) {
  const idx = Number(e?.detail?.value ?? 0)
  formStatus.value = statusPickerOptions[idx] || 'todo'
}

async function submitEdit() {
  if (!ensureProjectReady()) return
  const content = formContent.value.trim()
  if (!content) {
    uni.showToast({ title: '请输入文案内容', icon: 'none' })
    return
  }
  const tags = parseTagsFromText(formTagsText.value)

  try {
    uni.showLoading({ title: '保存中...' })
    if (editingId.value) {
      await updateCopywritingEntry(editingId.value, {
        content,
        tags,
        status: formStatus.value,
      })
    } else {
      await createCopywritingEntry({
        project_id: activeProjectId.value as number,
        content,
        tags,
        status: formStatus.value,
      })
    }
    closeEditModal()
    await fetchList(true)
    uni.showToast({ title: '已保存', icon: 'success' })
  } catch (e: any) {
    uni.showToast({ title: e?.message || '保存失败', icon: 'none' })
  } finally {
    uni.hideLoading()
  }
}

async function confirmDelete(entry: CopywritingEntry) {
  const res = await uni.showModal({
    title: '确认删除',
    content: '确定要删除这条文案吗？',
    confirmText: '删除',
    cancelText: '取消',
  })
  if (!res.confirm) return
  try {
    uni.showLoading({ title: '删除中...' })
    await deleteCopywritingEntry(entry.id)
    await fetchList(true)
    uni.showToast({ title: '已删除', icon: 'success' })
  } catch (e: any) {
    uni.showToast({ title: e?.message || '删除失败', icon: 'none' })
  } finally {
    uni.hideLoading()
  }
}

async function toggleArchive(entry: CopywritingEntry) {
  const nextStatus: CopywritingEntryStatus = entry.status === 'archived' ? 'todo' : 'archived'
  try {
    await updateCopywritingEntry(entry.id, { status: nextStatus })
    await fetchList(true)
  } catch (e: any) {
    uni.showToast({ title: e?.message || '操作失败', icon: 'none' })
  }
}

// ===== 补录发布数据 =====
const showPublishModal = ref(false)
const publishingId = ref<number | null>(null)
const publishViews = ref('')
const publishLikes = ref('')
const publishComments = ref('')
const publishShares = ref('')

function openPublish(entry: CopywritingEntry) {
  publishingId.value = entry.id
  publishViews.value = entry.views != null ? String(entry.views) : ''
  publishLikes.value = entry.likes != null ? String(entry.likes) : ''
  publishComments.value = entry.comments != null ? String(entry.comments) : ''
  publishShares.value = entry.shares != null ? String(entry.shares) : ''
  showPublishModal.value = true
}

function closePublishModal() {
  showPublishModal.value = false
  publishingId.value = null
}

function toIntOrUndefined(v: string): number | undefined {
  const s = (v || '').trim()
  if (!s) return undefined
  const n = Number(s)
  if (!Number.isFinite(n) || n < 0) return undefined
  return Math.floor(n)
}

async function submitPublish() {
  if (!publishingId.value) return
  try {
    uni.showLoading({ title: '保存中...' })
    await updateCopywritingPublishData(publishingId.value, {
      views: toIntOrUndefined(publishViews.value),
      likes: toIntOrUndefined(publishLikes.value),
      comments: toIntOrUndefined(publishComments.value),
      shares: toIntOrUndefined(publishShares.value),
    })
    closePublishModal()
    await fetchList(true)
    uni.showToast({ title: '已保存', icon: 'success' })
  } catch (e: any) {
    uni.showToast({ title: e?.message || '保存失败', icon: 'none' })
  } finally {
    uni.hideLoading()
  }
}

onMounted(() => {
  fetchList(true)
})

// 从其他页面返回时刷新（避免切换项目后库内容不一致）
onShow(() => {
  fetchList(true)
})
</script>

<style lang="scss" scoped>
.library-page {
  min-height: 100vh;
  background: #f5f7fa;
}

.filter-bar {
  display: flex;
  gap: 16rpx;
  padding: 20rpx 24rpx 12rpx;
  overflow-x: auto;
  white-space: nowrap;
}
.tab-item {
  padding: 12rpx 18rpx;
  border-radius: 999rpx;
  background: rgba(255, 255, 255, 0.9);
  border: 1rpx solid rgba(0, 0, 0, 0.06);
}
.tab-item.active {
  background: rgba(255, 107, 53, 0.12);
  border-color: rgba(255, 107, 53, 0.25);
}
.tab-text {
  font-size: 24rpx;
  color: #1d2129;
}

.search-section {
  padding: 0 24rpx 16rpx;
}
.search-box {
  display: flex;
  align-items: center;
  gap: 12rpx;
  padding: 16rpx 18rpx;
  background: #ffffff;
  border-radius: 18rpx;
  border: 1rpx solid rgba(0, 0, 0, 0.06);
}
.search-input {
  flex: 1;
  font-size: 26rpx;
  color: #1d2129;
}
.clear-btn {
  width: 36rpx;
  height: 36rpx;
  display: flex;
  align-items: center;
  justify-content: center;
}

.list-container {
  height: calc(100vh - 280rpx);
  padding: 0 24rpx;
}

.entry-card {
  background: rgba(255, 255, 255, 0.96);
  border-radius: 20rpx;
  padding: 22rpx;
  margin-bottom: 18rpx;
  border: 1rpx solid rgba(0, 0, 0, 0.06);
}
.card-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.status-pill {
  padding: 6rpx 14rpx;
  border-radius: 999rpx;
  background: rgba(0, 0, 0, 0.04);
}
.status-pill.todo {
  background: rgba(59, 130, 246, 0.1);
}
.status-pill.published {
  background: rgba(16, 185, 129, 0.12);
}
.status-pill.archived {
  background: rgba(107, 114, 128, 0.12);
}
.status-pill.draft {
  background: rgba(249, 115, 22, 0.12);
}
.pill-text {
  font-size: 22rpx;
  color: #4e5969;
}

.card-actions {
  display: flex;
  gap: 14rpx;
}
.action-btn {
  width: 56rpx;
  height: 56rpx;
  border-radius: 14rpx;
  background: rgba(0, 0, 0, 0.03);
  display: flex;
  align-items: center;
  justify-content: center;
}
.action-btn.danger {
  background: rgba(239, 68, 68, 0.06);
}

.content {
  margin-top: 14rpx;
}
.content-text {
  font-size: 28rpx;
  color: #1d2129;
  line-height: 1.7;
  white-space: pre-wrap;
  word-break: break-word;
}

.tags {
  margin-top: 14rpx;
  display: flex;
  flex-wrap: wrap;
  gap: 10rpx;
}
.tag {
  padding: 6rpx 12rpx;
  border-radius: 999rpx;
  background: rgba(255, 107, 53, 0.1);
}
.tag-text {
  font-size: 22rpx;
  color: #ff6b35;
}

.metrics {
  margin-top: 16rpx;
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 10rpx;
}
.metric-item {
  padding: 12rpx 10rpx;
  border-radius: 14rpx;
  background: rgba(0, 0, 0, 0.02);
  text-align: center;
}
.metric-label {
  display: block;
  font-size: 20rpx;
  color: #86909c;
}
.metric-value {
  display: block;
  margin-top: 4rpx;
  font-size: 24rpx;
  font-weight: 600;
  color: #1d2129;
}

.card-bottom {
  margin-top: 16rpx;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12rpx;
}
.time-text {
  font-size: 22rpx;
  color: #86909c;
}
.bottom-actions {
  display: flex;
  gap: 10rpx;
  flex-wrap: wrap;
  justify-content: flex-end;
}
.mini-btn {
  padding: 10rpx 14rpx;
  border-radius: 14rpx;
  background: rgba(0, 0, 0, 0.04);
}
.mini-btn.primary {
  background: rgba(59, 130, 246, 0.12);
}
.mini-btn-text {
  font-size: 22rpx;
  color: #4e5969;
}

.empty {
  padding: 120rpx 24rpx;
  text-align: center;
}
.empty-title {
  font-size: 32rpx;
  font-weight: 700;
  color: #1d2129;
}
.empty-subtitle {
  margin-top: 10rpx;
  font-size: 26rpx;
  color: #86909c;
}

.loading {
  padding: 28rpx 0;
  display: flex;
  gap: 12rpx;
  align-items: center;
  justify-content: center;
}
.loading-text {
  font-size: 26rpx;
  color: #6b7280;
}

.bottom-safe-area {
  height: 140rpx;
}

.fab-wrapper {
  position: fixed;
  right: 26rpx;
  bottom: 40rpx;
  z-index: 99;
}
.fab-btn {
  width: 104rpx;
  height: 104rpx;
  border-radius: 50%;
  background: linear-gradient(135deg, #ff6b35, #ff8c5a);
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 10rpx 24rpx rgba(255, 107, 53, 0.35);
}

.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.35);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24rpx;
  z-index: 200;
}
.modal {
  width: 100%;
  max-width: 680rpx;
  background: #ffffff;
  border-radius: 20rpx;
  overflow: hidden;
}
.modal-header {
  padding: 20rpx 22rpx;
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 1rpx solid rgba(0, 0, 0, 0.06);
}
.modal-title {
  font-size: 30rpx;
  font-weight: 700;
  color: #1d2129;
}
.modal-close {
  width: 56rpx;
  height: 56rpx;
  display: flex;
  align-items: center;
  justify-content: center;
}
.modal-body {
  padding: 20rpx 22rpx;
}
.field {
  margin-bottom: 16rpx;
}
.field-label {
  display: block;
  margin-bottom: 10rpx;
  font-size: 24rpx;
  color: #4e5969;
}
.textarea {
  width: 100%;
  min-height: 240rpx;
  padding: 14rpx 16rpx;
  border-radius: 14rpx;
  background: rgba(0, 0, 0, 0.03);
  font-size: 26rpx;
  line-height: 1.6;
}
.input {
  width: 100%;
  padding: 14rpx 16rpx;
  border-radius: 14rpx;
  background: rgba(0, 0, 0, 0.03);
  font-size: 26rpx;
}
.picker {
  width: 100%;
  padding: 14rpx 16rpx;
  border-radius: 14rpx;
  background: rgba(0, 0, 0, 0.03);
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.picker-text {
  font-size: 26rpx;
  color: #1d2129;
}
.modal-footer {
  padding: 18rpx 22rpx;
  display: flex;
  gap: 16rpx;
  border-top: 1rpx solid rgba(0, 0, 0, 0.06);
}
.btn {
  flex: 1;
  height: 84rpx;
  border-radius: 16rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 28rpx;
  font-weight: 600;
}
.btn.secondary {
  background: rgba(0, 0, 0, 0.05);
  color: #1d2129;
}
.btn.primary {
  background: linear-gradient(135deg, #3b82f6, #4facfe);
  color: #ffffff;
}
.grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16rpx;
}
.hint {
  margin-top: 6rpx;
  padding: 10rpx 12rpx;
  border-radius: 12rpx;
  background: rgba(16, 185, 129, 0.08);
}
.hint-text {
  font-size: 22rpx;
  color: #10b981;
}
</style>

