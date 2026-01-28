import { defineStore } from "pinia";
import piniaPersistConfig from "@/stores/helper/persist";

/**
 * 可用模型类型
 * 对齐小程序端的模型类型定义
 */
export type MPModelType = "deepseek" | "doubao" | "gpt4" | "claude";

/**
 * 模型配置信息
 */
export interface MPModelConfig {
  type: MPModelType;
  name: string;
  icon: string;
  description: string;
  available: boolean;
}

/**
 * 小程序工作台 - 模型设置 Store
 * 用于记录当前选择的大模型类型，并在本地持久化
 */
export const useMPSettingsStore = defineStore({
  id: "sfire-mp-settings",
  state: () => ({
    // 当前选中的模型类型，默认与小程序保持一致
    modelType: "claude" as MPModelType
  }),
  getters: {
    /**
     * 当前模型配置
     */
    currentModel: state => {
      return MP_MODEL_LIST.find(m => m.type === state.modelType) || MP_MODEL_LIST[0];
    },
    /**
     * 可用模型列表
     */
    availableModels: () => {
      return MP_MODEL_LIST.filter(m => m.available);
    }
  },
  actions: {
    /**
     * 设置当前模型类型
     * @param type 模型类型
     */
    setModelType(type: MPModelType) {
      const model = MP_MODEL_LIST.find(m => m.type === type);
      if (model && model.available) {
        this.modelType = type;
      } else {
        console.warn(`模型 ${type} 当前不可用`);
      }
    }
  },
  // 使用 pinia 持久化，记录当前选择的模型
  persist: piniaPersistConfig("sfire-mp-settings", ["modelType"])
});

/**
 * 与小程序端保持一致的模型配置列表
 */
export const MP_MODEL_LIST: MPModelConfig[] = [
  {
    type: "deepseek",
    name: "DeepSeek",
    icon: "🧠",
    description: "深度求索，国产大模型",
    available: true
  },
  {
    type: "doubao",
    name: "豆包",
    icon: "🫛",
    description: "字节跳动火山引擎",
    available: true
  },
  {
    type: "gpt4",
    name: "GPT-4",
    icon: "🤖",
    description: "OpenAI GPT-4",
    available: false
  },
  {
    type: "claude",
    name: "Claude",
    icon: "🎭",
    description: "Anthropic Claude",
    available: true
  }
];






























