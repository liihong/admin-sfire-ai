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
    gender: number;
    user: { detail: { age: number } };
    idCard: string;
    email: string;
    address: string;
    createTime: string;
    status: number;
    avatar: string;
    photo: any[];
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
