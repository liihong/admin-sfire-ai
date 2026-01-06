"""
Routers Package
路由聚合包
"""
from fastapi import APIRouter

from .miniprogram import miniprogram_router
from .admin import admin_router

__all__ = ["miniprogram_router", "admin_router"]



