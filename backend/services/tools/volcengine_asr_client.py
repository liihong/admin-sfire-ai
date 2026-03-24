"""
火山引擎 大模型录音文件识别标准版（异步 submit + query）
文档：https://www.volcengine.com/docs/6561/1354868
仅 HTTP，不落盘；通过 audio.url 传入公网可访问的媒体地址。
"""
from __future__ import annotations

import asyncio
import time
import uuid
from typing import Any, Optional

import httpx
from loguru import logger

from core.config import settings
from utils.exceptions import BadRequestException, ServerErrorException

SUBMIT_URL = "https://openspeech.bytedance.com/api/v3/auc/bigmodel/submit"
QUERY_URL = "https://openspeech.bytedance.com/api/v3/auc/bigmodel/query"

# query 返回：处理中 / 排队
PENDING_CODES = {20000001, 20000002}
# 静音 / 无有效语音
SILENCE_CODE = 20000003


class VolcengineAsrClient:
    def __init__(self) -> None:
        self.app_key = (settings.VOLCENGINE_APP_ID or "").strip()
        self.access_key = (settings.VOLCENGINE_ACCESS_TOKEN or "").strip()
        self.resource_id = (
            getattr(settings, "VOLCENGINE_ASR_RESOURCE_ID", None) or "volc.bigasr.auc"
        ).strip()
        self.poll_interval = float(
            getattr(settings, "VOLCENGINE_ASR_POLL_INTERVAL_SEC", None) or 1.5
        )
        self.poll_timeout = float(
            getattr(settings, "VOLCENGINE_ASR_POLL_TIMEOUT_SEC", None) or 180.0
        )

    def _check_config(self) -> None:
        if not self.app_key or not self.access_key:
            raise BadRequestException(
                msg="火山语音识别未配置，请配置 VOLCENGINE_APP_ID 与 VOLCENGINE_ACCESS_TOKEN"
            )

    def _headers(self, request_id: str) -> dict[str, str]:
        return {
            "Content-Type": "application/json",
            "X-Api-App-Key": self.app_key,
            "X-Api-Access-Key": self.access_key,
            "X-Api-Resource-Id": self.resource_id,
            "X-Api-Request-Id": request_id,
            "X-Api-Sequence": "-1",
        }

    @staticmethod
    def _is_likely_video_url(media_url: str) -> bool:
        """抖音/常见 CDN 视频 MP4 直链（无扩展名也可能是视频）。"""
        u = media_url.lower()
        return bool(
            u.endswith(".mp4")
            or "/video/tos" in u
            or "douyinvod" in u
            or "mime=video" in u
            or "aweme/snas" in u
            or "bytevod" in u
        )

    def _submit_format_candidates(self, media_url: str) -> list[str]:
        """
        文档要求 format ∈ raw/wav/mp3/ogg，勿传 mp4（会 query 报 45000151 audio convert failed）。
        对视频 MP4 直链：按官方枚举用 mp3 声明，由服务端拉取 URL 后解封装（与控制台常见用法一致）。
        """
        fixed = (getattr(settings, "VOLCENGINE_ASR_AUDIO_FORMAT", None) or "").strip()
        if fixed:
            return [fixed]

        u = media_url.lower().split("?", 1)[0]
        if u.endswith(".mp3"):
            return ["mp3"]
        if u.endswith(".wav"):
            return ["wav"]
        if u.endswith(".ogg"):
            return ["ogg"]

        if self._is_likely_video_url(media_url):
            return ["mp3", "ogg", "wav"]

        return ["mp3", "ogg", "wav"]

    @staticmethod
    def _is_retryable_format_error(exc: BaseException) -> bool:
        s = str(exc)
        return (
            "45000151" in s
            or "Invalid audio format" in s
            or "audio convert" in s
        )

    async def _submit(
        self, media_url: str, request_id: str, language: str, fmt: str
    ) -> None:
        self._check_config()
        body: dict[str, Any] = {
            "user": {"uid": "douyin-caption-tool"},
            "audio": {
                "url": media_url,
                "format": fmt,
                "language": language,
            },
            "request": {
                "model_name": "bigmodel",
                "enable_itn": True,
                "enable_punc": True,
            },
        }
        # 仅文档列出的容器；不传 codec，避免与 mp3/ogg 等冲突
        if fmt in ("mp3", "wav", "ogg", "raw"):
            body["audio"].pop("codec", None)

        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(60.0)) as client:
                resp = await client.post(
                    SUBMIT_URL, headers=self._headers(request_id), json=body
                )
        except httpx.RequestError as e:
            logger.error(f"火山 ASR submit 网络错误: {e}")
            raise ServerErrorException(msg="语音识别服务请求失败")

        status = (resp.headers.get("X-Api-Status-Code") or "").strip()
        msg = resp.headers.get("X-Api-Message", "")
        logid = resp.headers.get("X-Tt-Logid", "")
        if status != "20000000":
            logger.error(
                f"火山 ASR submit 失败 status={status} msg={msg} logid={logid} body={resp.text[:300]}"
            )
            raise ServerErrorException(
                msg=f"语音识别任务提交失败：{msg or status or '未知错误'}"
            )

    async def _query_once(self, request_id: str) -> tuple[int, Optional[dict]]:
        self._check_config()
        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(60.0)) as client:
                resp = await client.post(
                    QUERY_URL, headers=self._headers(request_id), json={}
                )
        except httpx.RequestError as e:
            logger.error(f"火山 ASR query 网络错误: {e}")
            raise ServerErrorException(msg="语音识别查询失败")

        status_hdr = (resp.headers.get("X-Api-Status-Code") or "").strip()
        msg = resp.headers.get("X-Api-Message", "")
        try:
            code = int(status_hdr) if status_hdr else -1
        except ValueError:
            code = -1

        if code in PENDING_CODES:
            return code, None

        if code == SILENCE_CODE:
            raise BadRequestException(msg="未识别到有效语音内容（静音或过短）")

        if code != 20000000:
            logger.error(
                f"火山 ASR query 失败 code={code} msg={msg} body={resp.text[:500]}"
            )
            raise ServerErrorException(
                msg=f"语音识别失败：{msg or str(code)}"
            )

        try:
            data = resp.json() if resp.content else {}
        except Exception:
            data = {}
        return code, data if isinstance(data, dict) else {}

    @staticmethod
    def _extract_text(data: dict) -> str:
        result = data.get("result")
        if isinstance(result, dict):
            t = result.get("text")
            if isinstance(t, str):
                return t.strip()
        if isinstance(result, list) and result:
            first = result[0]
            if isinstance(first, dict):
                t = first.get("text")
                if isinstance(t, str):
                    return t.strip()
        return ""

    async def _poll_until_text(self, request_id: str) -> str:
        deadline = time.monotonic() + self.poll_timeout
        last_pending = False
        while time.monotonic() < deadline:
            code, data = await self._query_once(request_id)
            if code in PENDING_CODES:
                last_pending = True
                await asyncio.sleep(self.poll_interval)
                continue
            if data is None:
                await asyncio.sleep(self.poll_interval)
                continue
            text = self._extract_text(data)
            if text:
                return text
            if last_pending:
                await asyncio.sleep(self.poll_interval)
                continue
            break

        raise ServerErrorException(msg="语音识别超时，请稍后重试")

    async def transcribe_url(
        self,
        media_url: str,
        language: str = "zh-CN",
    ) -> str:
        """提交公网媒体 URL，轮询至完成，返回识别文本。"""
        last_err: ServerErrorException | None = None
        for fmt in self._submit_format_candidates(media_url):
            request_id = str(uuid.uuid4())
            try:
                await self._submit(media_url, request_id, language, fmt)
            except ServerErrorException as e:
                last_err = e
                if self._is_retryable_format_error(e):
                    logger.warning(f"火山 ASR submit format={fmt} 失败，换下一格式: {e}")
                    continue
                raise
            try:
                return await self._poll_until_text(request_id)
            except BadRequestException:
                raise
            except ServerErrorException as e:
                if self._is_retryable_format_error(e):
                    last_err = e
                    logger.warning(f"火山 ASR query format={fmt} 失败，换下一格式: {e}")
                    continue
                raise

        if last_err:
            if self._is_retryable_format_error(last_err):
                raise ServerErrorException(
                    msg=(
                        "语音识别无法解码该链接（火山：音频格式/转封装失败）。"
                        "「大模型录音文件识别」的 audio.url 需为可拉取的音频流；"
                        "抖音整段视频 MP4 常被拒绝。请确认已在火山控制台开通本能力且 AppId/Token 正确；"
                        "若仍失败，需使用纯音频地址或咨询火山是否支持该 CDN。"
                    )
                )
            raise last_err
        raise ServerErrorException(msg="语音识别任务失败，请稍后重试")


def get_volcengine_asr_client() -> VolcengineAsrClient:
    return VolcengineAsrClient()
