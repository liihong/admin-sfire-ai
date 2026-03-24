"""
C 端工具包路由
- packages：公开元数据
- voice-clone 等：按接口使用小程序用户鉴权
"""
from fastapi import APIRouter

from . import voice_clone, tool_packages, douyin_caption

router = APIRouter()
router.include_router(
    tool_packages.router, prefix="/packages", tags=["工具包-元数据"]
)
router.include_router(voice_clone.router, prefix="/voice-clone", tags=["工具包-声音复刻"])
router.include_router(
    douyin_caption.router, prefix="/douyin-caption", tags=["工具包-抖音文案提取"]
)
