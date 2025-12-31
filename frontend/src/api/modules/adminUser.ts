import { ResPage } from "@/api/interface/index";
import type { AdminUser } from "@/api/interface/index";
import { PORT1 } from "@/api/config/servicePort";
import http from "@/api";

/**
 * @name 管理员用户管理模块
 */
// 获取管理员用户列表
export const getAdminUserList = (params: AdminUser.ReqAdminUserParams) => {
  return http.get<ResPage<AdminUser.ResAdminUserList>>(PORT1 + `/admin-users`, params);
};

// 获取管理员用户详情
export const getAdminUserDetail = (userId: number) => {
  return http.get<AdminUser.ResAdminUser>(PORT1 + `/admin-users/${userId}`);
};

// 新增管理员用户
export const addAdminUser = (params: AdminUser.ReqAdminUserCreate) => {
  return http.post(PORT1 + `/admin-users`, params);
};

// 编辑管理员用户
export const editAdminUser = (userId: number, params: AdminUser.ReqAdminUserUpdate) => {
  return http.put(PORT1 + `/admin-users/${userId}`, params);
};

// 删除管理员用户
export const deleteAdminUser = (userId: number) => {
  return http.delete(PORT1 + `/admin-users/${userId}`);
};

// 修改管理员用户状态
export const changeAdminUserStatus = (userId: number, status: number) => {
  return http.patch(PORT1 + `/admin-users/${userId}/status?status=${status}`);
};

// 获取用户状态选项
export const getAdminUserStatusOptions = () => {
  return http.get(PORT1 + `/admin-users/status/options`);
};

