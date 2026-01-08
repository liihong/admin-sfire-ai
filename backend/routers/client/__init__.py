"""
Client Routers
C端路由聚合（小程序 & PC官网）
统一管理所有C端用户接口，包括小程序和PC官网共用的功能
"""
from fastapi import APIRouter

from . import auth, creation, projects, tikhub, web_auth, conversations

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
