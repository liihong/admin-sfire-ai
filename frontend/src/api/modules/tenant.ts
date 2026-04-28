import { PORT1 } from "@/api/config/servicePort";
import http from "@/api";
import type { Tenant } from "@/api/interface/index";
import type { ResPage } from "@/api/interface/index";

/** 租户下拉（平台全量；租户管理员仅当前租户） */
export const getTenantOptionsApi = () => {
  return http.get<Tenant.ResTenantOption[]>(PORT1 + `/tenants/options`);
};

export const getTenantListApi = (params: Tenant.ReqTenantParams) => {
  return http.get<ResPage<Tenant.ResTenant>>(PORT1 + `/tenants`, params);
};

export const getTenantDetailApi = (id: number) => {
  return http.get<Tenant.ResTenant>(PORT1 + `/tenants/${id}`);
};

export const createTenantApi = (params: Tenant.ReqTenantCreate) => {
  return http.post(PORT1 + `/tenants`, params);
};

export const updateTenantApi = (id: number, params: Tenant.ReqTenantUpdate) => {
  return http.put(PORT1 + `/tenants/${id}`, params);
};
