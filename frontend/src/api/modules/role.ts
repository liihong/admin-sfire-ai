
import { Role } from "@/api/interface/index";
import { PORT1 } from "@/api/config/servicePort";
import http from "@/api";

/**
 * @name 角色管理模块
 */
// 获取角色列表
export const getRoleList = () => {
    return http.get<Role.ResRoleList>(PORT1 + `/roles/list`);
};

// 获取角色详情
export const getRoleDetail = (roleId: number) => {
    return http.get<Role.ResRole>(PORT1 + `/roles/${roleId}`);
};

// 新增角色
export const addRole = (params: Role.ReqRoleCreate) => {
    return http.post(PORT1 + `/roles`, params);
};

// 编辑角色
export const editRole = (roleId: number, params: Role.ReqRoleUpdate) => {
    return http.put(PORT1 + `/roles/${roleId}`, params);
};

// 删除角色
export const deleteRole = (roleId: number) => {
    return http.delete(PORT1 + `/roles/${roleId}`);
};

// 获取角色权限
export const getRolePermissions = (roleId: number) => {
    return http.get<Role.ResRolePermissions>(PORT1 + `/roles/${roleId}/permissions`);
};

// 设置角色权限
export const setRolePermissions = (roleId: number, params: Role.ReqRolePermissions) => {
    return http.put(PORT1 + `/roles/${roleId}/permissions`, params);
};
