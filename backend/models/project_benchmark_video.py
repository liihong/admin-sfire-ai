"""
ProjectBenchmarkVideo - 对标账号视频缓存
"""
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, ForeignKey, Index, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import BaseModel

if TYPE_CHECKING:
    from models.project_benchmark import ProjectBenchmarkAccount


class ProjectBenchmarkVideo(BaseModel):
    __tablename__ = "project_benchmark_videos"
    __table_args__ = (
        UniqueConstraint("account_id", "aweme_id", name="uq_pbv_account_aweme"),
        Index("ix_pbv_tenant_id", "tenant_id"),
        Index("ix_pbv_project_account", "project_id", "account_id"),
        Index("ix_pbv_account_top_create", "account_id", "is_top", "create_time"),
        {"comment": "项目对标账号视频缓存"},
    )

    tenant_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("tenants.id", ondelete="RESTRICT"),
        nullable=False,
        default=1,
        comment="租户ID",
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
    account_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("project_benchmark_accounts.id", ondelete="CASCADE"),
        nullable=False,
        comment="对标账号ID",
    )

    aweme_id: Mapped[str] = mapped_column(String(64), nullable=False, comment="抖音作品ID")
    is_top: Mapped[int] = mapped_column(Integer, default=0, server_default="0", nullable=False, comment="是否置顶：1-置顶，0-普通")
    desc: Mapped[str] = mapped_column(String(2000), default="", server_default="", nullable=False, comment="文案")
    create_time: Mapped[int] = mapped_column(Integer, default=0, server_default="0", nullable=False, comment="发布时间戳")
    cover_url: Mapped[str] = mapped_column(String(1024), default="", server_default="", nullable=False, comment="封面图")
    digg_count: Mapped[int] = mapped_column(Integer, default=0, server_default="0", nullable=False, comment="点赞数")
    comment_count: Mapped[int] = mapped_column(Integer, default=0, server_default="0", nullable=False, comment="评论数")
    share_count: Mapped[int] = mapped_column(Integer, default=0, server_default="0", nullable=False, comment="分享数")
    collect_count: Mapped[int] = mapped_column(Integer, default=0, server_default="0", nullable=False, comment="收藏数")
    play_count: Mapped[int] = mapped_column(Integer, default=0, server_default="0", nullable=False, comment="播放数")
    duration: Mapped[int] = mapped_column(Integer, default=0, server_default="0", nullable=False, comment="时长秒")
    author_nickname: Mapped[str] = mapped_column(String(200), default="", server_default="", nullable=False, comment="作者昵称")
    author_avatar_url: Mapped[str] = mapped_column(String(1024), default="", server_default="", nullable=False, comment="作者头像")
    video_url: Mapped[str] = mapped_column(String(1024), default="", server_default="", nullable=False, comment="视频直链")
    share_url: Mapped[str] = mapped_column(String(1024), default="", server_default="", nullable=False, comment="分享链接")

    account: Mapped["ProjectBenchmarkAccount"] = relationship("ProjectBenchmarkAccount", lazy="selectin")

