/**
 * @description: 技能组装相关接口
 * v2版本：支持技能组装模式
 */
import http from "@/api";
import { Skill, AgentV2 } from "@/api/interface";

// ========== 技能库管理 ==========

/**
 * 获取技能列表
 */
export const getSkillList = (params: {
  page?: number;
  size?: number;
  category?: string;
  status?: number;
}) => {
  return http.get<Skill.ResSkillList>("/v2/admin/skills/list", params);
};

/**
 * 获取技能分类及数量
 */
export const getSkillCategories = () => {
  return http.get<Skill.ResSkillCategory[]>("/v2/admin/skills/categories");
};

/**
 * 获取技能详情
 */
export const getSkillDetail = (id: number) => {
  return http.get<Skill.ResSkillItem>(`/v2/admin/skills/${id}`);
};

/**
 * 创建技能
 */
export const createSkill = (data: Skill.ReqSkillCreate) => {
  return http.post<Skill.ResSkillItem>("/v2/admin/skills/", data);
};

/**
 * 更新技能
 */
export const updateSkill = (id: number, data: Skill.ReqSkillUpdate) => {
  return http.put<Skill.ResSkillItem>(`/v2/admin/skills/${id}`, data);
};

/**
 * 删除技能（软删除）
 */
export const deleteSkill = (id: number) => {
  return http.delete(`/v2/admin/skills/${id}`);
};

// ========== Agent管理（v2） ==========

/**
 * 获取Agent列表
 */
export const getAgentListV2 = (params: {
  page?: number;
  size?: number;
  name?: string;
  agent_mode?: number;
  status?: number;
}) => {
  return http.get<AgentV2.ResAgentList>("/v2/admin/agents/list", params);
};

/**
 * 获取Agent详情（包含技能详情）
 */
export const getAgentDetailV2 = (id: number) => {
  return http.get<AgentV2.ResAgentItem>(`/v2/admin/agents/${id}`);
};

/**
 * 创建Agent（支持技能模式）
 */
export const createAgentV2 = (data: AgentV2.ReqAgentCreate) => {
  return http.post<AgentV2.ResAgentItem>("/v2/admin/agents/", data);
};

/**
 * 更新Agent（支持技能模式）
 */
export const updateAgentV2 = (id: number, data: AgentV2.ReqAgentUpdate) => {
  return http.put<AgentV2.ResAgentItem>(`/v2/admin/agents/${id}`, data);
};

/**
 * 删除Agent
 */
export const deleteAgentV2 = (id: number) => {
  return http.delete(`/v2/admin/agents/${id}`);
};

/**
 * 切换Agent运行模式
 */
export const switchAgentMode = (id: number, agent_mode: number) => {
  return http.post<AgentV2.ResAgentItem>(`/v2/admin/agents/${id}/mode`, undefined, { params: { agent_mode } });
};

/**
 * 预览Agent的完整Prompt
 */
export const previewPrompt = (id: number, data: AgentV2.ReqPreviewPrompt) => {
  return http.post<AgentV2.ResPreviewPrompt>(`/v2/admin/agents/${id}/preview`, data);
};

/**
 * 预览智能路由结果
 */
export const previewRouting = (id: number, data: AgentV2.ReqRoutingPreview) => {
  return http.post<AgentV2.ResRoutingPreview>(`/v2/admin/agents/${id}/routing-preview`, data);
};

// ========== Agent执行（前端用户使用） ==========

/**
 * 执行Agent（支持IP基因注入）
 */
export const executeAgent = (agentId: number, data: AgentV2.ReqAgentExecute) => {
  return http.post<AgentV2.ResAgentExecute>(`/v2/client/execution/agents/${agentId}/execute`, data);
};

/**
 * 获取项目的IP人设配置
 */
export const getProjectPersona = (projectId: number, userId: number) => {
  return http.get<any>("/v2/client/execution/projects/{projectId}/persona", {
    projectId,
    userId
  });
};

/**
 * 构建执行Prompt（仅构建，不执行LLM）
 */
export const buildExecutionPrompt = (params: {
  agent_id: number;
  user_id: number;
  project_id: number;
  input_text: string;
  enable_persona?: boolean;
}) => {
  return http.post<any>("/v2/client/execution/build-prompt", params);
};
