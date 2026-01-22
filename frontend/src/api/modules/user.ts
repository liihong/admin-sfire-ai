import { ResPage } from "@/api/interface/index";
import type { User } from "@/api/interface/index";
import { PORT1 } from "@/api/config/servicePort";
import http from "@/api";

/**
 * @name 用户管理模块
 * 对接 /api/v1/users 接口
 */

// 获取用户列表
export const getUserList = (params: User.ReqUserParams) => {
  return http.get<ResPage<User.ResUserList>>(PORT1 + `/users`, params);
};

// 获取用户详情
export const getUserDetail = (id: string) => {
  return http.get<User.ResUserDetail>(PORT1 + `/users/${id}`);
};

// 新增用户
export const addUser = (params: {
  username: string;
  password: string;
  phone?: string;
  nickname?: string;
  level: string; // "normal" | "member" | "partner"
  remark?: string;
  parent_id?: number;
}) => {
  return http.post(PORT1 + `/users`, params);
};

// 编辑用户
export const editUser = (params: {
  id?: string;
  username?: string;
  phone?: string;
  nickname?: string;
  level?: string; // "normal" | "member" | "partner"
  is_active?: boolean;
  remark?: string;
}) => {
  const { id, ...data } = params;
  if (!id) {
    throw new Error("用户ID不能为空");
  }
  return http.put(PORT1 + `/users/${id}`, data);
};

// 删除用户
export const deleteUser = (params: { id: string[] }) => {
  return http.delete(PORT1 + `/users/${params.id[0]}`);
};

// 切换用户状态（封禁/解封）
export const changeUserStatus = (params: { id: string; status: number }) => {
  return http.patch(PORT1 + `/users/${params.id}/status`, null, { params: { status: params.status } });
};

// 修改用户等级
export const changeUserLevel = (params: User.ReqChangeLevel) => {
  return http.post(PORT1 + `/users/change-level`, params);
};

// 充值算力
export const rechargeUserCompute = (params: User.ReqRecharge) => {
  return http.post(PORT1 + `/users/recharge`, params);
};

// 扣除算力
export const deductUserCompute = (params: User.ReqDeduct) => {
  return http.post(PORT1 + `/users/deduct`, params);
};

// 获取用户选项（状态和等级）- 统一接口
export const getUserOptions = () => {
  return http.get<{ levels: User.ResLevel[]; status: User.ResStatus[] }>(PORT1 + `/users/options`);
};

// 获取用户等级选项（从统一接口提取，保持向后兼容）
export const getUserLevelOptions = () => {
  return http.get<User.ResLevel[]>(PORT1 + `/users/options`).then(res => {
    return { data: res.data.levels };
  });
};

// 获取用户状态选项（从统一接口提取，保持向后兼容）
export const getUserStatus = () => {
  return http.get<User.ResStatus[]>(PORT1 + `/users/options`).then(res => {
    return { data: res.data.status };
  });
};

// 获取用户状态选项（别名，保持向后兼容）
export const getUserStatusOptions = getUserStatus;

// 获取用户算力消耗记录
export const getUserComputeRecords = (params: { userId: string; pageNum: number; pageSize: number }) => {
  return http.post<ResPage<User.UserActivity>>(PORT1 + `/users/compute/records`, params);
};

// 导出用户信息（统一使用此函数）
export const exportUserInfo = (params: User.ReqUserParams) => {
  return http.download(PORT1 + `/users/export`, params);
};

// 导出用户数据（别名，保持向后兼容）
export const exportUserData = exportUserInfo;

// 批量添加用户
export const BatchAddUser = (params: FormData) => {
  return http.post(PORT1 + `/users/batch`, params, {
    headers: { "Content-Type": "multipart/form-data" }
  });
};

// 获取用户部门列表
export const getUserDepartment = () => {
  return http.get<User.ResDepartment[]>(PORT1 + `/users/departments`);
};

// 重置用户密码
export const resetUserPassWord = (params: { id: string }) => {
  return http.post(PORT1 + `/users/${params.id}/reset-password`);
};

// 获取用户性别选项
export const getUserGender = () => {
  return http.get<User.ResGender[]>(PORT1 + `/users/gender/options`);
};

// 获取用户角色选项
export const getUserRole = () => {
  return http.get<User.ResRole[]>(PORT1 + `/users/roles`);
};

// 获取用户树形列表
export const getUserTreeList = (params: User.ReqUserParams) => {
  return http.get<ResPage<User.ResUserList>>(PORT1 + `/users/tree`, params);
};