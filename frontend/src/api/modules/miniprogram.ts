import http from "@/api";

/**
 * @name 小程序用户模块
 * 对接 /api/v1/client 接口
 */

const MP_API_PREFIX = "/v1/client";

// ============== 认证相关 ==============

/**
 * 微信扫码登录请求
 */
export interface WechatLoginRequest {
  code: string; // 微信登录 code
  phone_code?: string; // 手机号授权 code（可选）
}

/**
 * 账号密码登录请求
 */
export interface AccountLoginRequest {
  phone: string; // 手机号
  password: string; // 密码
}

/**
 * 微信登录响应
 */
export interface WechatLoginResponse {
  success: boolean;
  token: string;
  refreshToken: string;
  expiresIn: number;
  userInfo: {
    openid: string;
    nickname: string;
    avatarUrl: string;
    gender?: number;
    city?: string;
    province?: string;
    country?: string;
  };
  updated_at?: string; // 账号更新时间
  vip_expired?: boolean; // 会员是否已过期
  vip_expire_date?: string; // 会员到期日期
}

/**
 * 微信扫码登录
 */
export const wechatLoginApi = (params: WechatLoginRequest) => {
  return http.post<WechatLoginResponse>(MP_API_PREFIX + `/auth/login`, params, { loading: false });
};

/**
 * 账号密码登录
 */
export const accountLoginApi = (params: AccountLoginRequest) => {
  return http.post<WechatLoginResponse>(MP_API_PREFIX + `/auth/account/login`, params, { loading: false });
};

/**
 * 刷新Token
 */
export interface RefreshTokenResponse {
  token: string;
  refreshToken: string;
  expiresIn: number;
}

export const refreshClientTokenApi = (refreshToken: string) => {
  return http.post<RefreshTokenResponse>(MP_API_PREFIX + `/auth/refresh`, { refreshToken }, { loading: false });
};

/**
 * 获取当前用户信息
 */
export interface MPUserInfo {
  success: boolean;
  userInfo: {
    openid: string;
    nickname: string;
    avatarUrl: string;
    gender?: number;
    city?: string;
    province?: string;
    country?: string;
  };
}

export const getMPUserInfoApi = () => {
  return http.get<MPUserInfo>(MP_API_PREFIX + `/auth/user`, {}, { loading: false });
};

/**
 * 获取用户详细信息（我的页面使用）
 */
export interface MPUserDetailInfo {
  phone: string;
  avatar: string;
  nickname: string;
  power: string; // 算力余额
  partnerBalance: string; // 合伙人资产余额
  partnerStatus: string; // 合伙人状态
  expireDate?: string; // 会员到期时间 YYYY-MM-DD
}

export const getMPUserDetailInfoApi = () => {
  return http.get<MPUserDetailInfo>(MP_API_PREFIX + `/auth/user`, {}, { loading: false });
};

/**
 * 更新用户信息
 */
export interface UpdateMPUserRequest {
  nickname?: string;
  avatar?: string;
  gender?: number;
}

export const updateMPUserInfoApi = (params: UpdateMPUserRequest) => {
  return http.put<MPUserInfo>(MP_API_PREFIX + `/auth/user`, params);
};

/**
 * 修改密码请求
 */
export interface ChangePasswordRequest {
  old_password: string; // 原密码（MD5加密）
  new_password: string; // 新密码（MD5加密）
}

/**
 * 修改密码
 */
export const changePasswordApi = (params: ChangePasswordRequest) => {
  return http.post<{ success: boolean }>(MP_API_PREFIX + `/auth/user/change-password`, params);
};

// ============== 项目管理相关 ==============

/**
 * 人设配置（与后端 PersonaSettings / 小程序 persona_settings 一致）
 */
export interface PersonaSettings {
  ip_name: string;
  ip_age: string;
  ip_city: string;
  ip_industry: string;
  ip_identityTag: string;
  ip_experience: string;
  cl_mainProducts: string;
  cl_targetPopulation: string;
  cl_painPoints: string;
  cl_advantages: string;
  cl_feedback: string;
  style_tones: string;
  style_mantra: string;
  keywords: string[];
}

/** 新人设表单默认值（与小程序一致） */
export const DEFAULT_PERSONA_SETTINGS: PersonaSettings = {
  ip_name: "",
  ip_age: "",
  ip_city: "",
  ip_industry: "",
  ip_identityTag: "",
  ip_experience: "",
  cl_mainProducts: "",
  cl_targetPopulation: "",
  cl_painPoints: "",
  cl_advantages: "",
  cl_feedback: "",
  style_tones: "专业亲和",
  style_mantra: "",
  keywords: []
};

/**
 * 项目信息（人设仅在 persona_settings 中）
 */
export interface MPProject {
  id: number;
  name: string;
  industry: string;
  avatar_letter?: string;
  avatar_color?: string;
  /** 列表/详情接口应始终返回；兼容旧数据时可缺省 */
  persona_settings?: PersonaSettings;
  isActive: boolean;
  createdAt: string;
  updatedAt: string;
}

/**
 * 项目列表响应
 */
export interface MPProjectListResponse {
  success: boolean;
  projects: MPProject[];
  active_project_id?: string;
}

/**
 * 单个项目响应
 */
export interface MPProjectSingleResponse {
  success: boolean;
  project: MPProject;
}

/**
 * 创建项目请求
 */
export interface CreateMPProjectRequest {
  name: string;
  industry: string;
  persona_settings: PersonaSettings;
}

/**
 * 更新项目请求
 */
export interface UpdateMPProjectRequest {
  name?: string;
  industry?: string;
  persona_settings: PersonaSettings;
}

/**
 * 切换项目请求
 */
export interface SwitchMPProjectRequest {
  project_id: string;
}

/**
 * 获取项目列表
 */
export const getMPProjectListApi = () => {
  return http.get<MPProjectListResponse>(MP_API_PREFIX + `/projects`, {}, { loading: false });
};

/**
 * 获取项目详情
 * 返回格式：{code: number, data: MPProject, msg: string}
 */
export const getMPProjectApi = (projectId: number) => {
  return http.get<{ code: number; data: MPProject; msg: string }>(MP_API_PREFIX + `/projects/${projectId}`, {}, { loading: false });
};

/**
 * 获取当前激活的项目
 * 返回格式：{code: number, data: MPProject, msg: string}
 */
export const getMPActiveProjectApi = () => {
  return http.get<{ code: number; data: MPProject; msg: string }>(MP_API_PREFIX + `/projects/active`, {}, { loading: false });
};

/**
 * 创建项目
 */
export const createMPProjectApi = (params: CreateMPProjectRequest) => {
  return http.post<MPProjectSingleResponse>(MP_API_PREFIX + `/projects`, params);
};

/**
 * 更新项目
 */
export const updateMPProjectApi = (projectId: number, params: UpdateMPProjectRequest) => {
  return http.put<MPProjectSingleResponse>(MP_API_PREFIX + `/projects/${projectId}`, params);
};

/**
 * 删除项目
 */
export const deleteMPProjectApi = (projectId: number) => {
  return http.delete<{ success: boolean; message: string }>(MP_API_PREFIX + `/projects/${projectId}`);
};

/**
 * 切换项目
 */
export const switchMPProjectApi = (params: SwitchMPProjectRequest) => {
  return http.post<{ success: boolean; message: string; project: MPProject }>(
    MP_API_PREFIX + `/projects/switch`,
    params
  );
};

/**
 * 获取项目配置选项（行业赛道和语气风格）
 */
export interface MPProjectOptions {
  success: boolean;
  industries: Array<{ label: string; value: string }>;
  tones: Array<{ label: string; value: string }>;
}

export const getMPProjectOptionsApi = () => {
  return http.get<MPProjectOptions>(MP_API_PREFIX + `/projects/options`, {}, { loading: false });
};

// ============== 小程序码登录相关 ==============

/**
 * 生成小程序码响应
 */
export interface QrcodeGenerateResponse {
  scene_str: string;
  qrcode_url: string; // base64数据URL
}

/**
 * 检查登录状态响应
 */
export interface QrcodeStatusResponse {
  status: "waiting" | "authorized" | "expired";
  token?: string;
  refreshToken?: string;
  expiresIn?: number; // 秒数，7天=604800
  userInfo?: {
    openid: string;
    nickname: string;
    avatarUrl: string;
    gender?: number;
    city?: string;
    province?: string;
    country?: string;
  };
}

/**
 * 生成小程序码
 */
export const generateQrcodeApi = () => {
  return http.post<QrcodeGenerateResponse>(MP_API_PREFIX + `/auth/qrcode/generate`, {}, { loading: false });
};

/**
 * 检查登录状态
 */
export const checkQrcodeStatusApi = (scene_str: string) => {
  return http.get<QrcodeStatusResponse>(MP_API_PREFIX + `/auth/qrcode/status`, { scene_str }, { loading: false });
};

// ============== 智能体和内容生成相关 ==============

/**
 * 智能体信息
 */
export interface MPAgentInfo {
  type: string;
  id: number; // 统一为 number 类型
  name: string;
  icon: string;
  description: string;
  welcomeMessage?: string; // 欢迎语（数据库配置，空则使用前端默认）
}

/**
 * 智能体列表响应（统一格式）
 */
export interface MPAgentListResponse {
  code: number;
  data: {
    agents: MPAgentInfo[];
  };
  msg: string;
}

/**
 * 对话消息
 */
export interface MPChatMessage {
  role: "user" | "assistant";
  content: string;
}

/**
 * 对话请求
 */
export interface MPChatRequest {
  conversation_id?: number; // 会话ID（可选）
  project_id?: number;
  agent_type: string;
  agent_id?: number; // 智能体数据库ID（可选，用于 usage_count 统计，当 agent_type 为预设时需传）
  messages: MPChatMessage[];
  model_type?: string;
  temperature?: number;
  max_tokens?: number;
  stream?: boolean;
}

/**
 * 对话响应（非流式）
 */
export interface MPChatResponse {
  success: boolean;
  content: string;
  agent_type: string;
  model_type: string;
}

/**
 * 获取智能体列表
 * 返回格式：{code: number, data: {agents: MPAgentInfo[]}, msg: string}
 */
export const getMPAgentsApi = () => {
  return http.get<MPAgentListResponse>(MP_API_PREFIX + `/agents`, {}, { loading: false });
};

/**
 * AI内容生成（流式）
 * 使用 fetch 处理 SSE 流式响应
 */
export const generateMPContentApi = async (
  params: MPChatRequest,
  onChunk: (chunk: string) => void,
  onError?: (error: string) => void,
  onDone?: () => void,
  onConversationId?: (conversationId: number) => void
): Promise<void> => {
  const { useMPUserStore } = await import("@/stores/modules/miniprogramUser");
  const mpUserStore = useMPUserStore();
  const baseURL = import.meta.env.VITE_API_URL as string;
  const url = `${baseURL}${MP_API_PREFIX}/chat`;
  
  try {
    const response = await fetch(url, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${mpUserStore.token}`
      },
      body: JSON.stringify(params)
    });
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    const reader = response.body?.getReader();
    if (!reader) {
      throw new Error("无法获取响应流");
    }
    
    const decoder = new TextDecoder();
    let buffer = "";
    
    while (true) {
      const { done, value } = await reader.read();
      if (done) {
        if (onDone) onDone();
        break;
      }
      
      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split("\n");
      buffer = lines.pop() || "";
      
      for (const line of lines) {
        if (line.startsWith("data: ")) {
          try {
            const data = JSON.parse(line.slice(6));
            // 处理 conversation_id
            if (data.conversation_id !== undefined && onConversationId) {
              onConversationId(data.conversation_id);
            }
            // 处理内容块
            if (data.content) {
              onChunk(data.content);
            }
            // 处理完成标志
            if (data.done) {
              if (onDone) onDone();
              return;
            }
            // 处理错误
            if (data.error) {
              if (onError) onError(data.error);
              return;
            }
          } catch (e) {
            console.error("解析流式数据失败:", e);
          }
        }
      }
    }
  } catch (error: any) {
    if (onError) {
      onError(error.message || "生成失败");
    }
    throw error;
  }
};

/**
 * AI内容生成（非流式）
 */
export const generateMPContentSyncApi = (params: MPChatRequest) => {
  return http.post<MPChatResponse>(MP_API_PREFIX + `/chat`, { ...params, stream: false });
};

/**
 * 快速生成（简化接口）
 */
export const quickGenerateMPContentApi = (params: {
  content: string;
  agent_type?: string;
  project_id?: number;
  model_type?: string;
}) => {
  return http.post<MPChatResponse>(
    MP_API_PREFIX + `/chat/quick`,
    {},
    {
      params,
      loading: false
    }
  );
};

// ============== 对话会话相关 ==============

/**
 * 会话信息
 */
export interface MPConversation {
  id: number;
  user_id: number;
  agent_id?: number;
  project_id?: number;
  title: string;
  model_type: string;
  total_tokens: number;
  message_count: number;
  status: string;
  created_at: string;
  updated_at?: string;
}

/**
 * 会话消息
 */
export interface MPConversationMessage {
  id: number;
  conversation_id: number;
  role: "user" | "assistant" | "system";
  content: string;
  tokens: number;
  sequence: number;
  embedding_status: string;
  created_at: string;
}

/**
 * 会话详情（包含消息列表）
 */
export interface MPConversationDetail extends MPConversation {
  messages: MPConversationMessage[];
  agent_name?: string;
  project_name?: string;
}

/**
 * 创建会话请求
 */
export interface MPCreateConversationRequest {
  agent_id?: number;
  project_id?: number;
  title?: string;
  model_type?: string;
}

/**
 * 会话列表查询参数
 */
export interface MPConversationListParams {
  pageNum?: number;
  pageSize?: number;
  status?: string;
  agent_id?: number;
  project_id?: number;
  keyword?: string;
}

/**
 * 会话列表响应
 */
export interface MPConversationListResponse {
  list: MPConversation[];
  total: number;
  pageNum: number;
  pageSize: number;
}

/**
 * 创建新会话
 */
export const createMPConversationApi = (params: MPCreateConversationRequest) => {
  return http.post<{ code: number; data: MPConversation; msg: string }>(
    MP_API_PREFIX + `/conversations`,
    params
  );
};

/**
 * 获取会话列表
 */
export const getMPConversationListApi = (params?: MPConversationListParams) => {
  return http.get<{ code: number; data: MPConversationListResponse; msg: string }>(
    MP_API_PREFIX + `/conversations`,
    params || {}
  );
};

/**
 * 获取会话详情
 */
export const getMPConversationDetailApi = (conversationId: number) => {
  return http.get<{ code: number; data: MPConversationDetail; msg: string }>(
    MP_API_PREFIX + `/conversations/${conversationId}`,
    {}
  );
};

/**
 * 更新会话标题
 */
export const updateMPConversationTitleApi = (conversationId: number, title: string) => {
  return http.put<{ code: number; data: MPConversation; msg: string }>(
    MP_API_PREFIX + `/conversations/${conversationId}/title`,
    {},
    { params: { title } }
  );
};

/**
 * 删除会话
 */
export const deleteMPConversationApi = (conversationId: number) => {
  return http.delete<{ code: number; msg: string }>(
    MP_API_PREFIX + `/conversations/${conversationId}`,
    {}
  );
};

/**
 * 归档会话
 */
export const archiveMPConversationApi = (conversationId: number) => {
  return http.post<{ code: number; data: MPConversation; msg: string }>(
    MP_API_PREFIX + `/conversations/${conversationId}/archive`,
    {}
  );
};

// ============== 算力相关 ==============

/**
 * 算力流水记录
 */
export interface MPComputeRecord {
  id: string;
  userId: string;
  username?: string;
  type: string; // recharge, consume, refund, reward, freeze, unfreeze, etc.
  typeName: string; // 充值、消耗、退款等
  amount: number;
  beforeBalance: number;
  afterBalance: number;
  remark?: string;
  orderId?: string;
  taskId?: string;
  operatorId?: string;
  operatorName?: string;
  source: string;
  createTime: string;
}

/**
 * 算力流水列表查询参数
 */
export interface MPComputeRecordsParams {
  pageNum?: number;
  pageSize?: number;
  logType?: string; // 流水类型过滤
}

/**
 * 算力流水列表响应
 */
export interface MPComputeRecordsResponse {
  list: MPComputeRecord[];
  total: number;
  pageNum: number;
  pageSize: number;
}

/**
 * 获取算力流水列表
 */
export const getMPComputeRecordsApi = (params?: MPComputeRecordsParams) => {
  return http.get<MPComputeRecordsResponse>(
    MP_API_PREFIX + `/coin/transactions`,
    params || {}
  );
};

/**
 * 算力余额信息
 */
export interface MPCoinBalance {
  balance: number;
  frozenBalance: number;
  availableBalance: number;
}

/**
 * 获取算力余额
 */
export const getMPCoinBalanceApi = () => {
  return http.get<MPCoinBalance>(
    MP_API_PREFIX + `/coin/balance`,
    {}
  );
};

/**
 * 算力统计信息
 */
export interface MPCoinStatistics {
  balance: number;
  frozenBalance: number;
  availableBalance: number;
  totalRecharge: number;
  totalConsume: number;
  totalRefund: number;
  totalReward: number;
  totalCommission: number;
  totalAdjustment: number;
  /** 月消耗 */
  monthConsumption: number;
  /** 累计产生内容（AI 助手消息数） */
  totalContent: number;
  /** 已陪伴您 x 天 */
  withDay: number;
}

/**
 * 获取算力统计信息
 */
export const getMPCoinStatisticsApi = () => {
  return http.get<MPCoinStatistics>(
    MP_API_PREFIX + `/coin/statistics`,
    {}
  );
};

// ============== AI智能填写相关 ==============

/**
 * IP信息采集对话请求
 */
export interface IPCollectRequest {
  messages: Array<{
    role: "user" | "assistant";
    content: string;
  }>;
  step?: number;
  context?: Record<string, any>;
}

/**
 * IP信息采集对话响应
 */
export interface IPCollectResponse {
  reply: string;
  next_step?: number;
  collected_info?: Record<string, any>;
  is_complete: boolean;
}

/**
 * IP信息压缩请求
 */
export interface IPCompressRequest {
  raw_info: {
    name?: string;
    industry?: string;
    ip_experience?: string;
    style_tones?: string;
    cl_targetPopulation?: string;
    style_mantra?: string;
    keywords?: string[];
    [key: string]: any;
  };
}

/**
 * IP信息压缩响应
 */
export interface IPCompressResponse {
  compressed_info: {
    name: string;
    industry: string;
    ip_experience: string;
    style_tones: string;
    cl_targetPopulation: string;
    style_mantra: string;
    keywords: string[];
  };
}

/**
 * AI智能填写 - IP信息采集对话
 */
export const aiCollectIPInfoApi = (params: IPCollectRequest) => {
  return http.post<{ code: number; data: IPCollectResponse; msg: string }>(
    MP_API_PREFIX + `/projects/ai-collect`,
    params
  );
};

/**
 * AI智能填写 - IP信息压缩
 */
export const compressIPInfoApi = (params: IPCompressRequest) => {
  return http.post<{ code: number; data: IPCompressResponse; msg: string }>(
    MP_API_PREFIX + `/projects/ai-compress`,
    params
  );
};

