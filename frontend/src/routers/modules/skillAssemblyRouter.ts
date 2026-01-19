/**
 * 技能组装模块路由配置
 *
 * 说明：
 * 本项目使用动态路由，菜单从后端数据库加载。
 * 如果要使用技能组装功能，需要在后台管理系统的"菜单管理"中添加以下菜单项：
 *
 * ===== 菜单配置 =====
 * 1. 一级菜单：技能组装
 *    - 菜单名称：技能组装
 *    - 菜单类型：目录
 *    - 路由路径：/skill-assembly
 *    - 组件路径：(留空)
 *    - 图标：setting
 *    - 排序：根据需要设置
 *    - 状态：启用
 *
 * 2. 二级菜单1：技能库管理
 *    - 父级菜单：技能组装
 *    - 菜单名称：技能库管理
 *    - 菜单类型：菜单
 *    - 路由路径：/skill-assembly/library
 *    - 组件路径：/skill-assembly/SkillLibrary
 *    - 图标：list
 *    - 权限标识：skill:library:view
 *    - 排序：1
 *    - 状态：启用
 *
 * 3. 二级菜单2：Agent构建器
 *    - 父级菜单：技能组装
 *    - 菜单名称：Agent构建器
 *    - 菜单类型：菜单
 *    - 路由路径：/skill-assembly/builder
 *    - 组件路径：/skill-assembly/AgentBuilder
 *    - 图标：plus
 *    - 权限标识：skill:agent:view
 *    - 排序：2
 *    - 状态：启用
 *
 * ===== 按钮权限配置（可选） =====
 * 在"技能库管理"菜单下添加按钮权限：
 * - 新增技能：skill:library:create
 * - 编辑技能：skill:library:update
 * - 删除技能：skill:library:delete
 *
 * 在"Agent构建器"菜单下添加按钮权限：
 * - 创建Agent：skill:agent:create
 * - 编辑Agent：skill:agent:update
 * - 删除Agent：skill:agent:delete
 * - 预览Prompt：skill:agent:preview
 *
 * ===== 数据库SQL示例 =====
 * 如果需要手动添加菜单，可以执行以下SQL：
 *
 * -- 一级菜单：技能组装
 * INSERT INTO menu (name, title, path, component, icon, type, sort, status)
 * VALUES ('skillAssembly', '技能组装', '/skill-assembly', NULL, 'setting', 0, 100, 1);
 *
 * -- 获取刚插入的菜单ID（假设为 @parent_id）
 * SET @parent_id = LAST_INSERT_ID();
 *
 * -- 二级菜单1：技能库管理
 * INSERT INTO menu (name, title, path, component, icon, type, sort, status, parent_id)
 * VALUES ('skillLibrary', '技能库管理', '/skill-assembly/library', '/skill-assembly/SkillLibrary', 'list', 1, 1, 1, @parent_id);
 *
 * -- 二级菜单2：Agent构建器
 * INSERT INTO menu (name, title, path, component, icon, type, sort, status, parent_id)
 * VALUES ('agentBuilder', 'Agent构建器', '/skill-assembly/builder', '/skill-assembly/AgentBuilder', 'plus', 1, 2, 1, @parent_id);
 */

import { RouteRecordRaw } from "vue-router";

export const skillAssemblyRouter: RouteRecordRaw[] = [
  {
    path: "/skill-assembly",
    name: "SkillAssembly",
    redirect: "/skill-assembly/library",
    meta: {
      title: "技能组装",
      icon: "Setting"
    }
  },
  {
    path: "/skill-assembly/library",
    name: "SkillLibrary",
    component: () => import("@/views/skill-assembly/SkillLibrary.vue"),
    meta: {
      title: "技能库管理",
      icon: "List"
    }
  },
  {
    path: "/skill-assembly/builder",
    name: "AgentBuilder",
    component: () => import("@/views/skill-assembly/AgentBuilder.vue"),
    meta: {
      title: "Agent构建器",
      icon: "Plus"
    }
  },
  {
    path: "/skill-assembly/builder/:id",
    name: "AgentBuilderEdit",
    component: () => import("@/views/skill-assembly/AgentBuilder.vue"),
    meta: {
      title: "编辑Agent",
      icon: "Edit",
      activeMenu: "/skill-assembly/builder"
    }
  }
];

export default skillAssemblyRouter;
