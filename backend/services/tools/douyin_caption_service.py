"""
抖音文案提取：TikHub 解析链接 + 火山 ASR 转写（不落盘音视频）
"""
from __future__ import annotations

from dataclasses import dataclass

from loguru import logger

from services.tools.tikhub_douyin import resolve_play_url_from_share
from services.tools.volcengine_asr_client import get_volcengine_asr_client
from utils.exceptions import BadRequestException, ServerErrorException


@dataclass
class DouyinCaptionResult:
    text: str
    aweme_id: str
    title: str | None
    play_url: str


class DouyinCaptionService:
    """编排第三方解析与语音识别，本服务无状态、不存储媒体文件。"""

    async def extract(self, share_url: str) -> DouyinCaptionResult:
        media_urls, title, aweme_id = await resolve_play_url_from_share(share_url)
        asr = get_volcengine_asr_client()
        last_err: ServerErrorException | None = None
        for u in media_urls:
            try:
                text = await asr.transcribe_url(u, language="zh-CN")
                return DouyinCaptionResult(
                    text=text,
                    aweme_id=aweme_id,
                    title=title,
                    play_url=u,
                )
            except BadRequestException:
                raise
            except ServerErrorException as e:
                last_err = e
                logger.warning(f"抖音文案 ASR 失败，尝试下一媒体地址: {e}")
                continue
        if last_err:
            raise last_err
        raise ServerErrorException(msg="语音识别失败")
