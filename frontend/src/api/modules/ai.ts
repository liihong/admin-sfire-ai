import { AI, Compute } from "@/api/interface/index";
import { PORT1 } from "@/api/config/servicePort";
import http from "@/api";

/**
 * @name AI 算力模块
 */

// 发送对话请求（非流式）
export const sendChatMessage = (params: AI.ReqChatParams) => {
  return http.post<AI.ResChatCompletion>(PORT1 + `/ai/chat`, params);
};

// 获取可用模型列表
export const getModelList = () => {
  return http.get<AI.ResModelInfo[]>(PORT1 + `/ai/models`);
};

// 获取算力余额
export const getComputeBalance = () => {
  return http.get<Compute.ResBalance>(PORT1 + `/compute/balance`);
};

// 获取算力消耗记录
export const getUsageRecords = (params?: { pageNum: number; pageSize: number }) => {
  return http.get<Compute.ResUsageRecord[]>(PORT1 + `/compute/usage`, params);
};

// 获取算力套餐列表
export const getPlanList = () => {
  return http.get<Compute.ResPlanInfo[]>(PORT1 + `/compute/plans`);
};

// 充值算力
export const rechargeCompute = (params: Compute.ReqRechargeParams) => {
  return http.post(PORT1 + `/compute/recharge`, params);
};

// 获取用户等级信息
export const getUserLevel = () => {
  return http.get<Compute.ResUserLevel>(PORT1 + `/user/level`);
};

/**
 * @description 创建 SSE 流式对话连接
 * @param _params 对话参数（当前未使用，保留用于未来扩展）
 * @returns EventSource URL（需配合 useSSE hook 使用）
 */
export const getStreamChatUrl = (_params: AI.ReqChatParams): string => {
  // 使用代理路径，确保与代理配置一致
  // 代理配置：[["/api", "http://localhost:8000"]]
  // 最终URL: /api/v1/ai/chat/stream
  const baseUrl = import.meta.env.VITE_API_URL as string;
  return `${baseUrl}${PORT1}/ai/chat/stream`;
};
