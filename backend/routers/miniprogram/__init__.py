"""
MiniProgram Routers
小程序路由聚合
"""
from fastapi import APIRouter

from . import auth, creation, projects, tikhub

miniprogram_router = APIRouter()

# 注册各个模块的路由
miniprogram_router.include_router(auth.router, prefix="/auth", tags=["小程序-认证"])
miniprogram_router.include_router(projects.router, prefix="/projects", tags=["小程序-项目管理"])
miniprogram_router.include_router(creation.router, prefix="/creation", tags=["小程序-内容生成"])
miniprogram_router.include_router(tikhub.router, prefix="/tikhub", tags=["小程序-抖音分析"])

