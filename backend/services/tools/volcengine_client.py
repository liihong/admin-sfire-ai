"""
火山引擎豆包语音 API 客户端
工具包-声音复刻：纯 HTTP 调用，无业务逻辑
参考文档：https://www.volcengine.com/docs/6561/1305191
"""
import base64
import json
import os
from typing import Optional

import httpx
from loguru import logger

from core.config import settings
from utils.exceptions import BadRequestException, ServerErrorException

# #region agent log
def _debug_log(msg: str, data: dict, hypothesis_id: str = "A") -> None:
    try:
        log_path = os.path.join(os.path.dirname(__file__), "..", "..", "..", "debug-02fb33.log")
        abs_path = os.path.abspath(log_path)
        entry = json.dumps({"sessionId": "02fb33", "hypothesisId": hypothesis_id, "location": "volcengine_client.py", "message": msg, "data": data, "timestamp": __import__("time").time() * 1000}) + "\n"
        with open(abs_path, "a", encoding="utf-8") as f:
            f.write(entry)
    except Exception:
        pass
# #endregion


class VolcengineVoiceClient:
    """火山引擎声音复刻 API 客户端
    参考：https://www.volcengine.com/docs/6561/1305191
    """

    BASE_URL = "https://openspeech.bytedance.com"
    UPLOAD_PATH = "/api/v1/mega_tts/audio/upload"
    # Resource-Id: seed-icl-1.0(声音复刻1.0) / seed-icl-2.0(声音复刻2.0)
    RESOURCE_ID_ICL1 = "seed-icl-1.0"
    RESOURCE_ID_ICL2 = "seed-icl-2.0"

    def __init__(self) -> None:
        self.app_id = settings.VOLCENGINE_APP_ID
        self.access_token = settings.VOLCENGINE_ACCESS_TOKEN
        # License（API Key）与 Access Token 不同，声音复刻接口的 license 参数需从控制台 API Key 管理获取
        self.license = getattr(settings, "VOLCENGINE_LICENSE", None) or settings.VOLCENGINE_ACCESS_TOKEN
        self.base_url = getattr(settings, "VOLCENGINE_VOICE_BASE_URL", self.BASE_URL)
        # Resource-Id: seed-icl-1.0 或 seed-icl-2.0
        self.resource_id = getattr(
            settings, "VOLCENGINE_VOICE_RESOURCE_ID", None
        ) or self.RESOURCE_ID_ICL1

    def _check_config(self) -> None:
        """检查必要配置"""
        if not self.app_id or not self.access_token:
            raise BadRequestException(
                msg="火山引擎语音服务未配置，请联系管理员配置 VOLCENGINE_APP_ID 和 VOLCENGINE_ACCESS_TOKEN"
            )
        if not self.license or not str(self.license).strip():
            logger.warning(
                "VOLCENGINE_LICENSE 未配置或为空，声音复刻接口会报 403。"
                "请在火山引擎控制台-API Key 管理中创建 API Key，并配置到 .env 的 VOLCENGINE_LICENSE"
            )
            raise BadRequestException(
                msg="火山引擎声音复刻未配置 License，请在控制台 API Key 管理中获取并配置 VOLCENGINE_LICENSE"
            )

    def _headers(self) -> dict:
        """请求头：Bearer;{token} 或 ApiKey;{license}（分号分隔），Resource-Id 必填
        声音复刻工具包接口可能要求使用 API Key 鉴权，否则会报 403 parameter license not found
        """
        headers = {
            "Resource-Id": self.resource_id,
            "Content-Type": "application/json",
        }
        # 优先使用 API Key（license）鉴权：声音复刻 Upload 接口要求 license，部分环境需放在 Authorization 头
        use_api_key_auth = getattr(settings, "VOLCENGINE_USE_API_KEY_AUTH", None)
        if use_api_key_auth and self.license:
            headers["Authorization"] = f"ApiKey;{self.license}"
        else:
            headers["Authorization"] = f"Bearer;{self.access_token}"
            if self.license:
                headers["License"] = self.license  # 同时放在请求头，部分接口需要
        return headers

    async def upload_audio(
        self,
        speaker_id: str,
        audio_content: bytes,
        audio_format: str = "wav",
        language: int = 0,
        model_type: int = 1,
    ) -> dict:
        """
        上传音频训练音色

        Args:
            speaker_id: 火山引擎 speaker_id
            audio_content: 音频二进制内容
            audio_format: 音频格式 wav/mp3/ogg/m4a/aac/pcm
            language: 0=中文 1=英文 2=日语 等
            model_type: 1=ICL1.0 2=DiT标准版 3=DiT还原版 4=ICL2.0

        Returns:
            火山引擎响应
        """
        self._check_config()
        audio_b64 = base64.b64encode(audio_content).decode("utf-8")
        # 按文档：audios 为对象数组，audio_bytes+audio_format
        payload = {
            "appid": self.app_id,
            "speaker_id": speaker_id,
            "license": self.license,
            "audios": [
                {"audio_bytes": audio_b64, "audio_format": audio_format}
            ],
            "source": 2,  # 固定值：2
            "language": language,
            "model_type": model_type,
            "extra_params": json.dumps({"voice_clone_denoise_model_id": ""}),
        }
        url = f"{self.base_url.rstrip('/')}{self.UPLOAD_PATH}"
        headers = self._headers()
        # #region agent log
        _debug_log("upload_audio REQUEST", {"url": url, "headers_keys": list(headers.keys()), "auth_prefix": headers.get("Authorization", "")[:15] + "..." if headers.get("Authorization") else None, "resource_id": headers.get("Resource-Id"), "payload_keys": list(payload.keys()), "appid_type": type(payload["appid"]).__name__, "source_type": type(payload["source"]).__name__, "language_type": type(payload["language"]).__name__, "model_type_val": payload["model_type"]}, "A")
        # #endregion
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                resp = await client.post(url, headers=headers, json=payload)
                # #region agent log
                _debug_log("upload_audio RESPONSE", {"status_code": resp.status_code, "response_body": resp.text[:500] if resp.text else None}, "B")
                # #endregion
                resp.raise_for_status()
                data = resp.json()
                if data.get("code") != 0 and data.get("code") is not None:
                    raise BadRequestException(msg=data.get("message", "上传失败"))
                return data
        except httpx.HTTPStatusError as e:
            # #region agent log
            _debug_log("upload_audio HTTP_ERROR", {"status_code": getattr(e, "response", None) and e.response.status_code, "response_text": getattr(e, "response", None) and e.response.text[:800]}, "C")
            # #endregion
            logger.error(f"火山引擎 Upload 请求失败: {e.response.status_code} {e.response.text}")
            raise ServerErrorException(msg="火山引擎服务异常，请稍后重试")
        except httpx.RequestError as e:
            logger.error(f"火山引擎 Upload 请求错误: {e}")
            raise ServerErrorException(msg="网络请求失败，请检查配置")

    async def get_train_status(self, speaker_id: str) -> dict:
        """
        查询音色训练状态

        Args:
            speaker_id: 火山引擎 speaker_id

        Returns:
            状态信息，含 status、version 等
        """
        self._check_config()
        # 使用 BatchListMegaTTSTrainStatus 接口
        url = f"{self.base_url.rstrip('/')}/api/v1/mega_tts/train/status"
        payload = {
            "appid": self.app_id,
            "speaker_ids": [speaker_id],
            "license": self.license,
        }
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(url, headers=self._headers(), json=payload)
                resp.raise_for_status()
                data = resp.json()
                items = data.get("data", {}).get("items", [])
                if items:
                    return items[0]
                return {"speaker_id": speaker_id, "status": "unknown"}
        except httpx.HTTPStatusError as e:
            logger.error(f"火山引擎 查询状态 失败: {e.response.status_code} {e.response.text}")
            raise ServerErrorException(msg="查询训练状态失败")
        except httpx.RequestError as e:
            logger.error(f"火山引擎 查询状态 请求错误: {e}")
            raise ServerErrorException(msg="网络请求失败")

    async def synthesize(
        self,
        speaker_id: str,
        text: str,
        format: str = "mp3",
    ) -> bytes:
        """
        文本转语音

        Args:
            speaker_id: 火山引擎 speaker_id
            text: 待合成文本
            format: 输出格式 mp3/wav

        Returns:
            音频二进制内容
        """
        self._check_config()
        # 大模型语音合成 HTTP 接口，参考文档 1598757
        url = f"{self.base_url.rstrip('/')}/api/v3/tts"
        payload = {
            "app": {"appid": self.app_id, "token": self.access_token, "cluster": "volcano_tts"},
            "user": {"uid": "tools-voice-clone"},
            "audio": {"format": format, "rate": 24000},
            "request": {
                "reqid": f"voice-clone-{speaker_id[:8]}",
                "text": text,
                "text_type": "plain",
                "operation": "query",
                "voice_type": speaker_id,
                "license": self.license,
            },
        }
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                resp = await client.post(url, headers={"Content-Type": "application/json"}, json=payload)
                resp.raise_for_status()
                return resp.content
        except httpx.HTTPStatusError as e:
            logger.error(f"火山引擎 TTS 失败: {e.response.status_code} {e.response.text[:500]}")
            raise ServerErrorException(msg="语音合成失败，请检查音色是否已训练完成")
        except httpx.RequestError as e:
            logger.error(f"火山引擎 TTS 请求错误: {e}")
            raise ServerErrorException(msg="网络请求失败")
