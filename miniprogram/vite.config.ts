import { defineConfig } from "vite";
import uni from "@dcloudio/vite-plugin-uni";

// ============== API 配置 ==============
// 开发环境 API 地址
const DEV_API_URL = "https://sourcefire.cn";
// 生产环境 API 地址（部署时修改此处）
const PROD_API_URL = "https://sourcefire.cn";

// https://vitejs.dev/config/
export default defineConfig(({ mode }) => {
  const isDev = mode === "development";

  return {
    plugins: [uni()],
    define: {
      // 注入全局 API 地址常量
      __API_BASE_URL__: JSON.stringify(isDev ? DEV_API_URL : PROD_API_URL),
    },
  };
});
