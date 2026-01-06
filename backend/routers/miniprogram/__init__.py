"""
MiniProgram Routers
小程序路由聚合
"""
from fastapi import APIRouter

from . import auth, creation, projects, tikhub
from .creation import AgentListResponse, list_agents, generate_chat, quick_generate

miniprogram_router = APIRouter()

# 注册各个模块的路由
miniprogram_router.include_router(auth.router, prefix="/auth", tags=["小程序-认证"])
miniprogram_router.include_router(projects.router, prefix="/projects", tags=["小程序-项目管理"])
miniprogram_router.include_router(creation.router, prefix="/creation", tags=["小程序-内容生成"])
miniprogram_router.include_router(tikhub.router, prefix="/tikhub", tags=["小程序-抖音分析"])

# 直接暴露智能体列表接口，复用微信小程序接口
miniprogram_router.add_api_route(
    "/agents",
    list_agents,
    methods=["GET"],
    response_model=AgentListResponse,
    tags=["小程序-智能体"]
)

# 直接暴露对话接口，复用小程序已有实现
miniprogram_router.add_api_route(
    "/chat",
    generate_chat,
    methods=["POST"],
    tags=["小程序-内容生成"]
)

miniprogram_router.add_api_route(
    "/chat/quick",
    quick_generate,
    methods=["POST"],
    tags=["小程序-内容生成"]
)


