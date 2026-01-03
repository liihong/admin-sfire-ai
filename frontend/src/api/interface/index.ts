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
  }
  export interface ResAuthButtons {
    [key: string]: string[];
  }
}

// AI 算力模块
export namespace AI {
  // 对话消息
  export interface Message {
    role: "user" | "assistant" | "system";
    content: string;
    timestamp?: number;
  }

  // 对话请求参数
  export interface ReqChatParams {
    messages: Message[];
    model?: string;
    temperature?: number;
    max_tokens?: number;
    stream?: boolean;
  }

  // 对话响应
  export interface ResChatCompletion {
    id: string;
    model: string;
    message: Message;
    usage: {
      prompt_tokens: number;
      completion_tokens: number;
      total_tokens: number;
    };
    finish_reason: string;
  }

  // SSE 流式响应块
  export interface ResStreamChunk {
    id: string;
    delta: {
      content?: string;
      role?: string;
    };
    finish_reason: string | null;
  }

  // 模型列表
  export interface ResModelInfo {
    id: string;
    name: string;
    description?: string;
    max_tokens: number;
    cost_per_token: number;
  }
}

// 算力模块
export namespace Compute {
  // 算力余额信息
  export interface ResBalance {
    total: number;
    used: number;
    remaining: number;
    expireTime?: string;
  }

  // 算力消耗记录
  export interface ResUsageRecord {
    id: string;
    model: string;
    tokens: number;
    cost: number;
    createTime: string;
    type: "chat" | "image" | "audio" | "video";
  }

  // 算力充值请求
  export interface ReqRechargeParams {
    amount: number;
    paymentMethod: string;
  }

  // 算力套餐
  export interface ResPlanInfo {
    id: string;
    name: string;
    tokens: number;
    price: number;
    description?: string;
    validDays: number;
  }

  // 用户等级信息
  export interface ResUserLevel {
    level: number;
    levelName: string;
    discount: number;
    dailyLimit: number;
    features: string[];
  }
}

// 用户管理模块
export namespace User {
  // 用户等级：0-普通, 1-会员, 2-合伙人
  export type LevelType = 0 | 1 | 2;

  // 算力明细
  export interface ComputePower {
    balance: number; // 当前剩余可用算力
    frozen: number; // 提现中/处理中的冻结算力
    totalConsumed: number; // 历史累计消耗
    totalRecharged: number; // 历史累计充值
    lastRechargeTime?: string; // 最后充值时间
  }

  // 用户查询参数
  export interface ReqUserParams extends ReqPage {
    username?: string;
    phone?: string;
    level?: LevelType;
    status?: number;
    createTime?: string[];
    minBalance?: number; // 最小算力余额
    maxBalance?: number; // 最大算力余额
  }

  // 用户列表项
  export interface ResUserList {
    id: string;
    username: string;
    phone: string;
    email?: string;
    avatar?: string;
    level: LevelType; // 用户等级
    computePower: ComputePower; // 算力明细
    role: string;
    inviteCode?: string; // 邀请码
    inviterId?: string; // 邀请人ID
    inviterName?: string; // 邀请人名称
    createTime: string;
    lastLoginTime?: string;
    status: number; // 1-正常, 0-封禁
  }

  // 用户详情（包含更多信息）
  export interface ResUserDetail extends ResUserList {
    inviteCount: number; // 邀请人数
    totalCommission: number; // 累计佣金
    withdrawableCommission: number; // 可提现佣金
    devices: UserDevice[]; // 登录设备
    recentActivities: UserActivity[]; // 最近活动
  }

  // 用户设备信息
  export interface UserDevice {
    deviceId: string;
    deviceType: "ios" | "android" | "web" | "miniapp";
    deviceName: string;
    lastActiveTime: string;
    ip?: string;
  }

  // 用户活动记录
  export interface UserActivity {
    id: string;
    type: "login" | "consume" | "recharge" | "withdraw";
    description: string;
    amount?: number;
    createTime: string;
  }

  // 充值请求
  export interface ReqRecharge {
    userId: string;
    amount: number;
    remark?: string;
  }

  // 扣费请求
  export interface ReqDeduct {
    userId: string;
    amount: number;
    reason: string;
  }

  // 修改等级请求
  export interface ReqChangeLevel {
    userId: string;
    level: LevelType;
    remark?: string;
  }

  // 状态选项
  export interface ResStatus {
    userLabel: string;
    userValue: number;
  }

  // 等级选项
  export interface ResLevel {
    label: string;
    value: LevelType;
    color: string;
  }

  // 部门
  export interface ResDepartment {
    id: string;
    name: string;
    children?: ResDepartment[];
  }

  // 角色
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
}

// 角色管理模块
export namespace Role {
  // 角色响应
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

  // 获取角色权限响应
  export interface ResRolePermissions {
    role_id: number;
    menu_ids: number[];
  }

  // 设置角色权限请求
  export interface ReqRolePermissions {
    menu_ids: number[];
  }
}

// 管理员用户管理模块
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
  export interface ResAdminUser extends ResAdminUserList { }

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

  // 状态选项
  export interface ResStatus {
    userLabel: string;
    userValue: number;
  }
}

// 智能体管理模块
export namespace Agent {
  // 智能体状态：0-下架, 1-上架
  export type StatusType = 0 | 1;

  // 智能体配置参数
  export interface AgentConfig {
    temperature: number; // 温度 0-2
    maxTokens: number; // 最大token数
    topP: number; // Top P 采样
    frequencyPenalty: number; // 频率惩罚
    presencePenalty: number; // 存在惩罚
  }

  // 智能体列表项
  export interface ResAgentItem {
    id: string;
    name: string;
    icon: string;
    description: string;
    systemPrompt: string;
    model: string;
    config: AgentConfig;
    sortOrder: number;
    status: StatusType;
    usageCount: number; // 使用次数
    createTime: string;
    updateTime: string;
  }

  // 智能体查询参数
  export interface ReqAgentParams {
    name?: string;
    status?: StatusType;
  }

  // 创建/更新智能体参数
  export interface ReqAgentForm {
    id?: string;
    name: string;
    icon: string;
    description: string;
    systemPrompt: string;
    model: string;
    config: AgentConfig;
    sortOrder: number;
    status: StatusType;
  }

  // 预设模板
  export interface PromptTemplate {
    id: string;
    name: string;
    content: string;
    category: string;
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

  // MenuOptions和MetaProps已在global.d.ts中定义，这里通过declare global扩展
  // 如果需要在模块中使用，可以通过类型引用：import type { MenuOptions } from "@/typings/global";
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
