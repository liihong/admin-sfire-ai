"""
Routers Package
路由聚合包
"""
from fastapi import APIRouter

from .client import client_router
from .admin import admin_router

# 导入v2版本路由
from .admin.v2 import admin_v2_router
from .client.v2 import client_v2_router

__all__ = ["client_router", "admin_router", "admin_v2_router", "client_v2_router"]



