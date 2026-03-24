"""
B 端工具包路由
鉴权：get_current_user（具体能力接口）；配置类接口在 tool_packages 中统一鉴权
"""
from fastapi import APIRouter

from . import voice_clone, tool_packages, douyin_caption

router = APIRouter()
router.include_router(
    tool_packages.router, prefix="/packages", tags=["工具包-配置管理"]
)
router.include_router(voice_clone.router, prefix="/voice-clone", tags=["工具包-声音复刻"])
router.include_router(
    douyin_caption.router, prefix="/douyin-caption", tags=["工具包-抖音文案提取"]
)
