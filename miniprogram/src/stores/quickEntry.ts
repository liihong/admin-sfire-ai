/**
 * Quick Entry Store - 快捷指令状态管理
 * 
 * 使用 Pinia 管理当前选中的快捷指令
 * 选中的快捷指令信息会持久化到本地存储
 */

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { QuickEntry } from '@/api/quickEntry'

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

// ============== Storage Key ==============
const ACTIVE_QUICK_ENTRY_INFO_KEY = 'active_quick_entry_info'

/**
 * Quick Entry Store
 */
export const useQuickEntryStore = defineStore('quickEntry', () => {
  // ============== State ==============
  
  // 当前选中的快捷指令
  const activeQuickEntry = ref<ActiveQuickEntry | null>(null)

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
    try {
      const stored = uni.getStorageSync(ACTIVE_QUICK_ENTRY_INFO_KEY)
      if (stored) {
        return JSON.parse(stored) as ActiveQuickEntry
      }
      return null
    } catch (error) {
      console.error('Failed to get active quick entry from storage:', error)
      return null
    }
  }

  /**
   * 保存选中的快捷指令信息到 storage
   */
  function saveActiveQuickEntryToStorage(entry: ActiveQuickEntry) {
    try {
      uni.setStorageSync(ACTIVE_QUICK_ENTRY_INFO_KEY, JSON.stringify(entry))
    } catch (error) {
      console.error('Failed to save active quick entry to storage:', error)
    }
  }

  /**
   * 清除 storage 中的快捷指令信息
   */
  function clearActiveQuickEntryFromStorage() {
    try {
      uni.removeStorageSync(ACTIVE_QUICK_ENTRY_INFO_KEY)
    } catch (error) {
      console.error('Failed to clear active quick entry from storage:', error)
    }
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

  return {
    // State
    activeQuickEntry,
    
    // Getters
    hasActiveQuickEntry,
    getActiveQuickEntryInstructions,
    
    // Actions
    setActiveQuickEntry,
    clearActiveQuickEntry,
    loadActiveQuickEntryFromStorage
  }
})




