"""
B 端：抖音文案提取（与 C 端能力一致，便于在工具包内自测）
"""
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from core.deps import get_current_user
from models.admin_user import AdminUser
from services.tools.douyin_caption_service import DouyinCaptionService
from utils.response import success

router = APIRouter()


class DouyinCaptionExtractRequest(BaseModel):
    url: str = Field(..., min_length=8, description="抖音分享链接或视频页链接")


@router.post("/extract", summary="抖音链接提取口播文案")
async def extract_caption(
    body: DouyinCaptionExtractRequest,
    _admin: AdminUser = Depends(get_current_user),
):
    svc = DouyinCaptionService()
    r = await svc.extract(body.url.strip())
    return success(
        data={
            "text": r.text,
            "aweme_id": r.aweme_id,
            "title": r.title,
        },
        msg="提取成功",
    )
