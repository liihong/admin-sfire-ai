"""
Admin Routers
管理后台路由聚合
"""
from fastapi import APIRouter

from . import (
    auth, dashboard, agents, admin_users, banner, 
    home_config, llm_models, menu, users, dictionary
)

# 尝试导入可选的路由
try:
    from . import roles
    roles_available = True
except ImportError:
    roles = None
    roles_available = False

try:
    from . import ai
    ai_available = True
except ImportError:
    ai = None
    ai_available = False

admin_router = APIRouter()

# 注册各个模块的路由
admin_router.include_router(auth.router, prefix="/auth", tags=["认证"])
admin_router.include_router(admin_users.router, prefix="/admin-users", tags=["管理员用户"])
admin_router.include_router(agents.router, prefix="/agents", tags=["智能体"])
admin_router.include_router(banner.router, prefix="/banners", tags=["轮播图"])
admin_router.include_router(dashboard.router, prefix="/dashboard", tags=["仪表盘"])
admin_router.include_router(home_config.router, prefix="/home-config", tags=["首页配置"])
admin_router.include_router(llm_models.router, prefix="/llm-models", tags=["LLM模型"])
admin_router.include_router(menu.router, prefix="/menu", tags=["菜单"])
admin_router.include_router(users.router, prefix="/users", tags=["用户"])
admin_router.include_router(dictionary.router, prefix="/dictionary", tags=["数据字典"])

if roles_available and hasattr(roles, "router"):
    admin_router.include_router(roles.router, prefix="/roles", tags=["角色"])

if ai_available and hasattr(ai, "router"):
    admin_router.include_router(ai.router, prefix="/ai", tags=["AI对话"])

