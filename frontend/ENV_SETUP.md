# 环境配置说明

## .env.development 配置

请在 `frontend` 目录下创建 `.env.development` 文件，内容如下：

```env
# 开发环境配置

# 应用标题
VITE_GLOB_APP_TITLE = SFire Admin

# 开发服务器端口
VITE_PORT = 5173

# 是否自动打开浏览器
VITE_OPEN = true

# 是否开启打包分析
VITE_REPORT = false

# 路由模式: hash | history
VITE_ROUTER_MODE = hash

# 是否开启 gzip 压缩
VITE_BUILD_COMPRESS = gzip

# 是否删除 console.log
VITE_DROP_CONSOLE = false

# 公共路径
VITE_PUBLIC_PATH = /

# 是否使用 Mock 数据（关闭，使用真实后端）
VITE_USE_MOCK = false

# API 基础路径（设置为空字符串，因为 PORT1 已经包含完整路径）
VITE_API_URL = 

# 代理配置（指向 FastAPI 后端）
# 格式: [["代理前缀", "目标地址"]]
# 注意：JSON 格式，需要转义引号
VITE_PROXY = [["/api", "http://localhost:8000"]]

# 是否开启 PWA
VITE_PWA = false

# 是否开启开发工具
VITE_DEVTOOLS = true

# 是否开启代码检查器
VITE_CODEINSPECTOR = false
```

## 重要配置说明

### 1. VITE_USE_MOCK
- 设置为 `false` 以使用真实后端 API
- 设置为 `true` 将使用 Mock 数据（已废弃）

### 2. VITE_PROXY
代理配置用于将前端请求转发到后端服务器：
- `/api` → `http://localhost:8000`（所有 `/api` 开头的请求都会代理到后端）

**注意**：如果后端运行在不同的端口，请修改 `http://localhost:8000` 为实际的后端地址。

### 3. API 路径映射

前端 API 调用路径（PORT1 = `/api/v1`，VITE_API_URL = 空字符串）：
- `baseURL + PORT1 + /auth/login` → `/api/v1/auth/login` → 代理到 `http://localhost:8000/api/v1/auth/login`
- `baseURL + PORT1 + /menu/list` → `/api/v1/menu/list` → 代理到 `http://localhost:8000/api/v1/menu/list`
- `baseURL + PORT1 + /auth/buttons` → `/api/v1/auth/buttons` → 代理到 `http://localhost:8000/api/v1/auth/buttons`

**重要**：如果出现 `/api/api/v1/...` 的错误，说明 `VITE_API_URL` 被设置为了 `/api`，请将其改为空字符串。

## 启动步骤

1. **启动后端服务**（在 `backend` 目录）：
   ```bash
   cd backend
   python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

2. **初始化数据库**（首次运行）：
   ```bash
   cd backend
   python -m scripts.init_db
   ```

3. **启动前端服务**（在 `frontend` 目录）：
   ```bash
   cd frontend
   npm install  # 或 pnpm install
   npm run dev  # 或 pnpm dev
   ```

4. **访问应用**：
   - 前端地址：http://localhost:5173
   - 后端 API 文档：http://localhost:8000/docs

## 默认登录账号

初始化脚本会创建默认管理员账号：
- 用户名：`admin`
- 密码：`admin123`

## 故障排查

### 1. 无法连接到后端
- 检查后端服务是否正常运行
- 检查 `.env.development` 中的 `VITE_PROXY` 配置是否正确
- 检查后端端口是否为 8000

### 2. 登录失败
- 检查后端 API 是否正常响应
- 检查浏览器控制台的网络请求
- 确认 Token 是否正确保存

### 3. 菜单不显示
- 检查后端 `/api/v1/menu/list` 接口是否正常返回数据
- 检查浏览器控制台是否有错误信息
- 确认数据库是否已初始化菜单数据

