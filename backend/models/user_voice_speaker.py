"""
用户音色映射模型
支持 C 端用户与 B 端管理员双端使用，通过 owner_type + owner_id 区分
"""
from sqlalchemy import String, BigInteger, Integer, Index, UniqueConstraint, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from models.base import BaseModel


class UserVoiceSpeaker(BaseModel):
    """
    用户音色映射表
    
    - owner_type='user': owner_id 对应 users.id（C 端小程序/PC 用户）
    - owner_type='admin': owner_id 对应 admin_users.id（B 端管理员）
    - 每个 owner 仅一条记录，唯一约束 (owner_type, owner_id)
    """
    __tablename__ = "user_voice_speakers"
    __table_args__ = (
        UniqueConstraint("tenant_id", "owner_type", "owner_id", name="uq_user_voice_speaker_tenant_owner"),
        Index("ix_user_voice_speakers_tenant_id", "tenant_id"),
        Index("ix_user_voice_speakers_owner", "owner_type", "owner_id"),
        {"comment": "用户音色映射表（工具包-声音复刻）"},
    )

    tenant_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("tenants.id", ondelete="RESTRICT"),
        nullable=False,
        default=1,
        comment="租户ID",
    )

    owner_type: Mapped[str] = mapped_column(
        String(16),
        nullable=False,
        comment="所有者类型: user(C端) | admin(B端)",
    )
    owner_id: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
        comment="所有者ID: users.id 或 admin_users.id",
    )
    speaker_id: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        comment="火山引擎 speaker_id",
    )
    train_version: Mapped[int] = mapped_column(
        Integer,
        default=0,
        server_default="0",
        nullable=False,
        comment="训练次数（每个音色最多 10 次）",
    )
    status: Mapped[str] = mapped_column(
        String(32),
        default="pending",
        nullable=False,
        comment="状态: pending | training | success | failed",
    )
