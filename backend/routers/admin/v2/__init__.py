"""
Admin v2路由
后台管理接口（v2版本）
"""
from fastapi import APIRouter

from .skill_library import router as skill_library_router
from .agents_v2 import router as agents_v2_router

admin_v2_router = APIRouter()

# 注册子路由
admin_v2_router.include_router(skill_library_router)
admin_v2_router.include_router(agents_v2_router)

__all__ = ["admin_v2_router"]
