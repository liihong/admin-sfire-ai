import { Menu } from "@/api/interface/index";
import { PORT1 } from "@/api/config/servicePort";
import http from "@/api";

/**
 * @name 菜单管理模块
 */
// 获取菜单列表（前端路由用）
export const getMenuList = () => {
  return http.get<Menu.MenuOptions[]>(PORT1 + `/menu/list`);
};

// 获取所有菜单（管理用，树形结构）
export const getAllMenus = () => {
  return http.get<Menu.ResMenuList[]>(PORT1 + `/menu/all`);
};

// 获取菜单详情
export const getMenuDetail = (menuId: number) => {
  return http.get<Menu.ResMenuDetail>(PORT1 + `/menu/${menuId}`);
};

// 新增菜单
export const addMenu = (params: Menu.ReqMenuCreate) => {
  return http.post(PORT1 + `/menu`, params);
};

// 编辑菜单
export const editMenu = (menuId: number, params: Menu.ReqMenuUpdate) => {
  return http.put(PORT1 + `/menu/${menuId}`, params);
};

// 删除菜单
export const deleteMenu = (menuId: number) => {
  return http.delete(PORT1 + `/menu/${menuId}`);
};





















