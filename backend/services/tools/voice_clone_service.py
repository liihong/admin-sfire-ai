"""
声音复刻业务服务
工具包-声音复刻：编排逻辑、owner 解析、UserVoiceSpeaker 管理
"""
from typing import Optional, Tuple

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.user_voice_speaker import UserVoiceSpeaker
from services.tools.volcengine_client import VolcengineVoiceClient
from utils.exceptions import BadRequestException


class VoiceCloneService:
    """声音复刻业务服务"""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.client = VolcengineVoiceClient()

    def _parse_speaker_ids(self) -> list[str]:
        """从配置解析音色 ID 池"""
        from core.config import settings

        ids_str = settings.VOLCENGINE_SPEAKER_IDS or ""
        return [x.strip() for x in ids_str.split(",") if x.strip()]

    async def _get_or_create_speaker(
        self,
        owner_type: str,
        owner_id: int,
    ) -> UserVoiceSpeaker:
        """
        获取或创建用户的音色映射
        若不存在则从池中分配新 speaker_id
        """
        result = await self.db.execute(
            select(UserVoiceSpeaker).where(
                UserVoiceSpeaker.owner_type == owner_type,
                UserVoiceSpeaker.owner_id == owner_id,
            )
        )
        record = result.scalar_one_or_none()
        if record:
            return record

        # 从池中找未被占用的 speaker_id
        pool = self._parse_speaker_ids()
        if not pool:
            raise BadRequestException(
                msg="音色资源已用完，请联系管理员在配置中添加 VOLCENGINE_SPEAKER_IDS"
            )

        used = await self.db.execute(
            select(UserVoiceSpeaker.speaker_id).where(
                UserVoiceSpeaker.speaker_id.in_(pool)
            )
        )
        used_ids = set(used.scalars().all())
        available = [s for s in pool if s not in used_ids]
        if not available:
            raise BadRequestException(
                msg="音色资源已用完，请联系管理员购买更多音色"
            )

        speaker_id = available[0]
        record = UserVoiceSpeaker(
            owner_type=owner_type,
            owner_id=owner_id,
            speaker_id=speaker_id,
            train_version=0,
            status="pending",
        )
        self.db.add(record)
        await self.db.flush()
        return record

    async def upload_and_train(
        self,
        owner_type: str,
        owner_id: int,
        audio_content: bytes,
        audio_format: str = "wav",
    ) -> dict:
        """
        上传音频并触发训练

        Returns:
            { speaker_id, status, train_version }
        """
        record = await self._get_or_create_speaker(owner_type, owner_id)
        if record.train_version >= 10:
            raise BadRequestException(msg="该音色已达到最大训练次数（10次）")

        await self.client.upload_audio(
            speaker_id=record.speaker_id,
            audio_content=audio_content,
            audio_format=audio_format,
        )
        record.status = "training"
        record.train_version += 1
        await self.db.flush()
        return {
            "speaker_id": record.speaker_id,
            "status": record.status,
            "train_version": record.train_version,
        }

    async def get_status(
        self,
        owner_type: str,
        owner_id: int,
    ) -> dict:
        """查询当前用户的音色训练状态"""
        result = await self.db.execute(
            select(UserVoiceSpeaker).where(
                UserVoiceSpeaker.owner_type == owner_type,
                UserVoiceSpeaker.owner_id == owner_id,
            )
        )
        record = result.scalar_one_or_none()
        if not record:
            return {"has_speaker": False, "status": "pending", "speaker_id": None}

        # 可选：同步火山引擎最新状态
        try:
            remote = await self.client.get_train_status(record.speaker_id)
            status = remote.get("status", record.status)
            if status in ("success", "failed"):
                record.status = status
                await self.db.flush()
        except Exception:
            pass

        return {
            "has_speaker": True,
            "speaker_id": record.speaker_id,
            "status": record.status,
            "train_version": record.train_version,
        }

    async def synthesize(
        self,
        owner_type: str,
        owner_id: int,
        text: str,
        speaker_id: Optional[str] = None,
    ) -> Tuple[bytes, str]:
        """
        文本转语音

        Returns:
            (audio_bytes, content_type)
        """
        sid = speaker_id
        if not sid:
            result = await self.db.execute(
                select(UserVoiceSpeaker).where(
                    UserVoiceSpeaker.owner_type == owner_type,
                    UserVoiceSpeaker.owner_id == owner_id,
                )
            )
            record = result.scalar_one_or_none()
            if not record:
                raise BadRequestException(msg="请先上传音频完成音色训练")
            if record.status != "success":
                raise BadRequestException(msg="音色尚未训练完成，请稍后再试")
            sid = record.speaker_id

        audio_bytes = await self.client.synthesize(speaker_id=sid, text=text)
        return audio_bytes, "audio/mpeg"
