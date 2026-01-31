/**
 * Agent Store - 智能体状态管理
 * 
 * 使用 Pinia 管理当前激活的智能体
 * 激活的智能体信息会持久化到本地存储
 */

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { getAgentList, type Agent } from '@/api/agent'
import type { ResponseData } from '@/utils/request'
import { storage } from '@/utils/storage'

// ============== 类型定义 ==============

/**
 * 激活的智能体信息
 */
export interface ActiveAgent {
  id: string
  name: string
  icon?: string
  description?: string
}

// ============== Storage Key ==============
const ACTIVE_AGENT_INFO_KEY = 'active_agent_info'

/**
 * Agent Store
 */
export const useAgentStore = defineStore('agent', () => {
  // ============== State ==============
  
  // 当前激活的智能体
  const activeAgent = ref<ActiveAgent | null>(null)
  
  // 加载状态（预留）
  const isLoading = ref(false)

  // ============== Getters ==============
  
  // 是否有激活的智能体
  const hasActiveAgent = computed(() => !!activeAgent.value)
  
  // 获取当前智能体 ID
  const getActiveAgentId = computed(() => activeAgent.value?.id || '')

  // ============== Actions ==============

  /**
   * 从 storage 读取激活的智能体信息
   */
  function getActiveAgentFromStorage(): ActiveAgent | null {
    return storage.get<ActiveAgent>(ACTIVE_AGENT_INFO_KEY)
  }

  /**
   * 保存激活的智能体信息到 storage
   */
  function saveActiveAgentToStorage(agent: ActiveAgent) {
    storage.set(ACTIVE_AGENT_INFO_KEY, agent)
  }

  /**
   * 清除 storage 中的激活智能体信息
   */
  function clearActiveAgentFromStorage() {
    storage.remove(ACTIVE_AGENT_INFO_KEY)
  }

  /**
   * 根据 agentId 从 API 获取智能体详情并设置激活的智能体
   * 只存储基本信息（id, name, icon, description），不包含 system_prompt
   * 
   * @param agentId 智能体 ID
   */
  async function setActiveAgentById(agentId: string) {
    // 如果已经是当前激活的智能体，直接返回
    if (activeAgent.value?.id === agentId) {
      return
    }

    isLoading.value = true
    try {
      // 调用 API 获取智能体列表
      const response: ResponseData<{ agents: Agent[] }> = await getAgentList()
      
      if (response.code === 200 && response.data?.agents) {
        // 从列表中查找对应的智能体
        const agent = response.data.agents.find(a => String(a.id) === String(agentId))
        
        if (agent) {
          // 只存储基本信息，不包含 system_prompt
          const agentInfo: ActiveAgent = {
            id: String(agent.id),
            name: agent.name,
            icon: agent.icon,
            description: agent.description
          }
          activeAgent.value = agentInfo
          saveActiveAgentToStorage(agentInfo)
        } else {
          // 如果找不到，使用默认值
          const agentInfo: ActiveAgent = {
            id: agentId,
            name: '智能体',
            icon: '',
            description: ''
          }
          activeAgent.value = agentInfo
          saveActiveAgentToStorage(agentInfo)
        }
      } else {
        // 失败时使用默认值
        const agentInfo: ActiveAgent = {
          id: agentId,
          name: '智能体',
          icon: '',
          description: ''
        }
        activeAgent.value = agentInfo
        saveActiveAgentToStorage(agentInfo)
      }
    } catch {
      // 失败时使用默认值
      const agentInfo: ActiveAgent = {
        id: agentId,
        name: '智能体',
        icon: '',
        description: ''
      }
      activeAgent.value = agentInfo
      saveActiveAgentToStorage(agentInfo)
    } finally {
      isLoading.value = false
    }
  }

  /**
   * 设置激活的智能体（直接设置，不调用 API）
   * 用于已有完整 agent 信息的场景（如从列表中选择）
   * 
   * @param agent 智能体信息（至少包含 id 和 name）
   */
  function setActiveAgent(agent: { id: string; name: string; icon?: string; description?: string }) {
    const agentInfo: ActiveAgent = {
      id: agent.id,
      name: agent.name,
      icon: agent.icon,
      description: agent.description
    }
    activeAgent.value = agentInfo
    saveActiveAgentToStorage(agentInfo)
  }

  /**
   * 清除激活的智能体（清空激活状态和本地存储）
   */
  function clearActiveAgent() {
    activeAgent.value = null
    clearActiveAgentFromStorage()
  }

  /**
   * 从 storage 加载激活的智能体信息（初始化时调用）
   */
  function loadActiveAgentFromStorage() {
    const stored = getActiveAgentFromStorage()
    if (stored) {
      activeAgent.value = stored
    }
  }

  /**
   * 设置加载状态
   */
  function setLoading(loading: boolean) {
    isLoading.value = loading
  }

  return {
    // State
    activeAgent,
    isLoading,
    
    // Getters
    hasActiveAgent,
    getActiveAgentId,
    
    // Actions
    setActiveAgent,
    setActiveAgentById,
    clearActiveAgent,
    loadActiveAgentFromStorage,
    setLoading
  }
})

