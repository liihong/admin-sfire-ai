"""
C 端声音复刻接口
"""
import base64
from fastapi import APIRouter, Depends, UploadFile, File
from pydantic import BaseModel, Field

from db import get_db
from core.deps import get_current_miniprogram_user
from models.user import User
from services.tools.voice_clone_service import VoiceCloneService
from utils.response import success
from utils.exceptions import BadRequestException

router = APIRouter()

# 允许的音频格式
ALLOWED_AUDIO_TYPES = {"audio/wav", "audio/wave", "audio/x-wav", "audio/mpeg", "audio/mp3"}
MAX_AUDIO_SIZE = 10 * 1024 * 1024  # 10MB


class SynthesizeRequest(BaseModel):
    """合成请求"""
    text: str = Field(..., min_length=1, max_length=2000, description="待合成文本")
    speaker_id: str | None = Field(default=None, description="音色 ID，不传则用当前用户绑定的")


@router.post("/upload", summary="上传训练音频")
async def upload_audio(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_miniprogram_user),
    db=Depends(get_db),
):
    """
    上传 5 秒以上音频，用于训练专属音色
    支持 wav、mp3 格式，最大 10MB
    """
    if file.content_type and file.content_type not in ALLOWED_AUDIO_TYPES:
        raise BadRequestException(msg="仅支持 wav、mp3 格式")
    content = await file.read()
    if len(content) > MAX_AUDIO_SIZE:
        raise BadRequestException(msg="文件大小不能超过 10MB")
    ext = (file.filename or "").split(".")[-1].lower()
    audio_format = "wav" if ext in ("wav", "wave") else "mp3"
    svc = VoiceCloneService(db)
    data = await svc.upload_and_train(
        owner_type="user",
        owner_id=current_user.id,
        audio_content=content,
        audio_format=audio_format,
    )
    return success(data=data, msg="上传成功，正在训练")


@router.get("/status", summary="查询训练状态")
async def get_status(
    current_user: User = Depends(get_current_miniprogram_user),
    db=Depends(get_db),
):
    """查询当前用户的音色训练状态"""
    svc = VoiceCloneService(db)
    data = await svc.get_status(owner_type="user", owner_id=current_user.id)
    return success(data=data, msg="查询成功")


@router.post("/synthesize", summary="文本转语音")
async def synthesize(
    body: SynthesizeRequest,
    current_user: User = Depends(get_current_miniprogram_user),
    db=Depends(get_db),
):
    """使用已训练音色将文本转为语音，返回 base64 音频"""
    svc = VoiceCloneService(db)
    audio_bytes, _ = await svc.synthesize(
        owner_type="user",
        owner_id=current_user.id,
        text=body.text,
        speaker_id=body.speaker_id,
    )
    b64 = base64.b64encode(audio_bytes).decode("utf-8")
    return success(data={"audio_base64": b64, "format": "mp3"}, msg="合成成功")
