/**
 * Settings Store - AI 模型设置状态管理
 * 
 * 使用 Pinia 管理全局设置，包括当前选中的 AI 模型类型
 * 支持本地持久化存储
 */

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { storage } from '@/utils/storage'

// 支持的模型类型
export type ModelType = 'deepseek' | 'doubao' | 'gpt4' | 'claude'

// 模型配置信息
export interface ModelConfig {
  type: ModelType
  name: string
  icon: string
  description: string
  available: boolean
}

// 可用模型列表
export const MODEL_LIST: ModelConfig[] = [
  {
    type: 'deepseek',
    name: 'DeepSeek',
    icon: '🧠',
    description: '深度求索，国产大模型',
    available: true
  },
  {
    type: 'doubao',
    name: '豆包',
    icon: '🫛',
    description: '字节跳动火山引擎',
    available: true
  },
  {
    type: 'gpt4',
    name: 'GPT-4',
    icon: '🤖',
    description: 'OpenAI GPT-4',
    available: false  // 预留，暂不可用
  },
  {
    type: 'claude',
    name: 'Claude',
    icon: '🎭',
    description: 'Anthropic Claude',
    available: true  // 预留，暂不可用
  }
]

// 缓存 key
const STORAGE_KEY = 'dingma_ai_settings'

/**
 * Settings Store
 */
export const useSettingsStore = defineStore('settings', () => {
  // ============== State ==============
  
  // 当前选中的模型类型
  const modelType = ref<ModelType>('claude')
  
  // ============== Getters ==============
  
  // 获取当前模型配置
  const currentModel = computed(() => {
    return MODEL_LIST.find(m => m.type === modelType.value) || MODEL_LIST[0]
  })
  
  // 获取可用模型列表
  const availableModels = computed(() => {
    return MODEL_LIST.filter(m => m.available)
  })
  
  // 获取所有模型列表（包括不可用的）
  const allModels = computed(() => MODEL_LIST)
  
  // ============== Actions ==============
  
  /**
   * 设置模型类型
   */
  function setModelType(type: ModelType) {
    const model = MODEL_LIST.find(m => m.type === type)
    if (model && model.available) {
      modelType.value = type
      saveToStorage()
    }
  }
  
  /**
   * 保存设置到本地存储
   */
  function saveToStorage() {
    const settings = {
      modelType: modelType.value
    }
    storage.set(STORAGE_KEY, settings)
  }
  
  /**
   * 从本地存储加载设置
   */
  function loadFromStorage() {
    const stored = storage.get<{ modelType: ModelType }>(STORAGE_KEY)
    if (stored?.modelType) {
      // 验证模型类型是否有效
      const model = MODEL_LIST.find(m => m.type === stored.modelType)
      if (model && model.available) {
        modelType.value = stored.modelType
      }
    }
  }
  
  /**
   * 重置设置到默认值
   */
  function resetSettings() {
    modelType.value = 'claude'
    saveToStorage()
  }
  
  // 初始化时从本地存储加载
  loadFromStorage()
  
  return {
    // State
    modelType,
    
    // Getters
    currentModel,
    availableModels,
    allModels,
    
    // Actions
    setModelType,
    saveToStorage,
    loadFromStorage,
    resetSettings
  }
})



