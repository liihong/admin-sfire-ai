"""
API v1 Router
汇总所有 v1 版本的路由
"""
from fastapi import APIRouter

from app.api.v1.endpoints import auth, admin_users, agents, banner, dashboard, home_config, llm_models, menu, users

# Try to import roles if it exists and has a router
try:
    from app.api.v1.endpoints import roles
except (ImportError, AttributeError):
    roles = None

# Try to import AI endpoint
try:
    from app.api.v1.endpoints import ai
    ai_available = True
except (ImportError, AttributeError):
    ai = None
    ai_available = False

api_router = APIRouter()

# 注册各个模块的路由
api_router.include_router(auth.router, prefix="/auth", tags=["认证"])
api_router.include_router(admin_users.router, prefix="/admin-users", tags=["管理员用户"])
api_router.include_router(agents.router, prefix="/agents", tags=["智能体"])
api_router.include_router(banner.router, prefix="/banner", tags=["轮播图"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["仪表盘"])
api_router.include_router(home_config.router, prefix="/home-config", tags=["首页配置"])
api_router.include_router(llm_models.router, prefix="/llm-models", tags=["LLM模型"])
api_router.include_router(menu.router, prefix="/menu", tags=["菜单"])
if roles and hasattr(roles, "router"):
    api_router.include_router(roles.router, prefix="/roles", tags=["角色"])
api_router.include_router(users.router, prefix="/users", tags=["用户"])

if ai_available and hasattr(ai, "router"):
    api_router.include_router(ai.router, prefix="/ai", tags=["AI对话"])
