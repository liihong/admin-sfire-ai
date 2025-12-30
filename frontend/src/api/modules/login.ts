import { Login } from "@/api/interface/index";
import { PORT1 } from "@/api/config/servicePort";
import http from "@/api";

/**
 * @name 登录模块
 * 已对接真实后端 API，不再使用 Mock 数据
 */
// 用户登录
export const loginApi = (params: Login.ReqLoginForm) => {
  return http.post<Login.ResLogin>(PORT1 + `/auth/login`, params, { loading: false });
};

// 获取菜单列表（从后端动态获取）
export const getAuthMenuListApi = () => {
  return http.get<Menu.MenuOptions[]>(PORT1 + `/menu/list`, {}, { loading: false });
};

// 获取按钮权限（从后端动态获取）
export const getAuthButtonListApi = () => {
  return http.get<Login.ResAuthButtons>(PORT1 + `/auth/buttons`, {}, { loading: false });
};

// 用户退出登录
export const logoutApi = () => {
  return http.post(PORT1 + `/auth/logout`);
};
