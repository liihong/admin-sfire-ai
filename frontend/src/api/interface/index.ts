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
    id: string;
    name: string;
    children?: ResDepartment[];
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
