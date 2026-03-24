"""
C 端：抖音文案提取（TikHub + 火山 ASR）
"""
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from core.deps import get_current_miniprogram_user
from models.user import User
from services.tools.douyin_caption_service import DouyinCaptionService
from utils.response import success

router = APIRouter()


class DouyinCaptionExtractRequest(BaseModel):
    url: str = Field(..., min_length=8, description="抖音分享链接或视频页链接")


@router.post("/extract", summary="抖音链接提取口播文案")
async def extract_caption(
    body: DouyinCaptionExtractRequest,
    _user: User = Depends(get_current_miniprogram_user),
):
    """
    使用 TikHub 解析作品并获取可播放地址，再由火山引擎异步语音识别转写为文字。
    不在服务器保存视频或音频文件。
    """
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
