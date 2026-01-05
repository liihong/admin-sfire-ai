import { createSSRApp } from "vue";
import { createPinia } from "pinia";
import App from "./App.vue";

export function createApp() {
  const app = createSSRApp(App);
  
  // 创建 Pinia 实例
  const pinia = createPinia();
  
  // 注册 Pinia
  app.use(pinia);
  
  return {
    app,
  };
}
