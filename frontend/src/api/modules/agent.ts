import { Agent, ResPage } from "@/api/interface/index";
import { PORT1 } from "@/api/config/servicePort";
import http from "@/api";

/**
 * @name 智能体管理模块
 * AI Agent 配置接口
 */

// 获取智能体列表
export const getAgentList = (params?: Agent.ReqAgentParams) => {
  return http.get<ResPage<Agent.ResAgentItem>>(PORT1 + `/agents`, params);
};

// 获取智能体详情
export const getAgentDetail = (id: string) => {
  return http.get<Agent.ResAgentItem>(PORT1 + `/agents/${id}`);
};

// 创建智能体
export const createAgent = (params: Agent.ReqAgentForm) => {
  return http.post(PORT1 + `/agents`, params);
};

// 更新智能体
export const updateAgent = (params: Agent.ReqAgentForm) => {
  return http.put(PORT1 + `/agents/${params.id}`, params);
};

// 删除智能体
export const deleteAgent = (id: string) => {
  return http.delete(PORT1 + `/agents/${id}`);
};

// 修改智能体状态（上架/下架）
export const changeAgentStatus = (id: string, status: Agent.StatusType) => {
  return http.patch(PORT1 + `/agents/${id}/status`, { status });
};

// 修改智能体排序
export const updateAgentSort = (id: string, sortOrder: number) => {
  return http.patch(PORT1 + `/agents/${id}/sort`, { sortOrder });
};

// 批量修改排序
export const batchUpdateSort = (items: Array<{ id: string; sortOrder: number }>) => {
  return http.post(PORT1 + `/agents/batch-sort`, { items });
};

// 获取预设模板列表
export const getPromptTemplates = () => {
  return http.get<Agent.PromptTemplate[]>(PORT1 + `/agents/templates`);
};

// 获取可用模型列表
export const getAvailableModels = () => {
  return http.get<Array<{ id: string; name: string; maxTokens: number }>>(PORT1 + `/agents/models`);
};
