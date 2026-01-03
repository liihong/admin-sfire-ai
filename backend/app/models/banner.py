"""
Banner模型
用于管理小程序首页的Banner轮播图
"""
import enum
from typing import Optional
from datetime import datetime
from sqlalchemy import (
    String,
    BigInteger,
    Boolean,
    DateTime,
    Index,
    Enum as SQLEnum,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class LinkType(enum.Enum):
    """链接类型枚举"""
    NONE = "none"           # 无链接
    INTERNAL = "internal"   # 内部链接
    EXTERNAL = "external"   # 外部链接


class BannerPosition(enum.Enum):
    """Banner位置枚举"""
    HOME_TOP = "home_top"           # 首页顶部
    HOME_MIDDLE = "home_middle"     # 首页中部
    HOME_BOTTOM = "home_bottom"     # 首页底部


class Banner(BaseModel):
    """
    Banner模型
    
    用于存储小程序首页的Banner轮播图信息
    """
    __tablename__ = "banners"
    __table_args__ = (
        Index("ix_banners_position", "position"),
        Index("ix_banners_sort_order", "sort_order"),
        Index("ix_banners_is_enabled", "is_enabled"),
        {"comment": "Banner表"},
    )
    
    # === 基础字段 ===
    title: Mapped[str] = mapped_column(
        String(128),
        nullable=False,
        comment="Banner标题",
    )
    
    image_url: Mapped[str] = mapped_column(
        String(512),
        nullable=False,
        comment="图片URL",
    )
    
    link_url: Mapped[Optional[str]] = mapped_column(
        String(512),
        nullable=True,
        comment="跳转链接",
    )
    
    link_type: Mapped[LinkType] = mapped_column(
        SQLEnum(LinkType, values_callable=lambda x: [e.value for e in x]),
        default=LinkType.NONE,
        server_default="none",
        nullable=False,
        comment="链接类型: none-无链接, internal-内部链接, external-外部链接",
    )
    
    sort_order: Mapped[int] = mapped_column(
        BigInteger,
        default=0,
        server_default="0",
        nullable=False,
        comment="排序顺序（数字越小越靠前）",
    )
    
    position: Mapped[BannerPosition] = mapped_column(
        SQLEnum(BannerPosition, values_callable=lambda x: [e.value for e in x]),
        default=BannerPosition.HOME_TOP,
        server_default="home_top",
        nullable=False,
        comment="Banner位置: home_top-首页顶部, home_middle-首页中部, home_bottom-首页底部",
    )
    
    # === 时间控制字段 ===
    start_time: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True,
        comment="开始时间（可选）",
    )
    
    end_time: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True,
        comment="结束时间（可选）",
    )
    
    # === 状态字段 ===
    is_enabled: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        server_default="1",
        nullable=False,
        comment="是否启用",
    )
    
    def __repr__(self) -> str:
        return f"<Banner(id={self.id}, title='{self.title}', position='{self.position.value}')>"

