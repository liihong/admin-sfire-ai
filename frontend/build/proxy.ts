import type { ProxyOptions } from "vite";

type ProxyItem = [string, string];

type ProxyList = ProxyItem[];

type ProxyTargetList = Record<string, ProxyOptions>;

/**
 * 创建代理，用于解析 .env.development 代理配置
 * @param list
 */
export function createProxy(list: ProxyList = []) {
  const ret: ProxyTargetList = {};

  if (!list || list.length === 0) {
    console.warn("[WARNING] VITE_PROXY is empty or not configured! Requests will not be proxied.");
    return ret;
  }

  console.log("[PROXY] Configured proxies:", list);

  for (const [prefix, target] of list) {
    const httpsRE = /^https:\/\//;
    const isHttps = httpsRE.test(target);

    // https://github.com/http-party/node-http-proxy#options
    ret[prefix] = {
      target: target,
      changeOrigin: true,
      ws: true,
      // 不移除 /api 前缀，因为后端路由包含 /api/v1
      rewrite: path => path,
      // https is require secure=false
      ...(isHttps ? { secure: false } : {})
    };
    console.log(`[PROXY] ${prefix} -> ${target}`);
  }

  return ret;
}
