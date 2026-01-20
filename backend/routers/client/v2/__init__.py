"""
Client v2路由
前端用户接口（v2版本）
"""
from fastapi import APIRouter

from .execution import router as execution_router

client_v2_router = APIRouter()

# 注册子路由
client_v2_router.include_router(execution_router)

__all__ = ["client_v2_router"]
