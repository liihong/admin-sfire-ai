"""
API v1 Router - 路由汇总
"""
from fastapi import APIRouter

from .endpoints import auth, users, dashboard, menu, agents, roles, admin_users, ai, llm_models, banner, home_config

api_router = APIRouter()

# 认证相关路由
api_router.include_router(
    auth.router,
    prefix="/auth",
    tags=["认证"]
)

# 管理员用户管理路由
api_router.include_router(
    admin_users.router,
    prefix="/admin-users",
    tags=["管理员用户管理"]
)

# 用户管理路由（微信小程序用户）
api_router.include_router(
    users.router,
    prefix="/users",
    tags=["用户管理"]
)

# Dashboard 统计路由
api_router.include_router(
    dashboard.router,
    prefix="/dashboard",
    tags=["Dashboard 统计"]
)

# 菜单管理路由
api_router.include_router(
    menu.router,
    prefix="/menu",
    tags=["菜单管理"]
)

# 智能体管理路由
api_router.include_router(
    agents.router,
    prefix="/agents",
    tags=["智能体管理"]
)

# 角色管理路由
api_router.include_router(
    roles.router,
    prefix="/roles",
    tags=["角色管理"]
)

# AI 对话路由
api_router.include_router(
    ai.router,
    prefix="/ai",
    tags=["AI 对话"]
)

# 大模型管理路由
api_router.include_router(
    llm_models.router,
    prefix="/llm-models",
    tags=["大模型管理"]
)

# Banner管理路由
api_router.include_router(
    banner.router,
    prefix="/banners",
    tags=["Banner管理"]
)

# 首页配置路由
api_router.include_router(
    home_config.router,
    prefix="/home-configs",
    tags=["首页配置"]
)


