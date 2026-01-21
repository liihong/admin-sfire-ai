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
  app.use(uviewPlus)

  return {
    app,
  };
}
