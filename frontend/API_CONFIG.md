# API 调用配置说明

## 配置要求

### 1. 环境变量配置（.env.development）

```env
# API 基础路径（必须设置为 "/api"）
VITE_API_URL = /api

# 代理配置（指向 FastAPI 后端）
VITE_PROXY = [["/api", "http://localhost:8000"]]
```

### 2. API 调用规范

所有 API 模块必须统一使用 `PORT1` 前缀：

```typescript
import { PORT1 } from "@/api/config/servicePort";
import http from "@/api";

// ✅ 正确：使用 PORT1
export const getAgentList = (params) => {
  return http.get(PORT1 + `/agents`, params);
};

// ❌ 错误：直接写完整路径
export const getAgentList = (params) => {
  return http.get(`/api/v1/agents`, params);  // 会导致路径重复
};
```

### 3. URL 构建规则

- `baseURL` = `VITE_API_URL` = `/api`
- `PORT1` = `/v1`
- 最终 URL = `baseURL` + `PORT1` + `path`
- 示例：`/api` + `/v1` + `/agents` = `/api/v1/agents`

### 4. 代理工作原理

1. 前端请求：`/api/v1/agents`
2. Vite 代理拦截：匹配 `/api` 前缀
3. 转发到后端：`http://localhost:8000/api/v1/agents`
4. 后端路由：`/api/v1/agents` ✅

## 已修复的模块

- ✅ `agent.ts` - 智能体管理
- ✅ `dashboard.ts` - 数据统计
- ✅ `userManage.ts` - 用户管理
- ✅ `login.ts` - 登录认证
- ✅ `ai.ts` - AI 算力
- ✅ `user.ts` - 用户相关
- ✅ `upload.ts` - 文件上传

## 常见问题

### Q: 为什么会出现 `/api/api/v1/...` 的错误？

A: 如果 `VITE_API_URL` 设置为 `/api`，但 API 调用时直接写了 `/api/v1/...`，就会导致路径重复。
**解决方案**：统一使用 `PORT1 + /path` 的方式。

### Q: 如果 `VITE_API_URL` 设置为空字符串会怎样？

A: 如果 `VITE_API_URL = ""`，那么：
- `baseURL("") + PORT1("/v1") + /agents` = `/v1/agents`
- 代理配置只匹配 `/api` 前缀，`/v1/agents` 不会被代理 ❌
- **解决方案**：必须设置 `VITE_API_URL = "/api"`

### Q: 如何验证配置是否正确？

A: 打开浏览器开发者工具 Network 面板：
- 请求 URL 应该是：`http://localhost:9000/api/v1/agents`
- 不应该出现：`http://localhost:9000/api/api/v1/agents`（路径重复）
- 不应该出现：`http://localhost:9000/v1/agents`（缺少 /api 前缀）



