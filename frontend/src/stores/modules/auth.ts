import { defineStore } from "pinia";
import { AuthState } from "@/stores/interface";
import { getAuthButtonListApi, getAuthMenuListApi } from "@/api/modules/login";
import { getFlatMenuList, getShowMenuList, getAllBreadcrumbList } from "@/utils";
import { ElMessage } from "element-plus";

export const useAuthStore = defineStore({
  id: "sfire-auth",
  state: (): AuthState => ({
    // 按钮权限列表
    authButtonList: {},
    // 菜单权限列表
    authMenuList: [],
    // 当前页面的 router name，用来做按钮权限筛选
    routeName: ""
  }),
  getters: {
    // 按钮权限列表
    authButtonListGet: state => state.authButtonList,
    // 菜单权限列表 ==> 这里的菜单没有经过任何处理
    authMenuListGet: state => state.authMenuList,
    // 菜单权限列表 ==> 左侧菜单栏渲染，需要剔除 isHide == true
    showMenuListGet: state => getShowMenuList(state.authMenuList),
    // 菜单权限列表 ==> 扁平化之后的一维数组菜单，主要用来添加动态路由
    flatMenuListGet: state => getFlatMenuList(state.authMenuList),
    // 递归处理后的所有面包屑导航列表
    breadcrumbListGet: state => getAllBreadcrumbList(state.authMenuList)
  },
  actions: {
    // Get AuthButtonList
    async getAuthButtonList() {
      try {
        const { data } = await getAuthButtonListApi();
        // 后端返回格式: { code: 200, data: {...}, msg: "..." }
        // axios 拦截器已经提取了 data，所以这里直接使用
        this.authButtonList = data || {};
      } catch (error) {
        console.error("获取按钮权限失败:", error);
        ElMessage.error("获取按钮权限失败");
        this.authButtonList = {};
      }
    },
    // Get AuthMenuList
    async getAuthMenuList() {
      try {
        const { data } = await getAuthMenuListApi();
        // 后端返回格式: { code: 200, data: [...], msg: "..." }
        // axios 拦截器已经提取了 data，所以这里直接使用
        this.authMenuList = Array.isArray(data) ? data : [];
      } catch (error) {
        console.error("获取菜单列表失败:", error);
        ElMessage.error("获取菜单列表失败");
        this.authMenuList = [];
        throw error; // 抛出错误，让调用方处理
      }
    },
    // Set RouteName
    async setRouteName(name: string) {
      this.routeName = name;
    }
  }
});
