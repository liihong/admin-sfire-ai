"""
ProjectBenchmarkAccount - 项目对标抖音账号

每个项目可绑定多个对标账号（sec_uid），用于拉取最新作品列表等。
"""
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, Boolean, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import BaseModel

if TYPE_CHECKING:
    from models.project import Project
    from models.user import User


class ProjectBenchmarkAccount(BaseModel):
    """项目-对标抖音账号"""

    __tablename__ = "project_benchmark_accounts"
    __table_args__ = (
        UniqueConstraint("project_id", "sec_uid", name="uq_project_benchmark_sec_uid"),
        Index("ix_pba_project_id", "project_id"),
        Index("ix_pba_user_id", "user_id"),
        {"comment": "项目对标抖音账号"},
    )

    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        comment="所属用户ID",
    )
    project_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        comment="项目ID",
    )
    sec_uid: Mapped[str] = mapped_column(
        String(128),
        nullable=False,
        comment="抖音 sec_uid",
    )
    profile_url: Mapped[str] = mapped_column(
        String(1024),
        default="",
        server_default="",
        nullable=False,
        comment="用户填写的主页或分享链接",
    )
    nickname: Mapped[str] = mapped_column(
        String(200),
        default="",
        server_default="",
        nullable=False,
        comment="昵称（解析或同步缓存）",
    )
    avatar_url: Mapped[str] = mapped_column(
        String(1024),
        default="",
        server_default="",
        nullable=False,
        comment="头像 URL（缓存）",
    )
    signature: Mapped[str] = mapped_column(
        String(1000),
        default="",
        server_default="",
        nullable=False,
        comment="简介（缓存）",
    )
    follower_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        server_default="0",
        nullable=False,
        comment="粉丝数（缓存）",
    )
    following_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        server_default="0",
        nullable=False,
        comment="关注数（缓存）",
    )
    total_favorited: Mapped[int] = mapped_column(
        Integer,
        default=0,
        server_default="0",
        nullable=False,
        comment="获赞总数（缓存）",
    )
    aweme_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        server_default="0",
        nullable=False,
        comment="作品数（缓存）",
    )
    remark: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="备注",
    )
    is_enabled: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        server_default="1",
        nullable=False,
        comment="是否启用",
    )

    project: Mapped["Project"] = relationship(
        "Project",
        lazy="selectin",
    )
    user: Mapped["User"] = relationship(
        "User",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<ProjectBenchmarkAccount(id={self.id}, project_id={self.project_id}, sec_uid={self.sec_uid!r})>"
