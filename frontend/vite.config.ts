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
      minify: "esbuild",
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
              // 1. 只有体积巨大的库才值得单独拆分
              if (id.includes("element-plus")) return "vendor-element";
              if (id.includes("echarts")) return "vendor-echarts";
              if (id.includes("swiper") || id.includes("gsap")) return "vendor-ui-major";

              // 2. 将 crypto-js, qs, dayjs 等所有工具类合并为一个 vendor-common
              // 这样可以确保它们内部的引用变量（如 I, xt, wt）在同一个作用域内，不会报错
              return "vendor-common";
            }
          }
        }
      }
    }
  };
});
