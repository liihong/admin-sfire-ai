import { defineConfig, loadEnv, ConfigEnv, UserConfig } from "vite";
import { resolve } from "path";
import { wrapperEnv } from "./build/getEnv";
import { createProxy } from "./build/proxy";
import { createVitePlugins } from "./build/plugins";
import pkg from "./package.json";
import dayjs from "dayjs";
import AutoImport from "unplugin-auto-import/vite";
import Components from "unplugin-vue-components/vite";
import { ElementPlusResolver } from "unplugin-vue-components/resolvers";

const { dependencies, devDependencies, name, version } = pkg;
const __APP_INFO__ = {
  pkg: { dependencies, devDependencies, name, version },
  lastBuildTime: dayjs().format("YYYY-MM-DD HH:mm:ss")
};

// @see: https://vitejs.dev/config/
export default defineConfig(({ mode }: ConfigEnv): UserConfig => {
  const root = process.cwd();
  const env = loadEnv(mode, root);
  const viteEnv = wrapperEnv(env);

  return {
    base: viteEnv.VITE_PUBLIC_PATH,
    root,
    resolve: {
      alias: {
        "@": resolve(__dirname, "./src"),
        "vue-i18n": "vue-i18n/dist/vue-i18n.cjs.js"
      }
    },
    define: {
      __APP_INFO__: JSON.stringify(__APP_INFO__)
    },
    css: {
      preprocessorOptions: {
        scss: {
          // 👇 添加这一行配置
          api: "modern-compiler",

          additionalData: `@use "@/styles/var.scss" as *;`
        }
      }
    },
    server: {
      host: "0.0.0.0",
      port: viteEnv.VITE_PORT,
      open: false,
      cors: true,
      // Load proxy configuration from .env.development
      proxy: createProxy(viteEnv.VITE_PROXY)
    },
    plugins: [
      ...createVitePlugins(viteEnv),
      // Element Plus 按需引入
      AutoImport({
        resolvers: [ElementPlusResolver()]
      }),
      Components({
        resolvers: [ElementPlusResolver()]
      })
    ],
    esbuild: {
      pure: viteEnv.VITE_DROP_CONSOLE ? ["console.log", "debugger"] : []
    },
    build: {
      outDir: "dist",
      minify: "terser",
      terserOptions: {
        compress: {
          // 生产环境移除 console
          drop_console: viteEnv.VITE_DROP_CONSOLE,
          drop_debugger: true,
          // 移除无用代码
          pure_funcs: viteEnv.VITE_DROP_CONSOLE ? ["console.log"] : []
        },
        format: {
          // 移除注释
          comments: false
        }
      },
      sourcemap: false,
      // 禁用 gzip 压缩大小报告，可略微减少打包时间
      reportCompressedSize: false,
      // 规定触发警告的 chunk 大小 (降低到 500KB)
      chunkSizeWarningLimit: 500,
      rollupOptions: {
        output: {
          // Static resource classification and packaging
          chunkFileNames: "assets/js/[name]-[hash].js",
          entryFileNames: "assets/js/[name]-[hash].js",
          assetFileNames: "assets/[ext]/[name]-[hash].[ext]",
          // 手动代码分割策略
          manualChunks: (id: string) => {
            // 1. 将 node_modules 中的包按类型分离
            if (id.includes("node_modules")) {
              // Vue 核心 (进一步拆分)
              if (id.includes("vue")) {
                // vue 核心单独
                if (id.includes("vue/runtime") || id.includes("vue/dist/vue.runtime")) {
                  return "vendor-vue-runtime";
                }
                // @vue/* 相关
                if (id.includes("@vue")) {
                  return "vendor-vue-lib";
                }
                return "vendor-vue-core";
              }
              // Element Plus 相关 (进一步拆分)
              if (id.includes("element-plus") || id.includes("@element-plus")) {
                // 图标库单独拆分
                if (id.includes("@element-plus/icons-vue")) {
                  return "vendor-element-icons";
                }
                return "vendor-element";
              }
              // ECharts 图表库 (进一步拆分)
              if (id.includes("echarts")) {
                // echarts 核心和组件
                if (id.includes("echarts/core") || id.includes("echarts/charts") || id.includes("echarts/components")) {
                  return "vendor-echarts-core";
                }
                // echarts-liquidfill 水球图插件
                if (id.includes("echarts-liquidfill")) {
                  return "vendor-echarts-liquidfill";
                }
                return "vendor-echarts";
              }
              // GSAP 动画库 (单独拆分)
              if (id.includes("gsap")) {
                return "vendor-gsap";
              }
              // 路由相关
              if (id.includes("vue-router")) {
                return "vendor-router";
              }
              // 状态管理
              if (id.includes("pinia")) {
                return "vendor-pinia";
              }
              // Swiper 轮播库 (单独拆分)
              if (id.includes("swiper")) {
                return "vendor-swiper";
              }
              // 其他 UI 组件工具库
              if (id.includes("sortablejs") || id.includes("driver.js") || id.includes("screenfull")) {
                return "vendor-ui-utils";
              }
              // axios 网络库
              if (id.includes("axios")) {
                return "vendor-axios";
              }
              // 工具库 (dayjs, js-md5, qs 等)
              if (id.includes("dayjs") || id.includes("js-md5") || id.includes("qs") || id.includes("mitt")) {
                return "vendor-utils";
              }
              // 其他 node_modules 包
              return "vendor";
            }
          }
        }
      }
    }
  };
});
