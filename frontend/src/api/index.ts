import axios, { AxiosInstance, AxiosError, AxiosRequestConfig, InternalAxiosRequestConfig, AxiosResponse } from "axios";
import { showFullScreenLoading, tryHideFullScreenLoading } from "@/components/Loading/fullScreen";
import { LOGIN_URL, MP_LOGIN_URL } from "@/config";
import { ElMessage } from "element-plus";
import { ResultData } from "@/api/interface";
import { ResultEnum } from "@/enums/httpEnum";
import { checkStatus } from "./helper/checkStatus";
import { AxiosCanceler } from "./helper/axiosCancel";
import { useUserStore } from "@/stores/modules/user";
import { useMPUserStore } from "@/stores/modules/miniprogramUser";
import router from "@/routers";

export interface CustomAxiosRequestConfig extends InternalAxiosRequestConfig {
  loading?: boolean;
  cancel?: boolean;
}

const config = {
  // 默认地址请求地址，可在 .env.** 文件中修改
  baseURL: import.meta.env.VITE_API_URL as string,
  // 设置超时时间
  timeout: ResultEnum.TIMEOUT as number,
  // 跨域时候允许携带凭证
  withCredentials: true
};

const axiosCanceler = new AxiosCanceler();

// Token刷新相关变量
let isRefreshing = false;
let refreshSubscribers: ((token: string) => void)[] = [];

// 订阅token刷新完成
function subscribeTokenRefresh(cb: (token: string) => void) {
  refreshSubscribers.push(cb);
}

// 通知所有订阅者token已刷新
function onTokenRefreshed(token: string) {
  refreshSubscribers.forEach(cb => cb(token));
  refreshSubscribers = [];
}

class RequestHttp {
  service: AxiosInstance;
  public constructor(config: AxiosRequestConfig) {
    // instantiation
    this.service = axios.create(config);

    /**
     * @description 请求拦截器
     * 客户端发送请求 -> [请求拦截器] -> 服务器
     * token校验(JWT) : 接受服务器返回的 token,存储到 vuex/pinia/本地储存当中
     */
    this.service.interceptors.request.use(
      async (config: CustomAxiosRequestConfig) => {
        const userStore = useUserStore();
        const mpUserStore = useMPUserStore();

        // 判断是Admin还是Client请求
        const isClientRequest = config.url && config.url.includes("/v1/client");
        const store = isClientRequest ? mpUserStore : userStore;

        // Token自动刷新逻辑
        if (store && store.isTokenExpiringSoon && store.isTokenExpiringSoon() && store.refreshToken) {
          if (!isRefreshing) {
            isRefreshing = true;
            try {
              const success = await store.refreshToken();
              if (!success) {
                // 刷新失败，清除token并跳转登录
                store.resetUser();
                router.replace(isClientRequest ? MP_LOGIN_URL : LOGIN_URL);
                return Promise.reject("Token刷新失败");
              }
            } catch (error) {
              // 刷新异常，清除token并跳转登录
              store.resetUser();
              router.replace(isClientRequest ? MP_LOGIN_URL : LOGIN_URL);
              return Promise.reject("Token刷新异常");
            } finally {
              isRefreshing = false;
              // 通知所有订阅者token已刷新
              onTokenRefreshed(store.token);
            }
          } else {
            // 如果正在刷新，等待刷新完成
            return new Promise(resolve => {
              subscribeTokenRefresh(token => {
                if (config.headers) {
                  config.headers.Authorization = `Bearer ${token}`;
                }
                resolve(config);
              });
            });
          }
        }

        // 重复请求不需要取消，在 api 服务中通过指定的第三个参数: { cancel: false } 来控制
        if (config.cancel === undefined) config.cancel = true;
        config.cancel && axiosCanceler.addPending(config);
        // 当前请求不需要显示 loading，在 api 服务中通过指定的第三个参数: { loading: false } 来控制
        if (config.loading === undefined) config.loading = true;
        config.loading && showFullScreenLoading();

        // 根据请求 URL 判断使用哪个 store 的 token
        // 如果请求的是小程序接口（/v1/client），使用小程序用户 token
        // 否则使用 admin 用户 token
        let token = "";
        if (config.url && config.url.includes("/v1/client")) {
          // 小程序接口，使用小程序用户 token
          token = mpUserStore?.token || "";
        } else {
          // Admin 接口，使用 admin 用户 token
          token = userStore.token;
        }

        // 设置 Authorization header（Bearer Token）
        if (token && config.headers) {
          config.headers.Authorization = `Bearer ${token}`;
          config.headers["X-My-Gate-Key"] = "Huoyuan2026";
        }
        return config;
      },
      (error: AxiosError) => {
        return Promise.reject(error);
      }
    );

    /**
     * @description 响应拦截器
     *  服务器换返回信息 -> [拦截统一处理] -> 客户端JS获取到信息
     */
    this.service.interceptors.response.use(
      (response: AxiosResponse & { config: CustomAxiosRequestConfig }) => {
        const { data, config } = response;

        const userStore = useUserStore();
        const mpUserStore = useMPUserStore();

        axiosCanceler.removePending(config);
        config.loading && tryHideFullScreenLoading();
        // 登录失效
        if (data.code == ResultEnum.OVERDUE) {
          // 根据请求 URL 判断是哪个模块的 token 失效
          if (config.url && config.url.includes("/v1/client")) {
            // 小程序用户 token 失效
            if (mpUserStore) {
              mpUserStore.resetUser();
            }
            router.replace(MP_LOGIN_URL);
          } else {
          // Admin 用户 token 失效
            userStore.resetUser();
            router.replace(LOGIN_URL);
          }
          ElMessage.error(data.msg);
          return Promise.reject(data);
        }
        // 全局错误信息拦截（防止下载文件的时候返回数据流，没有 code 直接报错）
        if (data.code && data.code !== ResultEnum.SUCCESS) {
          ElMessage.error(data.msg);
          return Promise.reject(data);
        }
        // 成功请求（在页面上除非特殊情况，否则不用处理失败逻辑）
        return data;
      },
      async (error: AxiosError) => {
        const { response } = error;
        tryHideFullScreenLoading();
        // 请求超时 && 网络错误单独判断，没有 response
        if (error.message.indexOf("timeout") !== -1) ElMessage.error("请求超时！请您稍后重试");
        if (error.message.indexOf("Network Error") !== -1) ElMessage.error("网络错误！请您稍后重试");
        // 根据服务器响应的错误状态码，做不同的处理
        if (response) checkStatus(response.status);
        // 服务器结果都没有返回(可能服务器错误可能客户端断网)，断网处理:可以跳转到断网页面
        if (!window.navigator.onLine) router.replace("/500");
        return Promise.reject(error);
      }
    );
  }

  /**
   * @description 常用请求方法封装
   */
  get<T>(url: string, params?: object, _object = {}): Promise<ResultData<T>> {
    return this.service.get(url, { params, ..._object });
  }
  post<T>(url: string, params?: object | string, _object = {}): Promise<ResultData<T>> {
    return this.service.post(url, params, _object);
  }
  put<T>(url: string, params?: object, _object = {}): Promise<ResultData<T>> {
    return this.service.put(url, params, _object);
  }
  patch<T>(url: string, params?: object | string | null, _object = {}): Promise<ResultData<T>> {
    return this.service.patch(url, params || undefined, _object);
  }
  delete<T>(url: string, params?: any, _object = {}): Promise<ResultData<T>> {
    return this.service.delete(url, { params, ..._object });
  }
  download(url: string, params?: object, _object = {}): Promise<BlobPart> {
    return this.service.post(url, params, { ..._object, responseType: "blob" });
  }
}

export default new RequestHttp(config);
