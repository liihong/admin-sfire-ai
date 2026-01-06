import { defineStore } from "pinia";
import piniaPersistConfig from "@/stores/helper/persist";
import type { MPProject } from "@/api/modules/miniprogram";

/**
 * 智能体信息
 */
export interface AgentInfo {
  type: string;
  id: string;
  name: string;
  icon: string;
  description: string;
}

/**
 * 生成内容版本
 */
export interface ContentVersion {
  id: string;
  content: string;
  createdAt: number;
  agentId: string;
  agentName: string;
}

/**
 * IP Creation Store 状态
 */
interface IPCreationState {
  // 当前激活的IP（项目）
  activeProject: MPProject | null;
  // 当前选中的智能体
  selectedAgent: AgentInfo | null;
  // 生成的内容版本列表
  contentVersions: ContentVersion[];
  // 当前查看的版本ID
  currentVersionId: string | null;
  // 是否正在生成
  isGenerating: boolean;
  // 当前生成的内容（流式输出中）
  currentContent: string;
  // 对话历史（用于多轮对话）
  conversationHistory: Array<{ role: "user" | "assistant"; content: string }>;
}

export const useIPCreationStore = defineStore({
  id: "sfire-ip-creation",
  state: (): IPCreationState => ({
    activeProject: null,
    selectedAgent: null,
    contentVersions: [],
    currentVersionId: null,
    isGenerating: false,
    currentContent: "",
    conversationHistory: []
  }),
  getters: {
    // 当前版本内容
    currentVersion: state => {
      if (!state.currentVersionId) return null;
      return state.contentVersions.find(v => v.id === state.currentVersionId) || null;
    },
    // 是否有内容版本
    hasVersions: state => state.contentVersions.length > 0
  },
  actions: {
    // 设置激活的项目
    setActiveProject(project: MPProject | null) {
      this.activeProject = project;
      // 切换项目时清空内容
      if (project) {
        this.clearContent();
      }
    },
    // 设置选中的智能体
    setSelectedAgent(agent: AgentInfo | null) {
      this.selectedAgent = agent;
      // 切换智能体时清空当前内容（但保留版本历史）
      this.currentContent = "";
      this.isGenerating = false;
    },
    // 添加内容版本
    addContentVersion(content: string, agentId: string, agentName: string) {
      const version: ContentVersion = {
        id: `v${Date.now()}`,
        content,
        createdAt: Date.now(),
        agentId,
        agentName
      };
      this.contentVersions.push(version);
      this.currentVersionId = version.id;
      this.currentContent = content;
      return version.id;
    },
    // 设置当前版本
    setCurrentVersion(versionId: string) {
      this.currentVersionId = versionId;
      const version = this.contentVersions.find(v => v.id === versionId);
      if (version) {
        this.currentContent = version.content;
      }
    },
    // 删除版本
    deleteVersion(versionId: string) {
      const index = this.contentVersions.findIndex(v => v.id === versionId);
      if (index > -1) {
        this.contentVersions.splice(index, 1);
        // 如果删除的是当前版本，切换到最后一个版本
        if (this.currentVersionId === versionId) {
          if (this.contentVersions.length > 0) {
            this.setCurrentVersion(this.contentVersions[this.contentVersions.length - 1].id);
          } else {
            this.currentVersionId = null;
            this.currentContent = "";
          }
        }
      }
    },
    // 更新当前内容（流式输出）
    updateCurrentContent(content: string) {
      this.currentContent = content;
    },
    // 设置生成状态
    setGenerating(isGenerating: boolean) {
      this.isGenerating = isGenerating;
    },
    // 添加对话消息
    addMessage(role: "user" | "assistant", content: string) {
      this.conversationHistory.push({ role, content });
      // 限制历史记录数量（保留最近20条）
      if (this.conversationHistory.length > 20) {
        this.conversationHistory = this.conversationHistory.slice(-20);
      }
    },
    // 清空对话历史
    clearConversation() {
      this.conversationHistory = [];
    },
    // 清空所有内容
    clearContent() {
      this.contentVersions = [];
      this.currentVersionId = null;
      this.currentContent = "";
      this.isGenerating = false;
      this.conversationHistory = [];
    },
    // 重置状态（切换IP时使用）
    reset() {
      this.selectedAgent = null;
      this.clearContent();
    }
  },
  persist: piniaPersistConfig("sfire-ip-creation", ["activeProject", "contentVersions", "currentVersionId"])
});


