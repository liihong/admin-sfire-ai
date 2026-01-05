// 后端微服务模块前缀
// 配置说明：
// - VITE_API_URL 应设置为 "/api"（作为 baseURL）
// - PORT1 = "/v1"（API版本前缀）
// - 最终 URL = baseURL(/api) + PORT1(/v1) + path(/auth/login) = /api/v1/auth/login
// - 代理配置：[["/api", "http://localhost:8000"]] 会将 /api 开头的请求代理到后端
export const PORT1 = "/v1/admin";
export const PORT2 = "/hooks";
