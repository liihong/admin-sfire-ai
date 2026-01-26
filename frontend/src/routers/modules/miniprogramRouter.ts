import { RouteRecordRaw } from "vue-router";
import { MP_LOGIN_URL, MP_HOME_URL } from "@/config";

/**
 * 小程序用户路由配置
 * 所有路由使用 /mp 前缀
 */
export const miniprogramRouter: RouteRecordRaw[] = [
  {
    path: MP_LOGIN_URL,
    name: "mpLogin",
    component: () => import("@/views/client/login/index.vue"),
    meta: {
      title: "小程序用户登录"
    }
  },
  {
    path: "/mp",
    name: "mpLayout",
    component: () => import("@/layouts/MiniProgramLayout/index.vue"),
    redirect: MP_HOME_URL,
    children: [
      {
        path: "home",
        name: "mpHome",
        component: () => import("@/views/client/home/index.vue"),
        meta: {
          title: "首页"
        }
      },
      {
        path: "project",
        name: "mpProject",
        component: () => import("@/views/client/project/index.vue"),
        meta: {
          title: "项目管理"
        }
      },
      {
        path: "user",
        name: "mpUser",
        component: () => import("@/views/client/user/index.vue"),
        meta: {
          title: "个人中心"
        }
      },
      {
        path: "data",
        name: "mpData",
        component: () => import("@/views/client/data/index.vue"),
        meta: {
          title: "数据统计"
        }
      },
      {
        path: "workspace/:projectId",
        name: "mpWorkspace",
        component: () => import("@/views/client/workspace/index.vue"),
        meta: {
          title: "创作指挥舱",
          isFull: true
        }
      }
    ]
  }
];


