import http from "@/api";
import { PORT1 } from "@/api/config/servicePort";
import { ResPage } from "@/api/interface";

const ADMIN = PORT1 + "/tools/packages";
const CLIENT = "/v1/client/tools/packages";

export interface ToolPackageItem {
  id: number;
  code: string;
  name: string;
  description?: string | null;
  icon: string;
  sort_order: number;
  status: number;
  created_at?: string | null;
  updated_at?: string | null;
}

export interface ToolPackageParams {
  pageNum?: number;
  pageSize?: number;
  status?: number;
  keyword?: string;
}

export interface ToolPackageCreate {
  code: string;
  name: string;
  description?: string;
  icon?: string;
  sort_order?: number;
  status?: number;
}

export interface ToolPackageUpdate {
  code?: string;
  name?: string;
  description?: string;
  icon?: string;
  sort_order?: number;
  status?: number;
}

/** 管理端分页 */
export const getAdminToolPackageList = (params?: ToolPackageParams) => {
  return http.get<ResPage<ToolPackageItem>>(ADMIN, params);
};

export const getAdminToolPackageDetail = (id: number) => {
  return http.get<ToolPackageItem>(`${ADMIN}/${id}`);
};

export const createToolPackage = (params: ToolPackageCreate) => {
  return http.post(ADMIN, params);
};

export const updateToolPackage = (id: number, params: ToolPackageUpdate) => {
  return http.put(`${ADMIN}/${id}`, params);
};

export const deleteToolPackage = (id: number) => {
  return http.delete(`${ADMIN}/${id}`);
};

export const sortToolPackages = (items: Array<{ id: number; sort_order: number }>) => {
  return http.put(`${ADMIN}/sort/batch`, { items });
};

/** C 端：已启用列表（公开，管理端列表页也可复用展示） */
export const getClientToolPackageList = () => {
  return http.get<ToolPackageItem[]>(CLIENT);
};
