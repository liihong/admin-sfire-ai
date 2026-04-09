"""
C 端：抖音文案提取（TikHub + 火山 ASR）
"""
import uuid

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from constants.coin_config import CoinConfig
from core.deps import get_current_miniprogram_user
from db import get_db
from models.user import User
from services.coin import CoinServiceFactory
from services.tools.douyin_caption_service import DouyinCaptionService
from utils.response import success

router = APIRouter()


class DouyinCaptionExtractRequest(BaseModel):
    url: str = Field(..., min_length=8, description="抖音分享链接或视频页链接")


@router.post("/extract", summary="抖音链接提取口播文案")
async def extract_caption(
    body: DouyinCaptionExtractRequest,
    current_user: User = Depends(get_current_miniprogram_user),
    db: AsyncSession = Depends(get_db),
):
    """
    使用 TikHub 解析作品并获取可播放地址，再由火山引擎异步语音识别转写为文字。
    不在服务器保存视频或音频文件。

    C 端每次调用扣固定火源币（见 CoinConfig.DOUYIN_CAPTION_EXTRACT_COST）；
    解析/识别失败时自动退还本次扣费。管理端同名接口不扣费。
    """
    cost = CoinConfig.DOUYIN_CAPTION_EXTRACT_COST
    task_id = f"douyin_caption_{uuid.uuid4().hex}"
    coin = CoinServiceFactory(db)

    await coin.consume_fixed_tool_fee(
        user_id=current_user.id,
        amount=cost,
        remark="抖音文案提取",
        task_id=task_id,
        source="miniapp",
    )

    svc = DouyinCaptionService()
    try:
        r = await svc.extract(body.url.strip())
    except Exception:
        try:
            await coin.refund_fixed_tool_fee(
                user_id=current_user.id,
                amount=cost,
                remark="抖音文案提取失败退还",
                task_id=task_id,
                source="miniapp",
            )
        except Exception as re:
            logger.error(
                "抖音文案提取失败后退费异常: user_id={} task_id={} err={}",
                current_user.id,
                task_id,
                re,
            )
        raise

    return success(
        data={
            "text": r.text,
            "aweme_id": r.aweme_id,
            "title": r.title,
            "coin_cost": int(cost),
        },
        msg="提取成功",
    )
