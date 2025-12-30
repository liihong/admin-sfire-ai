import { ResPage, User } from "@/api/interface/index";
import http from "@/api";

/**
 * @name 用户管理模块
 * 对接 /api/v1/users 接口
 */

// 获取用户列表
export const getUserList = (params: User.ReqUserParams) => {
  return http.get<ResPage<User.ResUserList>>(`/api/v1/users`, params);
};

// 获取用户详情
export const getUserDetail = (id: string) => {
  return http.get<User.ResUserDetail>(`/api/v1/users/${id}`);
};

// 新增用户
export const addUser = (params: Partial<User.ResUserList>) => {
  return http.post(`/api/v1/users`, params);
};

// 编辑用户
export const editUser = (params: Partial<User.ResUserList>) => {
  return http.put(`/api/v1/users/${params.id}`, params);
};

// 删除用户
export const deleteUser = (params: { id: string[] }) => {
  return http.delete(`/api/v1/users/${params.id[0]}`);
};

// 切换用户状态（封禁/解封）
export const changeUserStatus = (params: { id: string; status: number }) => {
  return http.patch(`/api/v1/users/${params.id}/status`, null, { params: { status: params.status } });
};

// 修改用户等级
export const changeUserLevel = (params: User.ReqChangeLevel) => {
  return http.post(`/api/v1/users/change-level`, params);
};

// 充值算力
export const rechargeUserCompute = (params: User.ReqRecharge) => {
  return http.post(`/api/v1/users/recharge`, params);
};

// 扣除算力
export const deductUserCompute = (params: User.ReqDeduct) => {
  return http.post(`/api/v1/users/deduct`, params);
};

// 获取用户等级选项
export const getUserLevelOptions = () => {
  return http.get<User.ResLevel[]>(`/api/v1/users/level/options`);
};

// 获取用户状态选项
export const getUserStatusOptions = () => {
  return http.get<User.ResStatus[]>(`/api/v1/users/status/options`);
};

// 导出用户数据
export const exportUserData = (params: User.ReqUserParams) => {
  return http.download(`/api/v1/users/export`, params);
};

// 获取用户算力消耗记录
export const getUserComputeRecords = (params: { userId: string; pageNum: number; pageSize: number }) => {
  return http.post<ResPage<User.UserActivity>>(`/api/v1/users/compute/records`, params);
};
