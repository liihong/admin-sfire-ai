"""
C 端工具包路由
鉴权：get_current_miniprogram_user
"""
from fastapi import APIRouter

from . import voice_clone

router = APIRouter()
router.include_router(voice_clone.router, prefix="/voice-clone", tags=["工具包-声音复刻"])
