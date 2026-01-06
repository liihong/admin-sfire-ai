import { createRouter, createWebHashHistory, createWebHistory } from "vue-router";
import { useUserStore } from "@/stores/modules/user";
import { useAuthStore } from "@/stores/modules/auth";
import { useMPUserStore } from "@/stores/modules/miniprogramUser";
import { LOGIN_URL, MP_LOGIN_URL, ROUTER_WHITE_LIST } from "@/config";
import { initDynamicRouter } from "@/routers/modules/dynamicRouter";
import { staticRouter, errorRouter } from "@/routers/modules/staticRouter";
import NProgress from "@/config/nprogress";

const mode = import.meta.env.VITE_ROUTER_MODE;

const routerMode = {
  hash: () => createWebHashHistory(),
  history: () => createWebHistory()
};

/**
 * @description 📚 路由参数配置简介
 * @param path ==> 路由菜单访问路径
 * @param name ==> 路由 name (对应页面组件 name, 可用作 KeepAlive 缓存标识 && 按钮权限筛选)
 * @param redirect ==> 路由重定向地址
 * @param component ==> 视图文件路径
 * @param meta ==> 路由菜单元信息
 * @param meta.icon ==> 菜单和面包屑对应的图标
 * @param meta.title ==> 路由标题 (用作 document.title || 菜单的名称)
 * @param meta.activeMenu ==> 当前路由为详情页时，需要高亮的菜单
 * @param meta.isLink ==> 路由外链时填写的访问地址
 * @param meta.isHide ==> 是否在菜单中隐藏 (通常列表详情页需要隐藏)
 * @param meta.isFull ==> 菜单是否全屏 (示例：数据大屏页面)
 * @param meta.isAffix ==> 菜单是否固定在标签页中 (首页通常是固定项)
 * @param meta.isKeepAlive ==> 当前路由是否缓存
 * */
const router = createRouter({
  history: routerMode[mode](),
  routes: [...staticRouter, ...errorRouter],
  strict: false,
  scrollBehavior: () => ({ left: 0, top: 0 })
});

// Hash 路由模式下的路径修复：如果 URL 路径包含 /mp/，但 hash 为空，则重定向到正确的 hash 路由
if (mode === "hash") {
  // 在应用启动时检查并修复路径
  const currentPath = window.location.pathname;
  const currentHash = window.location.hash;

  // 如果路径包含 /mp/ 但 hash 为空或不是以 /mp/ 开头，需要修复
  if (currentPath.includes("/mp/") && (!currentHash || !currentHash.startsWith("#/mp/"))) {
    // 提取路径中的 /mp/ 部分
    const mpPathMatch = currentPath.match(/\/mp\/.*/);
    if (mpPathMatch) {
      const targetPath = mpPathMatch[0];
      // 重定向到正确的 hash 路由
      window.location.replace(`/#${targetPath}`);
    }
  }
}

/**
 * @description 路由拦截 beforeEach
 * */
router.beforeEach(async (to, from, next) => {
  const userStore = useUserStore();
  const authStore = useAuthStore();
  const mpUserStore = useMPUserStore();

  // 1.NProgress 开始
  NProgress.start();

  // 2.动态设置标题
  const title = import.meta.env.VITE_GLOB_APP_TITLE;
  document.title = to.meta.title ? `${to.meta.title} - ${title}` : title;

  // 判断是否为小程序用户路由
  const isMPRoute = to.path.startsWith("/mp");

  // 3.小程序用户路由处理
  if (isMPRoute) {
    // 3.1 判断是访问小程序登录页
    if (to.path.toLocaleLowerCase() === MP_LOGIN_URL) {
      if (mpUserStore.token) {
        // 确保重定向到 MP 路由，如果 from.fullPath 不是 MP 路由，则使用默认的 /mp/home
        let redirectPath = "/mp/home";
        if (from.fullPath && from.fullPath.startsWith("/mp")) {
          redirectPath = from.fullPath;
        }
        return next(redirectPath);
      }
      return next();
    }

    // 3.2 判断访问页面是否在路由白名单地址中，如果存在直接放行
    if (ROUTER_WHITE_LIST.includes(to.path)) return next();

    // 3.3 判断是否有小程序用户 Token，没有重定向到小程序登录页
    if (!mpUserStore.token) {
      return next({ path: MP_LOGIN_URL, replace: true });
    }

    // 3.4 小程序用户路由不需要菜单权限检查，直接放行
    return next();
  }

  // 4.Admin 路由处理（原有逻辑）
  // 4.1 判断是访问登陆页，有 Token 就在当前页面，没有 Token 重置路由到登陆页
  if (to.path.toLocaleLowerCase() === LOGIN_URL) {
    if (userStore.token) return next(from.fullPath);
    resetRouter();
    return next();
  }

  // 4.2 判断访问页面是否在路由白名单地址(静态路由)中，如果存在直接放行
  if (ROUTER_WHITE_LIST.includes(to.path)) return next();

  // 4.3 判断是否有 Token，没有重定向到 login 页面
  if (!userStore.token) {
    return next({ path: LOGIN_URL, replace: true });
  }

  // 4.4 如果没有菜单列表，就重新请求菜单列表并添加动态路由
  if (!authStore.authMenuListGet.length) {
    await initDynamicRouter();
    return next({ ...to, replace: true });
  }

  // 4.5 存储 routerName 做按钮权限筛选
  authStore.setRouteName(to.name as string);

  // 4.6 正常访问页面
  next();
});

/**
 * @description 重置路由
 * */
export const resetRouter = () => {
  const authStore = useAuthStore();
  authStore.flatMenuListGet.forEach(route => {
    const { name } = route;
    if (name && router.hasRoute(name)) router.removeRoute(name);
  });
};

/**
 * @description 路由跳转错误
 * */
router.onError(error => {
  NProgress.done();
  console.warn("路由错误", error.message);
});

/**
 * @description 路由跳转结束
 * */
router.afterEach(() => {
  NProgress.done();
});

export default router;
