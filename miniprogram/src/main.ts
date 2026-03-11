import { createSSRApp } from "vue";
import { createPinia } from "pinia";
import App from "./App.vue";
import uviewPlus from 'uview-plus'

export function createApp() {
  const app = createSSRApp(App);

  // 创建 Pinia 实例
  const pinia = createPinia();

  // 注册 Pinia
  app.use(pinia);

  // 注册 uview-plus
  app.use(uviewPlus);

  // 全局错误处理：防止 Vue 内部 formatComponentName/classify 在格式化错误时
  // 因 Proxy/循环引用导致 Maximum call stack size exceeded，进而引发级联崩溃
  app.config.errorHandler = (err, instance, info) => {
    try {
      const errMsg = err instanceof Error ? err.message : String(err);
      const errStack = err instanceof Error ? err.stack : '';
      console.error('[App Error]', errMsg, info, errStack?.slice(0, 500));
      // 不重新抛出，避免触发 Vue 默认 handler 的 formatComponentName 等逻辑
    } catch (_e) {
      console.error('[App Error] 错误处理失败');
    }
  };

  return {
    app,
  };
}
