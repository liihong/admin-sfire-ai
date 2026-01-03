# SFire Admin Backend

基于 FastAPI 的高性能管理后台 API 服务。

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
├── .env.example           # 环境变量示例
├── app/
│   ├── api/v1/            # API 路由
│   │   ├── router.py      # 路由汇总
│   │   └── endpoints/     # 各模块端点
│   ├── core/              # 核心配置
│   │   ├── config.py      # 应用配置
│   │   └── security.py    # 安全相关
│   ├── db/                # 数据库
│   │   └── session.py     # 数据库连接
│   ├── models/            # SQLAlchemy 模型
│   ├── schemas/           # Pydantic 模型
│   ├── services/          # 业务逻辑层
│   └── utils/             # 工具函数
│       ├── response.py    # 统一响应格式
│       └── exceptions.py  # 异常处理
```

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
cp .env.example .env
# 编辑 .env 文件，配置数据库等信息
```

### 4. 启动服务

```bash
# 开发模式
python main.py

# 或使用 uvicorn
uvicorn main:app --reload
```

### 5. 访问 API 文档

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

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

1. 所有数据库操作使用异步方式
2. 业务逻辑放在 services 层
3. 数据验证使用 Pydantic schemas
4. 统一使用 loguru 进行日志记录



