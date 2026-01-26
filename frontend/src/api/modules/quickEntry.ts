import { ResPage } from "@/api/interface/index";
import { PORT1 } from "@/api/config/servicePort";
import http from "@/api";

/**
 * @name 快捷入口管理模块
 * 对接 /api/v1/admin/quick-entries 接口
 */

// ============== 类型定义 ==============

export interface QuickEntryItem {
  id: number;
  unique_key: string;
  type: "category" | "command";
  title: string;
  subtitle?: string;
  icon_class: string;
  bg_color?: string;
  action_type: "agent" | "skill" | "prompt";
  action_value: string;
  tag: "none" | "new" | "hot";
  priority: number;
  status: number; // 0-禁用, 1-启用, 2-即将上线
  created_at: string;
  updated_at?: string;
}

export interface QuickEntryParams {
  pageNum?: number;
  pageSize?: number;
  type?: "category" | "command";
  status?: number;
  tag?: "none" | "new" | "hot";
  title?: string;
}

export interface QuickEntryCreate {
  unique_key: string;
  type: "category" | "command";
  title: string;
  subtitle?: string;
  icon_class: string;
  bg_color?: string;
  action_type: "agent" | "skill" | "prompt";
  action_value: string;
  tag?: "none" | "new" | "hot";
  priority?: number;
  status?: number;
}

export interface QuickEntryUpdate {
  unique_key?: string;
  type?: "category" | "command";
  title?: string;
  subtitle?: string;
  icon_class?: string;
  bg_color?: string;
  action_type?: "agent" | "skill" | "prompt";
  action_value?: string;
  tag?: "none" | "new" | "hot";
  priority?: number;
  status?: number;
}

export interface QuickEntrySortRequest {
  items: Array<{ id: number; priority: number }>;
}

export interface QuickEntryStatusRequest {
  status: number;
}

// ============== 接口方法 ==============

/**
 * 获取快捷入口列表（分页）
 */
export const getQuickEntryList = (params?: QuickEntryParams) => {
  return http.get<ResPage<QuickEntryItem>>(PORT1 + `/quick-entries`, params);
};

/**
 * 获取快捷入口详情
 */
export const getQuickEntryDetail = (id: number) => {
  return http.get<QuickEntryItem>(PORT1 + `/quick-entries/${id}`);
};

/**
 * 创建快捷入口
 */
export const createQuickEntry = (params: QuickEntryCreate) => {
  return http.post(PORT1 + `/quick-entries`, params);
};

/**
 * 更新快捷入口
 */
export const updateQuickEntry = (id: number, params: QuickEntryUpdate) => {
  return http.put(PORT1 + `/quick-entries/${id}`, params);
};

/**
 * 删除快捷入口
 */
export const deleteQuickEntry = (id: number) => {
  return http.delete(PORT1 + `/quick-entries/${id}`);
};

/**
 * 更新快捷入口状态
 */
export const updateQuickEntryStatus = (id: number, status: number) => {
  return http.put(PORT1 + `/quick-entries/${id}/status`, { status });
};

/**
 * 批量更新快捷入口排序
 */
export const updateQuickEntrySort = (items: Array<{ id: number; priority: number }>) => {
  return http.put(PORT1 + `/quick-entries/sort`, { items });
};

