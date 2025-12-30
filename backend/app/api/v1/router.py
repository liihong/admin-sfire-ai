"""
API v1 Router - 路由汇总
"""
from fastapi import APIRouter

from .endpoints import auth, users, dashboard, menu

api_router = APIRouter()

# 认证相关路由
api_router.include_router(
    auth.router,
    prefix="/auth",
    tags=["认证"]
)

# 用户管理路由
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


