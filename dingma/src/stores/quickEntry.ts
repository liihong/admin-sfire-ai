/**
 * Quick Entry Store - 快捷指令状态管理
 * 
 * 使用 Pinia 管理当前选中的快捷指令
 * 选中的快捷指令信息会持久化到本地存储
 */

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { QuickEntry } from '@/api/quickEntry'
import { getQuickEntries } from '@/api/quickEntry'
import { storage } from '@/utils/storage'

// ============== 类型定义 ==============

/**
 * 激活的快捷指令信息
 */
export interface ActiveQuickEntry {
  id: number
  title: string
  instructions: string | null
  action_type: 'agent' | 'skill' | 'prompt'
  action_value: string
}

/** 分类项（今天拍点啥） */
export interface CategoryItem {
  key: string
  label: string
  icon: string
  color: string
  id?: number
  action_type?: 'agent' | 'skill' | 'prompt' | 'url'
  action_value?: string
  instructions?: string | null
}

// ============== Storage Key ==============
const ACTIVE_QUICK_ENTRY_INFO_KEY = 'active_quick_entry_info'

/**
 * Quick Entry Store
 */
export const useQuickEntryStore = defineStore('quickEntry', () => {
  // ============== State ==============
  
  // 当前选中的快捷指令
  const activeQuickEntry = ref<ActiveQuickEntry | null>(null)

  // 今天拍点啥 - 分类列表
  const categoryList = ref<CategoryItem[]>([])
  // 快捷指令库列表
  const commandList = ref<QuickEntry[]>([])

  // 是否已加载过（避免重复请求）
  const hasQuickEntryLoaded = ref(false)
  // 是否正在加载
  const isQuickEntryLoading = ref(false)

  // ============== Getters ==============
  
  // 是否有选中的快捷指令
  const hasActiveQuickEntry = computed(() => !!activeQuickEntry.value)
  
  // 获取当前快捷指令的 instructions
  const getActiveQuickEntryInstructions = computed(() => {
    return activeQuickEntry.value?.instructions || null
  })

  // ============== Actions ==============

  /**
   * 从 storage 读取选中的快捷指令信息
   */
  function getActiveQuickEntryFromStorage(): ActiveQuickEntry | null {
    return storage.get<ActiveQuickEntry>(ACTIVE_QUICK_ENTRY_INFO_KEY)
  }

  /**
   * 保存选中的快捷指令信息到 storage
   */
  function saveActiveQuickEntryToStorage(entry: ActiveQuickEntry) {
    storage.set(ACTIVE_QUICK_ENTRY_INFO_KEY, entry)
  }

  /**
   * 清除 storage 中的快捷指令信息
   */
  function clearActiveQuickEntryFromStorage() {
    storage.remove(ACTIVE_QUICK_ENTRY_INFO_KEY)
  }

  /**
   * 设置选中的快捷指令（直接覆盖）
   * 
   * @param entry 快捷指令信息
   */
  function setActiveQuickEntry(entry: QuickEntry) {
    const entryInfo: ActiveQuickEntry = {
      id: entry.id,
      title: entry.title,
      instructions: entry.instructions,
      action_type: entry.action_type,
      action_value: entry.action_value
    }
    activeQuickEntry.value = entryInfo
    saveActiveQuickEntryToStorage(entryInfo)
  }

  /**
   * 清除选中的快捷指令（清空选中状态和本地存储）
   */
  function clearActiveQuickEntry() {
    activeQuickEntry.value = null
    clearActiveQuickEntryFromStorage()
  }

  /**
   * 从 storage 加载选中的快捷指令信息（初始化时调用）
   */
  function loadActiveQuickEntryFromStorage() {
    const stored = getActiveQuickEntryFromStorage()
    if (stored) {
      activeQuickEntry.value = stored
    }
  }

  /**
   * 加载快捷入口列表（今天拍点啥 + 快捷指令库）
   * @param forceRefresh 是否强制刷新（忽略已加载状态，用于下拉刷新等）
   * @returns 是否加载成功
   */
  async function loadQuickEntryList(forceRefresh = false): Promise<boolean> {
    if (isQuickEntryLoading.value) return false
    if (hasQuickEntryLoaded.value && !forceRefresh) return true

    isQuickEntryLoading.value = true
    try {
      const [categoryResponse, commandResponse] = await Promise.all([
        getQuickEntries('category'),
        getQuickEntries('command')
      ])

      if (categoryResponse.code === 200 && categoryResponse.data?.entries) {
        categoryList.value = categoryResponse.data.entries.map((entry: QuickEntry) => ({
          key: entry.unique_key || String(entry.id),
          label: entry.title,
          icon: entry.icon_class,
          color: entry.bg_color || '#F69C0E',
          id: entry.id,
          action_type: entry.action_type,
          action_value: entry.action_value,
          instructions: entry.instructions
        }))
      } else {
        categoryList.value = []
      }

      if (commandResponse.code === 200 && commandResponse.data?.entries) {
        commandList.value = commandResponse.data.entries
      } else {
        commandList.value = []
      }

      hasQuickEntryLoaded.value = true
      return true
    } catch (error) {
      console.error('[QuickEntryStore] 加载快捷入口失败:', error)
      categoryList.value = []
      commandList.value = []
      const msg = (error as Error)?.message || '加载失败'
      uni.showToast({ title: msg, icon: 'none' })
      return false
    } finally {
      isQuickEntryLoading.value = false
    }
  }

  return {
    // State
    activeQuickEntry,
    categoryList,
    commandList,
    hasQuickEntryLoaded,
    isQuickEntryLoading,

    // Getters
    hasActiveQuickEntry,
    getActiveQuickEntryInstructions,

    // Actions
    setActiveQuickEntry,
    clearActiveQuickEntry,
    loadActiveQuickEntryFromStorage,
    loadQuickEntryList
  }
})







