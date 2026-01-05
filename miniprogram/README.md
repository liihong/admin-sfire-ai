# 🔥 火源文案 - 前端工程说明书

> AI 驱动的短视频文案创作平台前端项目

## 📋 目录

- [项目概述](#项目概述)
- [技术栈](#技术栈)
- [项目结构](#项目结构)
- [快速开始](#快速开始)
- [核心模块说明](#核心模块说明)
- [状态管理](#状态管理)
- [API 请求封装](#api-请求封装)
- [多平台适配](#多平台适配)
- [AI 模型配置](#ai-模型配置)
- [环境配置](#环境配置)
- [后期数据库扩展说明](#后期数据库扩展说明)
- [部署指南](#部署指南)

---

## 项目概述

**火源文案** 是一款面向短视频创作者的 AI 文案生成工具，支持多智能体切换、IP 人设管理、多模型对话等功能。采用 uni-app 跨平台框架开发，一套代码可同时编译到微信小程序、H5、App 等多个平台。

### 核心功能

- 🤖 **多智能体对话** - 口播文案、小红书种草、营销转化等专业智能体
- 🎭 **IP 人设管理** - 创建和管理多个 IP 项目，自定义人设配置
- 🔄 **多模型切换** - 支持 DeepSeek、豆包、Claude 等多种 AI 模型
- 📝 **文案一键生成** - 输入主题即可生成专业文案
- 📱 **跨平台支持** - 微信小程序、H5、App 一码多端

---

## 技术栈

### 核心框架

| 技术 | 版本 | 说明 |
|------|------|------|
| **uni-app** | 3.0.0-408042 | 跨平台应用开发框架 |
| **Vue 3** | 3.4.21 | 渐进式 JavaScript 框架（Composition API） |
| **TypeScript** | 4.9.4 | JavaScript 超集，提供类型安全 |
| **Vite** | 5.2.8 | 下一代前端构建工具 |

### 状态管理

| 技术 | 版本 | 说明 |
|------|------|------|
| **Pinia** | 2.3.1 | Vue 3 官方状态管理库 |
| **pinia-plugin-persistedstate** | 4.7.1 | Pinia 持久化插件 |

### UI & 样式

| 技术 | 版本 | 说明 |
|------|------|------|
| **SCSS/SASS** | 1.97.1 | CSS 预处理器 |
| **uni-ui** | - | uni-app 官方组件库（按需引入） |

### 国际化

| 技术 | 版本 | 说明 |
|------|------|------|
| **vue-i18n** | 9.1.9 | Vue 3 国际化方案（预留） |

### 开发工具

| 工具 | 说明 |
|------|------|
| **vue-tsc** | Vue 文件 TypeScript 类型检查 |
| **@dcloudio/types** | uni-app TypeScript 类型声明 |
| **微信开发者工具** | 小程序调试运行 |

---

## 项目结构

```
frontend/
├── src/
│   ├── pages/                    # 页面目录
│   │   ├── index/               # 首页（发现）
│   │   │   └── index.vue
│   │   ├── login/               # 登录模块
│   │   │   ├── index.vue        # 登录页
│   │   │   └── profile.vue      # 完善资料页
│   │   ├── agent/               # 智能体入口
│   │   │   └── index.vue
│   │   ├── copywriting/         # AI 文案生成（智能体对话）
│   │   │   └── index.vue
│   │   ├── project/             # 项目管理模块
│   │   │   ├── list.vue         # 项目列表
│   │   │   ├── create.vue       # 创建项目
│   │   │   └── dashboard.vue    # 项目控制台
│   │   └── mine/                # 个人中心
│   │       └── index.vue
│   │
│   ├── components/              # 公共组件
│   │   └── ModelSwitcher.vue    # 模型切换悬浮球
│   │
│   ├── stores/                  # Pinia 状态管理
│   │   ├── index.ts             # Store 导出入口
│   │   ├── auth.ts              # 用户认证状态
│   │   ├── project.ts           # 项目管理状态
│   │   └── settings.ts          # 全局设置状态
│   │
│   ├── utils/                   # 工具函数
│   │   └── request.ts           # 请求封装（含拦截器）
│   │
│   ├── static/                  # 静态资源
│   │   ├── logo.png
│   │   ├── default-avatar.png
│   │   └── tab/                 # TabBar 图标
│   │
│   ├── App.vue                  # 应用入口组件
│   ├── main.ts                  # 应用入口文件
│   ├── pages.json               # 页面路由配置
│   ├── manifest.json            # 应用配置
│   └── uni.scss                 # 全局样式变量
│
├── dist/                        # 编译输出目录
│   └── dev/
│       └── mp-weixin/           # 微信小程序编译产物
│
├── vite.config.ts               # Vite 配置
├── tsconfig.json                # TypeScript 配置
├── package.json                 # 项目依赖配置
└── README.md                    # 本文档
```

---

## 快速开始

### 环境要求

- **Node.js** >= 18.x
- **npm** >= 9.x 或 **pnpm** >= 8.x
- **微信开发者工具**（小程序开发）

### 安装依赖

```bash
cd frontend
npm install
```

### 开发运行

```bash
# 微信小程序
npm run dev:mp-weixin

# H5 Web
npm run dev:h5

# 其他平台
npm run dev:mp-alipay    # 支付宝小程序
npm run dev:mp-toutiao   # 抖音小程序
npm run dev:mp-qq        # QQ 小程序
```

### 生产构建

```bash
# 微信小程序
npm run build:mp-weixin

# H5 Web
npm run build:h5
```

### 微信小程序调试

1. 运行 `npm run dev:mp-weixin`
2. 打开微信开发者工具
3. 导入项目 `dist/dev/mp-weixin` 目录
4. 在开发者工具中预览调试

---

## 核心模块说明

### 1. 智能体对话模块 (`pages/copywriting`)

核心的 AI 对话页面，支持多智能体切换和实时对话。

**智能体类型：**
| 智能体 | 图标 | 说明 |
|--------|------|------|
| 高效口播文案智能体 | 🎙️ | 短视频口播文案，节奏感强 |
| 小红书种草笔记智能体 | 📕 | 小红书爆款风格，emoji 丰富 |
| 营销转化文案智能体 | 💰 | AIDA 模型，高转化率 |
| 故事叙述智能体 | 📖 | 沉浸式故事，情感共鸣 |
| 知识科普智能体 | 🎓 | 专业知识通俗化 |

**功能特性：**
- IP 档案卡片展示当前项目信息
- 智能体切换时保留对话历史
- 消息复制功能
- 清空对话（保留 IP 卡片）

### 2. 项目管理模块 (`pages/project`)

管理多个 IP 项目，每个项目可配置独立人设。

**人设配置字段：**
```typescript
interface PersonaSettings {
  tone: string              // 语气风格
  catchphrase: string       // 口头禅
  target_audience: string   // 目标受众
  benchmark_accounts: string[] // 对标账号
  content_style: string     // 内容风格
  taboos: string[]          // 内容禁忌
  keywords: string[]        // 常用关键词
  introduction: string      // IP 简介
}
```

### 3. 登录认证模块 (`pages/login`)

支持微信小程序授权登录和 Mock 登录（开发调试）。

**登录流程：**
1. 调用 `uni.login` 获取微信登录 code
2. 发送 code 到后端换取 JWT token
3. 存储 token 和用户信息到本地
4. 后续请求自动携带 Authorization 头

---

## 状态管理

采用 Pinia 进行全局状态管理，支持本地持久化。

### Auth Store (`stores/auth.ts`)

用户认证状态管理。

```typescript
// 主要 API
const authStore = useAuthStore()

authStore.isLoggedIn      // 是否已登录
authStore.userInfo        // 用户信息
authStore.token           // JWT Token

authStore.setToken(token) // 设置 Token
authStore.silentLogin()   // 静默登录
authStore.requireLogin()  // 检查登录状态，未登录跳转登录页
authStore.clearAuth()     // 登出清除
```

### Project Store (`stores/project.ts`)

项目（IP）管理状态。

```typescript
// 主要 API
const projectStore = useProjectStore()

projectStore.projectList       // 项目列表
projectStore.activeProject     // 当前激活项目
projectStore.currentPersonaSettings // 当前人设配置

projectStore.fetchProjects()   // 获取项目列表
projectStore.createProject(data) // 创建项目
projectStore.updateProject(id, data) // 更新项目
projectStore.deleteProject(id) // 删除项目
projectStore.setActiveProject(project) // 切换项目
projectStore.getPersonaSystemPrompt() // 获取人设系统提示词
```

### Settings Store (`stores/settings.ts`)

全局设置管理（AI 模型选择等）。

```typescript
// 主要 API
const settingsStore = useSettingsStore()

settingsStore.modelType      // 当前模型类型
settingsStore.currentModel   // 当前模型配置
settingsStore.availableModels // 可用模型列表

settingsStore.setModelType('doubao') // 切换模型
```

---

## API 请求封装

封装了统一的请求工具，自动处理 Token、错误、Loading 等。

### 使用方式

```typescript
import { get, post, put, del } from '@/utils/request'

// GET 请求
const res = await get<{ projects: Project[] }>('/api/projects')

// POST 请求
const res = await post<{ success: boolean }>('/api/projects', {
  name: '我的项目'
})

// 带配置的请求
const res = await post('/api/generate', data, {
  showLoading: true,
  loadingText: 'AI 生成中...',
  timeout: 60000
})
```

### 请求配置选项

| 选项 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `needToken` | boolean | true | 是否携带 Token |
| `showLoading` | boolean | false | 是否显示 Loading |
| `loadingText` | string | '加载中...' | Loading 提示文字 |
| `timeout` | number | 30000 | 超时时间（毫秒） |
| `useMock` | boolean | false | 是否使用 Mock 数据 |

### 响应拦截

- **401** - Token 过期，自动清除认证信息
- **403** - 权限不足
- **404** - 资源不存在
- **5xx** - 服务器错误

---

## 多平台适配

### 支持的平台

| 平台 | 命令 | 说明 |
|------|------|------|
| 微信小程序 | `dev:mp-weixin` | 主要目标平台 |
| H5 Web | `dev:h5` | 浏览器访问 |
| 支付宝小程序 | `dev:mp-alipay` | 支付宝生态 |
| 抖音小程序 | `dev:mp-toutiao` | 字节生态 |
| 百度小程序 | `dev:mp-baidu` | 百度生态 |
| QQ 小程序 | `dev:mp-qq` | QQ 生态 |
| 快手小程序 | `dev:mp-kuaishou` | 快手生态 |
| 小红书小程序 | `dev:mp-xhs` | 小红书生态 |
| 鸿蒙 | `dev:mp-harmony` | 华为鸿蒙 |
| App | 需 HBuilderX | iOS/Android |

### 条件编译

```vue
<template>
  <!-- #ifdef MP-WEIXIN -->
  <button open-type="getUserInfo">微信授权</button>
  <!-- #endif -->
  
  <!-- #ifdef H5 -->
  <button @click="h5Login">H5 登录</button>
  <!-- #endif -->
</template>

<script>
// #ifdef MP-WEIXIN
uni.login({ provider: 'weixin' })
// #endif

// #ifndef MP-WEIXIN
// 非微信环境的逻辑
// #endif
</script>
```

---

## AI 模型配置

### 当前支持的模型

| 模型 | 类型标识 | 状态 | 说明 |
|------|----------|------|------|
| DeepSeek | `deepseek` | ✅ 可用 | 深度求索，国产大模型 |
| 豆包 | `doubao` | ✅ 可用 | 字节跳动火山引擎（默认） |
| Claude | `claude` | ✅ 可用 | Anthropic Claude |
| GPT-4 | `gpt4` | 🔒 预留 | OpenAI GPT-4 |

### 切换默认模型

修改 `stores/settings.ts`：

```typescript
// 修改默认模型
const modelType = ref<ModelType>('doubao')  // 默认使用豆包
```

或在业务代码中：

```typescript
// 验证 modelType，如果无效则使用默认值
if (!modelType || !['deepseek', 'doubao', 'claude'].includes(modelType)) {
  modelType = 'doubao'  // 默认使用豆包（节省API成本）
}
```

---

## 环境配置

### API 地址配置

修改 `vite.config.ts`：

```typescript
// 开发环境 API 地址
const DEV_API_URL = "http://localhost:8000";

// 生产环境 API 地址（部署时修改此处）
const PROD_API_URL = "https://api.your-domain.com";
```

### 微信小程序配置

修改 `src/manifest.json`：

```json
{
  "mp-weixin": {
    "appid": "你的小程序AppID",
    "setting": {
      "urlCheck": false  // 开发时关闭域名校验
    }
  }
}
```

---

## 后期数据库扩展说明

当前前端已预留完整的数据接口，后端可根据需要扩展数据库。

### 用户相关表

```sql
-- 用户表
CREATE TABLE users (
  id VARCHAR(36) PRIMARY KEY,
  openid VARCHAR(64) UNIQUE,       -- 微信 openid
  nickname VARCHAR(100),
  avatar_url TEXT,
  gender TINYINT DEFAULT 0,
  city VARCHAR(50),
  province VARCHAR(50),
  country VARCHAR(50),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);
```

### 项目相关表

```sql
-- 项目表
CREATE TABLE projects (
  id VARCHAR(36) PRIMARY KEY,
  user_id VARCHAR(36) NOT NULL,
  name VARCHAR(100) NOT NULL,
  industry VARCHAR(50),
  avatar_letter CHAR(1),
  avatar_color VARCHAR(20),
  is_active BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- 项目人设配置表
CREATE TABLE project_personas (
  id VARCHAR(36) PRIMARY KEY,
  project_id VARCHAR(36) NOT NULL UNIQUE,
  tone VARCHAR(50),                    -- 语气风格
  catchphrase TEXT,                    -- 口头禅
  target_audience VARCHAR(200),        -- 目标受众
  benchmark_accounts JSON,             -- 对标账号（数组）
  content_style TEXT,                  -- 内容风格
  taboos JSON,                         -- 内容禁忌（数组）
  keywords JSON,                       -- 常用关键词（数组）
  introduction TEXT,                   -- IP 简介
  FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
);
```

### 对话历史表（可选扩展）

```sql
-- 对话历史表
CREATE TABLE chat_histories (
  id VARCHAR(36) PRIMARY KEY,
  user_id VARCHAR(36) NOT NULL,
  project_id VARCHAR(36),
  agent_type VARCHAR(50),              -- 智能体类型
  model_type VARCHAR(20),              -- 使用的 AI 模型
  role ENUM('user', 'assistant', 'system') NOT NULL,
  content TEXT NOT NULL,
  tokens_used INT,                     -- 消耗的 token 数
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
  FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE SET NULL
);

-- 对话会话表
CREATE TABLE chat_sessions (
  id VARCHAR(36) PRIMARY KEY,
  user_id VARCHAR(36) NOT NULL,
  project_id VARCHAR(36),
  title VARCHAR(200),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);
```

### API 使用统计表（可选扩展）

```sql
-- API 调用统计
CREATE TABLE api_usage (
  id VARCHAR(36) PRIMARY KEY,
  user_id VARCHAR(36) NOT NULL,
  model_type VARCHAR(20) NOT NULL,
  endpoint VARCHAR(100),
  tokens_input INT DEFAULT 0,
  tokens_output INT DEFAULT 0,
  cost DECIMAL(10, 6) DEFAULT 0,       -- 费用（美元/人民币）
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- 用户配额表
CREATE TABLE user_quotas (
  id VARCHAR(36) PRIMARY KEY,
  user_id VARCHAR(36) NOT NULL UNIQUE,
  total_tokens INT DEFAULT 100000,     -- 总配额
  used_tokens INT DEFAULT 0,           -- 已使用
  reset_at TIMESTAMP,                  -- 重置时间
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);
```

### 前端对接说明

前端已预留以下接口，后端实现后可直接对接：

```typescript
// 项目 CRUD
GET    /api/projects          // 获取项目列表
POST   /api/projects          // 创建项目
PUT    /api/projects/:id      // 更新项目
DELETE /api/projects/:id      // 删除项目
POST   /api/projects/switch   // 切换激活项目

// 认证
POST   /api/auth/login        // 微信登录

// AI 生成
POST   /api/generate          // 通用生成接口

// 可扩展接口（预留）
GET    /api/chat/sessions     // 获取会话列表
GET    /api/chat/history/:id  // 获取对话历史
POST   /api/chat/save         // 保存对话
GET    /api/usage/stats       // 使用统计
```

---

## 部署指南

### 微信小程序发布

1. 运行 `npm run build:mp-weixin`
2. 打开微信开发者工具
3. 导入 `dist/build/mp-weixin` 目录
4. 点击"上传"提交审核

### H5 部署

1. 修改 `vite.config.ts` 中的生产环境 API 地址
2. 运行 `npm run build:h5`
3. 将 `dist/build/h5` 目录部署到 Web 服务器

### 注意事项

- 生产环境需配置 HTTPS
- 微信小程序需在后台配置合法域名
- 建议开启 CDN 加速静态资源

---

## 开发规范

### 代码风格

- 使用 Vue 3 Composition API + `<script setup>` 语法
- 使用 TypeScript 进行类型约束
- 组件命名采用 PascalCase
- 文件命名采用 kebab-case

### 提交规范

```
feat: 新功能
fix: Bug 修复
docs: 文档更新
style: 代码格式调整
refactor: 重构
perf: 性能优化
test: 测试相关
chore: 构建/工具相关
```

---

## 许可证

MIT License

---

## 联系方式

如有问题或建议，请联系开发团队。

