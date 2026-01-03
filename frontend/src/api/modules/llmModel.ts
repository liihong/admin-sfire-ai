import { LLMModel, ResPage } from "@/api/interface/index";
import { PORT1 } from "@/api/config/servicePort";
import http from "@/api";

/**
 * @name 大模型管理模块
 */

// 获取大模型列表
export const getLLMModelList = (params?: LLMModel.ReqLLMModelParams) => {
  return http.get<ResPage<LLMModel.ResLLMModelList>>(PORT1 + `/llm-models`, params);
};

// 获取大模型详情
export const getLLMModelDetail = (id: number) => {
  return http.get<LLMModel.ResLLMModelList>(PORT1 + `/llm-models/${id}`);
};

// 创建大模型
export const createLLMModel = (params: LLMModel.ReqLLMModelCreate) => {
  return http.post(PORT1 + `/llm-models`, params);
};

// 更新大模型
export const updateLLMModel = (id: number, params: LLMModel.ReqLLMModelUpdate) => {
  return http.put(PORT1 + `/llm-models/${id}`, params);
};

// 删除大模型
export const deleteLLMModel = (id: number) => {
  return http.delete(PORT1 + `/llm-models/${id}`);
};

// 刷新账户余额
export const refreshLLMModelBalance = (id: number) => {
  return http.post<LLMModel.ResBalanceRefresh>(PORT1 + `/llm-models/${id}/refresh-balance`);
};

// 获取可用模型列表（供智能体编辑页使用）
export const getAvailableLLMModels = () => {
  return http.get<Array<{ id: string; name: string; model_id: string; provider: string; max_tokens: number }>>(
    PORT1 + `/llm-models/available`
  );
};

