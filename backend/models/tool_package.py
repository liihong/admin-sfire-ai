"""
便捷工具包配置模型
Admin / Client 共用元数据，具体能力由 services/tools 与各路由实现
"""
from typing import Optional

from sqlalchemy import Index, Integer, String, Text, SmallInteger, UniqueConstraint, BigInteger, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from models.base import BaseModel


class ToolPackage(BaseModel):
    """
    工具包配置表

    code：URL 片段（如 voice-clone），与前端路由、toolRegistry 键一致
    """

    __tablename__ = "tool_packages"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_tool_packages_tenant_code"),
        Index("ix_tool_packages_tenant_id", "tenant_id"),
        Index("ix_tool_packages_status_sort", "status", "sort_order"),
        {"comment": "便捷工具包配置表"},
    )

    tenant_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("tenants.id", ondelete="RESTRICT"),
        nullable=False,
        default=1,
        comment="租户ID",
    )

    code: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        comment="唯一标识（同租户内路由片段唯一，如 voice-clone）",
    )
    name: Mapped[str] = mapped_column(String(128), nullable=False, comment="展示名称")
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="描述")
    icon: Mapped[str] = mapped_column(
        String(64),
        default="Box",
        server_default="Box",
        nullable=False,
        comment="Element Plus 图标名",
    )
    sort_order: Mapped[int] = mapped_column(
        Integer,
        default=0,
        server_default="0",
        nullable=False,
        comment="排序（越小越靠前）",
    )
    status: Mapped[int] = mapped_column(
        SmallInteger,
        default=1,
        server_default="1",
        nullable=False,
        comment="状态：0-禁用, 1-启用",
    )

    def __repr__(self) -> str:
        return f"<ToolPackage(id={self.id}, code='{self.code}')>"
