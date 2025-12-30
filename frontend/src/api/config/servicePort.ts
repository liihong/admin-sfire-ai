// 后端微服务模块前缀
// 根据日志，VITE_API_URL 被设置为 /api，所以这里应该是 /v1
// 最终 URL = baseURL(/api) + PORT1(/v1) + path(/auth/login) = /api/v1/auth/login
export const PORT1 = "/v1";
export const PORT2 = "/hooks";
