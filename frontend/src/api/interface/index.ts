// 请求响应参数（不包含data）
export interface Result {
  code: string;
  msg: string;
}

// 请求响应参数（包含data）
export interface ResultData<T = any> extends Result {
  data: T;
}

// 分页响应参数
export interface ResPage<T> {
  list: T[];
  pageNum: number;
  pageSize: number;
  total: number;
}

// 分页请求参数
export interface ReqPage {
  pageNum: number;
  pageSize: number;
}

// 文件上传模块
export namespace Upload {
  export interface ResFileUrl {
    fileUrl: string;
  }
}

// 登录模块
export namespace Login {
  export interface ReqLoginForm {
    username: string;
    password: string;
  }
  export interface ResLogin {
    access_token: string;
    refresh_token: string;
    expires_in: number;
  }
  export interface ResRefreshToken {
    access_token: string;
    refresh_token: string;
    expires_in: number;
  }
  export interface ResAuthButtons {
    [key: string]: string[];
  }
}

// 用户管理模块
export namespace User {
  export interface ReqUserParams extends ReqPage {
    username: string;
    gender: number;
    idCard: string;
    email: string;
    address: string;
    createTime: string[];
    status: number;
  }
  export interface ResUserList {
    id: string;
    username: string;
    gender?: number;
    user?: { detail: { age: number } };
    idCard?: string;
    email?: string;
    address?: string;
    createTime: string;
    lastLoginTime?: string; // 最后登录时间（对应数据库 updated_at 字段）
    status: number;
    avatar?: string;
    photo?: any[];
    phone?: string;
    nickname?: string;
    level?: LevelType | "normal" | "member" | "partner"; // 保留兼容旧字段
    levelCode?: string; // 新增：等级代码（normal/vip/svip/max）
    levelName?: string; // 新增：等级名称（中文）
    role?: string; // 角色：user/admin
    inviteCode?: string; // 邀请码
    inviterId?: string; // 邀请人ID
    inviterName?: string; // 邀请人名称
    remark?: string;
    computePower?: {
      balance: number;
      frozen: number;
      totalConsumed: number;
      totalRecharged: number;
      lastRechargeTime?: string;
    };
    password?: string;
    children?: ResUserList[];
  }
  export interface ResStatus {
    userLabel: string;
    userValue: number;
  }
  export interface ResGender {
    genderLabel: string;
    genderValue: number;
  }
  export interface ResDepartment {
    id: string;
    name: string;
    children?: ResDepartment[];
  }
  export interface ResRole {
    id: string;
    name: string;
    children?: ResDepartment[];
  }

  // 用户等级类型
  export type LevelType = 0 | 1 | 2; // 0-普通, 1-会员, 2-合伙人

  // 用户详情响应
  export interface ResUserDetail {
    id: string;
    username: string;
    phone?: string;
    nickname?: string;
    avatar?: string;
    level: LevelType;
    computePower: {
      balance: number;
      frozen: number;
      totalConsumed: number;
      totalRecharged: number;
      lastRechargeTime?: string;
    };
    role: string;
    inviteCode?: string;
    inviterId?: string;
    inviterName?: string;
    createTime: string;
    lastLoginTime?: string;
    status: number;
    remark?: string;
  }

  // 修改用户等级请求
  export interface ReqChangeLevel {
    userId: string;
    level: "normal" | "member" | "partner";
    remark?: string;
  }

  // 充值算力请求
  export interface ReqRecharge {
    userId: string;
    amount: number;
    remark?: string;
  }

  // 扣除算力请求
  export interface ReqDeduct {
    userId: string;
    amount: number;
    reason: string;
  }

  // 用户等级选项响应
  export interface ResLevel {
    label: string;
    value: string; // 等级代码（normal/vip/svip/max）
    code?: string; // 等级代码（与value相同）
    color?: string; // 等级颜色
    level?: LevelType; // 兼容旧字段
  }

  // 用户算力活动记录
  export interface UserActivity {
    id: string;
    userId: string;
    username?: string;
    type: string;
    typeName: string;
    amount: number;
    beforeBalance: number;
    afterBalance: number;
    remark?: string;
    orderId?: string;
    taskId?: string;
    operatorId?: string;
    operatorName?: string;
    source?: string;
    createTime: string;
  }
}

// 菜单管理模块
export namespace Menu {
  // 菜单列表项（树形结构，用于管理后台）
  export interface ResMenuList {
    id: number;
    parentId: number | null;
    name: string;
    path: string;
    component: string | null;
    redirect: string | null;
    sortOrder: number;
    icon: string;
    title: string;
    isLink: string;
    isHide: boolean;
    isFull: boolean;
    isAffix: boolean;
    isKeepAlive: boolean;
    isEnabled: boolean;
    createdAt?: string | null;
    updatedAt?: string | null;
    children?: ResMenuList[];
  }

  // 菜单详情
  export interface ResMenuDetail {
    id: number;
    parentId: number | null;
    name: string;
    path: string;
    component: string | null;
    redirect: string | null;
    sortOrder: number;
    icon: string;
    title: string;
    isLink: string;
    isHide: boolean;
    isFull: boolean;
    isAffix: boolean;
    isKeepAlive: boolean;
    activeMenu: string | null;
    perms: string | null;
    requiredLevel: string | null;
    requiredComputePower: number | null;
    consumeComputePower: number | null;
    isEnabled: boolean;
  }

  // 创建菜单请求参数
  export interface ReqMenuCreate {
    parent_id?: number | null;
    name: string;
    path: string;
    component?: string | null;
    redirect?: string | null;
    sort_order?: number;
    icon?: string;
    title: string;
    is_link?: string | null;
    is_hide?: boolean;
    is_full?: boolean;
    is_affix?: boolean;
    is_keep_alive?: boolean;
    active_menu?: string | null;
    perms?: string | null;
    required_level?: string | null;
    required_compute_power?: number | null;
    consume_compute_power?: number | null;
    is_enabled?: boolean;
  }

  // 更新菜单请求参数
  export interface ReqMenuUpdate {
    parent_id?: number | null;
    name?: string;
    path?: string;
    component?: string | null;
    redirect?: string | null;
    sort_order?: number;
    icon?: string;
    title?: string;
    is_link?: string | null;
    is_hide?: boolean;
    is_full?: boolean;
    is_affix?: boolean;
    is_keep_alive?: boolean;
    active_menu?: string | null;
    perms?: string | null;
    required_level?: string | null;
    required_compute_power?: number | null;
    consume_compute_power?: number | null;
    is_enabled?: boolean;
  }

  // MenuOptions类型（与global.d.ts中的定义保持一致）
  export interface MenuOptions {
    path: string;
    name: string;
    component?: string | (() => Promise<unknown>);
    redirect?: string;
    meta: {
      icon: string;
      title: string;
      activeMenu?: string;
      isLink?: string;
      isHide: boolean;
      isFull: boolean;
      isAffix: boolean;
      isKeepAlive: boolean;
      requiredLevel?: "free" | "v1" | "v2" | "v3";
      requiredComputePower?: number;
      consumeComputePower?: number;
    };
    children?: MenuOptions[];
  }
}

// 大模型管理模块
export namespace LLMModel {
  // 提供商类型
  export type ProviderType = "openai" | "anthropic" | "deepseek";

  // 大模型查询参数
  export interface ReqLLMModelParams extends ReqPage {
    name?: string;
    provider?: ProviderType;
    is_enabled?: boolean;
  }

  // 大模型列表项
  export interface ResLLMModelList {
    id: number;
    name: string;
    model_id: string;
    provider: ProviderType;
    has_api_key: boolean;
    base_url?: string;
    is_enabled: boolean;
    total_tokens_used: number;
    balance?: number;
    balance_updated_at?: string;
    sort_order: number;
    remark?: string;
    created_at?: string;
    updated_at?: string;
  }

  // 创建大模型请求
  export interface ReqLLMModelCreate {
    name: string;
    model_id: string;
    provider: ProviderType;
    api_key?: string;
    base_url?: string;
    is_enabled?: boolean;
    sort_order?: number;
    remark?: string;
  }

  // 更新大模型请求
  export interface ReqLLMModelUpdate {
    name?: string;
    model_id?: string;
    provider?: ProviderType;
    api_key?: string;
    base_url?: string;
    is_enabled?: boolean;
    sort_order?: number;
    remark?: string;
  }

  // 余额刷新响应
  export interface ResBalanceRefresh {
    balance?: number;
    balance_updated_at?: string;
    success: boolean;
    message?: string;
  }
}

// 角色管理模块
export namespace Role {
  // 角色列表项
  export interface ResRole {
    id: number;
    name: string;
    code: string;
    description?: string;
    sort_order: number;
    user_count: number;
    created_at?: string;
    updated_at?: string;
  }

  // 角色列表响应
  export interface ResRoleList {
    list: ResRole[];
    total: number;
  }

  // 创建角色请求
  export interface ReqRoleCreate {
    name: string;
    code: string;
    description?: string;
    sort_order?: number;
  }

  // 更新角色请求
  export interface ReqRoleUpdate {
    name?: string;
    description?: string;
    sort_order?: number;
  }

  // 角色权限响应
  export interface ResRolePermissions {
    menu_ids: number[];
  }

  // 设置角色权限请求
  export interface ReqRolePermissions {
    menu_ids: number[];
  }
}

// 智能体管理模块
export namespace Agent {
  // 状态类型
  export type StatusType = 0 | 1;

  // 智能体配置参数
  export interface AgentConfig {
    temperature: number;
    maxTokens: number;
    topP?: number;
    frequencyPenalty?: number;
    presencePenalty?: number;
  }

  // 智能体列表项
  export interface ResAgentItem {
    id: string;
    name: string;
    icon: string;
    description?: string;
    systemPrompt: string;
    model: string;
    config: AgentConfig;
    sortOrder: number;
    status: StatusType;
    agentMode?: number; // 0-普通模式, 1-Skill组装模式
    skillIds?: number[]; // 技能ID数组（按顺序）
    skillVariables?: Record<number, Record<string, string>>; // 技能变量配置
    isSystem?: number; // 是否为系统自用智能体：0-否，1-是
    usageCount?: number;
    createdAt?: string;
    updatedAt?: string;
    createTime?: string;
    updateTime?: string;
  }

  // 智能体查询参数
  export interface ReqAgentParams extends ReqPage {
    name?: string;
    status?: StatusType;
  }

  // 智能体表单数据
  export interface ReqAgentForm {
    id?: string;
    name: string;
    icon: string;
    description?: string;
    systemPrompt: string;
    model: string;
    config: AgentConfig;
    sortOrder?: number;
    status: StatusType;
    agentMode?: number; // 0-普通模式, 1-Skill组装模式
    skillIds?: number[]; // 技能ID数组（按顺序）
    skillVariables?: Record<number, Record<string, string>>; // 技能变量配置
    isSystem?: number; // 是否为系统自用智能体：0-否，1-是
  }

  // 预设模板
  export interface PromptTemplate {
    id: string;
    name: string;
    content: string;
    category: string;
  }
}

// ========== v2版本：技能组装模式 ==========

// 技能库模块
export namespace Skill {
  // 技能状态
  export type StatusType = 0 | 1;

  // 技能分类
  export type CategoryType = "model" | "hook" | "rule" | "audit";

  // 技能列表项
  export interface ResSkillItem {
    id: number;
    name: string;
    category: CategoryType;
    meta_description?: string;
    content: string;
    status: StatusType;
    created_at: string;
  }

  // 技能列表响应
  export interface ResSkillList {
    list: ResSkillItem[];
    total: number;
  }

  // 创建技能请求
  export interface ReqSkillCreate {
    name: string;
    category: CategoryType;
    meta_description?: string;
    content: string;
    status?: StatusType;
  }

  // 更新技能请求
  export interface ReqSkillUpdate {
    name?: string;
    category?: CategoryType;
    meta_description?: string;
    content?: string;
    status?: StatusType;
  }

  // 技能分类响应
  export interface ResSkillCategory {
    category: string;
    count: number;
  }
}

// Agent v2模块（技能组装模式）
export namespace AgentV2 {
  // Agent模式
  export type AgentMode = 0 | 1; // 0-普通模式, 1-Skill组装模式
  export type StatusType = 0 | 1;

  // Agent配置参数
  export interface AgentConfig {
    temperature: number;
    maxTokens: number;
    topP?: number;
    frequencyPenalty?: number;
    presencePenalty?: number;
  }

  // 技能列表项
  export interface ResSkillItem {
    id: number;
    name: string;
    category: string;
    meta_description?: string;
    content: string;
    status: number;
    created_at: string;
  }

  // Agent详情响应
  export interface ResAgentItem {
    id: number;
    name: string;
    icon: string;
    description?: string;
    agent_mode: AgentMode;
    system_prompt: string;
    model: string;
    config?: AgentConfig;
    sort_order: number;
    status: StatusType;
    usage_count: number;
    skill_ids?: number[];
    skill_variables?: Record<number, Record<string, string>>;
    routing_description?: string;
    is_routing_enabled: number;
    is_system?: number; // 是否为系统自用智能体：0-否，1-是
    skills_detail?: ResSkillItem[];
    created_at: string;
    updated_at?: string;
  }

  // Agent列表响应
  export interface ResAgentList {
    list: ResAgentItem[];
    total: number;
  }

  // 创建Agent请求
  export interface ReqAgentCreate {
    name: string;
    icon: string;
    description?: string;
    agent_mode: AgentMode;
    system_prompt?: string;
    model: string;
    config?: AgentConfig;
    sort_order?: number;
    status?: StatusType;
    skill_ids?: number[];
    skill_variables?: Record<number, Record<string, string>>;
    routing_description?: string;
    is_routing_enabled?: number;
  }

  // 更新Agent请求
  export interface ReqAgentUpdate {
    name?: string;
    icon?: string;
    description?: string;
    agent_mode?: AgentMode;
    system_prompt?: string;
    model?: string;
    config?: AgentConfig;
    sort_order?: number;
    status?: StatusType;
    skill_ids?: number[];
    skill_variables?: Record<number, Record<string, string>>;
    routing_description?: string;
    is_routing_enabled?: number;
  }

  // Prompt预览请求
  export interface ReqPreviewPrompt {
    skill_ids: number[];
    skill_variables?: Record<number, Record<string, string>>;
  }

  // Prompt预览响应
  export interface ResPreviewPrompt {
    full_prompt: string;
    token_count: number;
    skills_used: Array<{
      id: number;
      name: string;
      category: string;
      order: number;
    }>;
  }

  // Agent执行请求（前端用户使用）
  export interface ReqAgentExecute {
    user_id: number;
    project_id: number;
    input_text: string;
    enable_persona?: boolean;
  }

  // Agent执行响应
  export interface ResAgentExecute {
    response: string;
    prompt_used: string;
    skills_applied: number[];
  }

  // 路由预览请求
  export interface ReqRoutingPreview {
    user_input: string;
    use_vector?: boolean;
    top_k?: number;
    threshold?: number;
  }

  // 技能路由信息
  export interface SkillRoutingInfo {
    id: number;
    name: string;
    category: string;
    similarity: number;
    meta_description?: string;
  }

  // 路由预览响应
  export interface ResRoutingPreview {
    selected_skills: SkillRoutingInfo[];
    rejected_skills: SkillRoutingInfo[];
    token_comparison: {
      full: number;
      routed: number;
      saved_percent: number;
    };
    final_prompt: string;
    routing_method: "vector" | "keywords";
  }
}

// 管理员用户模块
export namespace AdminUser {
  // 管理员用户查询参数
  export interface ReqAdminUserParams extends ReqPage {
    username?: string;
    email?: string;
    role_id?: number;
    is_active?: boolean;
  }

  // 管理员用户列表项
  export interface ResAdminUserList {
    id: number;
    username: string;
    email?: string;
    role_id?: number;
    role_name?: string;
    role_code?: string;
    is_active: boolean;
    remark?: string;
    created_at?: string;
    updated_at?: string;
  }

  // 管理员用户详情
  export interface ResAdminUser {
    id: number;
    username: string;
    email?: string;
    role_id?: number;
    role_name?: string;
    role_code?: string;
    is_active: boolean;
    remark?: string;
    created_at?: string;
    updated_at?: string;
  }

  // 创建管理员用户请求
  export interface ReqAdminUserCreate {
    username: string;
    password: string;
    email?: string;
    role_id?: number;
    remark?: string;
  }

  // 更新管理员用户请求
  export interface ReqAdminUserUpdate {
    username?: string;
    email?: string;
    password?: string;
    role_id?: number;
    is_active?: boolean;
    remark?: string;
  }
}

// AI对话模块
export namespace AI {
  // 聊天消息
  export interface ChatMessage {
    role: "system" | "user" | "assistant";
    content: string;
    timestamp?: number;
  }

  // 聊天请求参数
  export interface ReqChatParams {
    messages: ChatMessage[];
    model: string;
    temperature?: number;
    max_tokens?: number;
    top_p?: number;
    frequency_penalty?: number;
    presence_penalty?: number;
    stream?: boolean;
  }

  // 聊天完成响应
  export interface ResChatCompletion {
    id: string;
    model: string;
    message: ChatMessage;
    usage?: {
      prompt_tokens?: number;
      completion_tokens?: number;
      total_tokens?: number;
    };
    finish_reason?: string;
  }

  // 模型信息
  export interface ResModelInfo {
    id: string;
    name: string;
    model_id: string;
    provider: "openai" | "anthropic" | "deepseek";
    is_enabled: boolean;
  }
}

// 算力模块
export namespace Compute {
  // 算力余额响应
  export interface ResBalance {
    balance: number;
    frozen: number;
    totalConsumed: number;
    totalRecharged: number;
    lastRechargeTime?: string;
  }

  // 算力使用记录
  export interface ResUsageRecord {
    id: string;
    userId: string;
    type: string;
    typeName: string;
    amount: number;
    beforeBalance: number;
    afterBalance: number;
    remark?: string;
    createTime: string;
  }

  // 算力套餐信息
  export interface ResPlanInfo {
    id: string;
    name: string;
    amount: number;
    price: number;
    description?: string;
  }

  // 充值算力请求参数
  export interface ReqRechargeParams {
    planId?: string;
    amount: number;
    remark?: string;
  }

  // 用户等级信息
  export interface ResUserLevel {
    level: "normal" | "member" | "partner";
    levelName: string;
    discount: number;
    dailyLimit: number;
  }
}