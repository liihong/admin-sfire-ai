# SFire Admin Backend

基于 FastAPI 的高性能管理后台 API 服务，支持 C端（小程序）和 B端（管理后台）接口的物理隔离。

## 技术栈

- **FastAPI** - 高性能异步 Web 框架
- **SQLAlchemy 2.0** - 异步 ORM
- **MySQL** - 关系型数据库
- **Redis** - 缓存和会话存储
- **Pydantic v2** - 数据验证
- **JWT** - 身份认证

## 项目结构

```
backend/
├── main.py                 # 应用入口
├── requirements.txt        # 依赖列表
├── env.example            # 环境变量示例
│
├── routers/               # 路由层（Controller）- 物理隔离
│   ├── miniprogram/      # C端接口（小程序 & PC官网）
│   │   ├── auth.py       # 微信登录/扫码登录
│   │   ├── creation.py    # 文案生成
│   │   ├── projects.py    # 项目管理
│   │   └── tikhub.py     # 抖音分析
│   └── admin/            # B端接口（管理后台）
│       ├── auth.py        # 管理员账号密码登录
│       ├── dashboard.py   # 数据大屏
│       ├── agents.py      # 智能体配置管理
│       ├── users.py       # 用户管理
│       └── ...            # 其他管理接口
│
├── models/               # 数据库模型（共享）
├── services/             # 业务逻辑层（共享）
├── schemas/              # Pydantic 数据模式（共享）
├── core/                 # 核心配置
│   ├── config.py         # 应用配置
│   ├── security.py        # 安全相关（JWT）
│   └── deps.py           # 鉴权依赖（区分 get_current_user 和 get_current_admin）
├── db/                   # 数据库连接
│   ├── session.py         # 数据库会话管理
│   └── redis.py           # Redis 连接
├── middleware/           # 中间件
│   └── rate_limiter.py   # API 限流
├── utils/                # 工具函数
│   ├── response.py        # 统一响应格式
│   └── exceptions.py      # 异常处理
├── constants/            # 常量定义
└── scripts/              # 数据库初始化脚本
```

## 架构设计

### 路由物理隔离

项目采用 FastAPI 的 APIRouter 分层机制，实现了 C端和 B端接口的物理隔离：

- **C端接口** (`/api/v1/client/*`): 小程序和 PC 官网使用
  - 微信登录、项目管理、内容生成、抖音分析等
  
- **B端接口** (`/api/v1/admin/*`): 管理后台使用
  - 管理员认证、数据大屏、用户管理、智能体配置等

### 共享资源

以下模块为 C端和 B端共享：

- `models/` - 数据库模型（User, Project, Agent 等）
- `services/` - 业务逻辑层（Service Layer）
- `schemas/` - 数据验证模式
- `db/` - 数据库连接
- `core/` - 核心配置和安全
- `utils/` - 工具函数

### 鉴权机制

- `get_current_user()` - 获取当前管理员用户（AdminUser）
- `get_current_miniprogram_user()` - 获取当前小程序用户（User）
- `get_current_admin()` - 获取当前管理员（需要角色权限）

## 快速开始

### 1. 创建虚拟环境

```bash
cd backend
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 配置环境变量

```bash
cp env.example .env
# 编辑 .env 文件，配置数据库等信息
```

### 4. 初始化数据库

```bash
# 运行数据库初始化脚本
python scripts/init_mysql_db.py
```

### 5. 启动服务

```bash
# 开发模式
python main.py

# 或使用 uvicorn
uvicorn main:app --reload
```

### 6. 访问 API 文档

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## API 路径说明

### C端接口（小程序 & PC官网）

所有 C端接口使用 `/api/v1/client` 前缀：

- `/api/v1/client/auth/login` - 微信小程序登录
- `/api/v1/client/auth/user` - 获取当前用户信息
- `/api/v1/client/projects` - 项目管理
- `/api/v1/client/creation/chat` - 内容生成
- `/api/v1/client/tikhub/analyze-douyin` - 抖音账号分析

### B端接口（管理后台）

所有 B端接口使用 `/api/v1/admin` 前缀：

- `/api/v1/admin/auth/login` - 管理员登录
- `/api/v1/admin/dashboard/stats` - 数据大屏统计
- `/api/v1/admin/users` - 用户管理
- `/api/v1/admin/agents` - 智能体管理
- `/api/v1/admin/menu` - 菜单管理

## API 响应格式

所有接口统一返回以下格式（兼容 Geeker-Admin）：

```json
{
  "code": 200,
  "data": {},
  "msg": "操作成功"
}
```

### 状态码说明

| code | 说明 |
|------|------|
| 200  | 成功 |
| 400  | 请求参数错误 |
| 401  | 未授权 |
| 403  | 禁止访问 |
| 404  | 资源不存在 |
| 500  | 服务器错误 |

## 开发规范

1. **目录结构**: 所有模块都在根目录下，采用扁平化结构
2. **路由组织**: C端和 B端路由物理隔离，使用不同的前缀
3. **异步操作**: 所有数据库操作使用异步方式
4. **业务逻辑**: 业务逻辑放在 `services/` 层，路由层只负责请求处理
5. **数据验证**: 使用 Pydantic schemas 进行数据验证
6. **日志记录**: 统一使用 loguru 进行日志记录
7. **导入路径**: 使用绝对导入，从根目录开始（如 `from models.user import User`）

## 依赖注入

### 数据库会话

```python
from db import get_db
from sqlalchemy.ext.asyncio import AsyncSession

async def my_endpoint(db: AsyncSession = Depends(get_db)):
    # 使用数据库会话
    pass
```

### 用户认证

```python
# 管理员认证
from core.deps import get_current_user
from models.admin_user import AdminUser

async def admin_endpoint(current_user: AdminUser = Depends(get_current_user)):
    pass

# 小程序用户认证
from core.deps import get_current_miniprogram_user
from models.user import User

async def client_endpoint(current_user: User = Depends(get_current_miniprogram_user)):
    pass
```

## 数据库迁移

数据库迁移相关文档请参考 `DATABASE_MIGRATION.md`。

## 部署

生产环境部署请参考项目根目录下的 `DEPLOYMENT.md` 和 `deploy/` 目录中的部署脚本。
