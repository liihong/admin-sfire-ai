import { ResPage } from "@/api/interface/index";
import { PORT1 } from "@/api/config/servicePort";
import http from "@/api";

/**
 * @name 用户等级管理模块
 * 对接 /api/v1/admin/user-levels 接口
 */

// ============== 类型定义 ==============

export namespace UserLevel {
  // 用户等级响应
  export interface ResUserLevel {
    id: number;
    code: string;
    name: string;
    max_ip_count?: number | null;
    ip_type: string;
    daily_tokens_limit?: number | null;
    can_use_advanced_agent: boolean;
    unlimited_conversations: boolean;
    is_enabled: boolean;
    sort_order: number;
    created_at?: string;
    updated_at?: string;
  }

  // 查询参数
  export interface ReqUserLevelParams {
    pageNum?: number;
    pageSize?: number;
    code?: string;
    name?: string;
    is_enabled?: boolean;
  }

  // 创建用户等级请求
  export interface ReqUserLevelCreate {
    code: string;
    name: string;
    max_ip_count?: number | null;
    ip_type?: string;
    daily_tokens_limit?: number | null;
    can_use_advanced_agent?: boolean;
    unlimited_conversations?: boolean;
    is_enabled?: boolean;
    sort_order?: number;
  }

  // 更新用户等级请求
  export interface ReqUserLevelUpdate {
    name?: string;
    max_ip_count?: number | null;
    ip_type?: string;
    daily_tokens_limit?: number | null;
    can_use_advanced_agent?: boolean;
    unlimited_conversations?: boolean;
    is_enabled?: boolean;
    sort_order?: number;
  }
}

// ============== 接口方法 ==============

/**
 * 获取用户等级列表（分页）
 */
export const getUserLevelList = (params?: UserLevel.ReqUserLevelParams) => {
  return http.get<ResPage<UserLevel.ResUserLevel>>(PORT1 + `/user-levels`, params);
};

/**
 * 获取所有启用的用户等级（不分页，用于下拉选择）
 */
export const getAllEnabledUserLevels = () => {
  return http.get<UserLevel.ResUserLevel[]>(PORT1 + `/user-levels/all`);
};

/**
 * 获取用户等级详情
 */
export const getUserLevelDetail = (level_id: number) => {
  return http.get<UserLevel.ResUserLevel>(PORT1 + `/user-levels/${level_id}`);
};

/**
 * 创建用户等级
 */
export const createUserLevel = (params: UserLevel.ReqUserLevelCreate) => {
  return http.post<UserLevel.ResUserLevel>(PORT1 + `/user-levels`, params);
};

/**
 * 更新用户等级
 */
export const updateUserLevel = (level_id: number, params: UserLevel.ReqUserLevelUpdate) => {
  return http.put<UserLevel.ResUserLevel>(PORT1 + `/user-levels/${level_id}`, params);
};

/**
 * 删除用户等级
 */
export const deleteUserLevel = (level_id: number) => {
  return http.delete(PORT1 + `/user-levels/${level_id}`);
};



