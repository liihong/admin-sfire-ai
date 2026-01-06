"""
Routers Package
路由聚合包
"""
from fastapi import APIRouter

from .client import client_router
from .admin import admin_router

__all__ = ["client_router", "admin_router"]



