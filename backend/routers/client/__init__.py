"""
Client Routers
C端路由聚合（小程序 & PC官网）
统一管理所有C端用户接口，包括小程序和PC官网共用的功能
"""
from fastapi import APIRouter

from . import auth, creation, projects, tikhub, web_auth, conversations, coin, security, permission, quick_entries, inspirations, home, article

# 创建C端路由聚合器
client_router = APIRouter()

# 注册各个模块的路由
# 认证模块：支持小程序微信登录、PC官网扫码登录、账号密码登录等
client_router.include_router(auth.router, prefix="/auth", tags=["C端-认证"])
# PC端独立认证模块：扫码登录、账号密码登录
client_router.include_router(web_auth.router, prefix="/auth", tags=["C端-认证-PC"])

# 项目管理模块：小程序和PC官网共用
client_router.include_router(projects.router, prefix="/projects", tags=["C端-项目管理"])

# 内容生成模块：智能体列表、对话生成等
# 注意：creation.router 中的路由（/agents, /chat, /chat/quick）直接暴露在根路径下
client_router.include_router(creation.router, prefix="", tags=["C端-内容生成"])

# 抖音分析模块：小程序和PC官网共用
client_router.include_router(tikhub.router, prefix="/tikhub", tags=["C端-抖音分析"])

# 对话会话管理模块
client_router.include_router(conversations.router, prefix="", tags=["C端-对话会话"])

# 算力管理模块
client_router.include_router(coin.router, prefix="", tags=["C端-算力管理"])

# 安全检测模块：内容安全检测等
client_router.include_router(security.router, prefix="/security", tags=["C端-安全检测"])

# 权限管理模块：用户权限快照查询
client_router.include_router(permission.router, prefix="/permission", tags=["C端-权限管理"])

# 快捷入口模块：今天拍点啥、快捷指令库
client_router.include_router(quick_entries.router, prefix="/quick-entries", tags=["C端-快捷入口"])

# 灵感管理模块：灵感捕获、列表、生成等
client_router.include_router(inspirations.router, prefix="/inspirations", tags=["C端-灵感管理"])

# 文章模块：小程序首页文章内容
client_router.include_router(article.router, prefix="/articles", tags=["C端-文章"])

# 首页内容模块：聚合首页所需的所有数据（Banner + 文章）
client_router.include_router(home.router, prefix="/home", tags=["C端-首页"])
