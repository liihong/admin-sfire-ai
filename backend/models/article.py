"""
文章模型
文章类型存 sys_dict.dict_code=article_category 的字典项 item_value（01-04）
"""
from typing import Optional
from datetime import datetime
from sqlalchemy import (
    String,
    BigInteger,
    Boolean,
    Text,
    DateTime,
    Integer,
    JSON,
    Index,
)
from sqlalchemy.orm import Mapped, mapped_column

from models.base import BaseModel

# 与 sys_dict article_category 的 item_value 一致（首页各区块按此取值筛选）
ARTICLE_CATEGORY_BUSINESS = "01"   # 商业底牌
ARTICLE_CATEGORY_TRAFFIC = "02"   # 流量心法
ARTICLE_CATEGORY_MANUAL = "03"    # 实操手册
ARTICLE_CATEGORY_FOUNDER = "04"  # 创始人说

# 与迁移脚本默认字典项一致；接口返回 category_name 时以 sys_dict 为准，缺失时回退此表
ARTICLE_CATEGORY_LABELS: dict[str, str] = {
    ARTICLE_CATEGORY_BUSINESS: "商业底牌",
    ARTICLE_CATEGORY_TRAFFIC: "流量心法",
    ARTICLE_CATEGORY_MANUAL: "实操手册",
    ARTICLE_CATEGORY_FOUNDER: "创始人说",
}


class Article(BaseModel):
    """
    文章模型
    
    用于存储小程序首页的文章内容；类型由字典 article_category 维护
    """
    __tablename__ = "articles"
    __table_args__ = (
        Index("ix_articles_category", "category"),
        Index("ix_articles_is_published", "is_published"),
        Index("ix_articles_is_enabled", "is_enabled"),
        Index("ix_articles_sort_order", "sort_order"),
        Index("ix_articles_publish_time", "publish_time"),
        {"comment": "文章表"},
    )
    
    # === 基础字段 ===
    category: Mapped[str] = mapped_column(
        String(8),
        nullable=False,
        comment="文章类型（sys_dict article_category 的 item_value：01-04）",
    )

    author: Mapped[str] = mapped_column(
        String(128),
        nullable=False,
        default="Source Fire",
        server_default="Source Fire",
        comment="作者",
    )

    title: Mapped[str] = mapped_column(
        String(256),
        nullable=False,
        comment="文章标题",
    )
    
    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="文章内容（富文本）",
    )
    
    summary: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
        comment="文章摘要/简介",
    )
    
    cover_image: Mapped[Optional[str]] = mapped_column(
        String(512),
        nullable=True,
        comment="封面图URL",
    )
    
    tags: Mapped[Optional[dict]] = mapped_column(
        JSON,
        nullable=True,
        comment="标签数组（JSON格式，如 [\"标签1\", \"标签2\"]）",
    )
    
    sort_order: Mapped[int] = mapped_column(
        BigInteger,
        default=0,
        server_default="0",
        nullable=False,
        comment="排序顺序（数字越小越靠前）",
    )
    
    publish_time: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True,
        comment="发布时间",
    )
    
    view_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        server_default="0",
        nullable=False,
        comment="浏览量",
    )
    
    # === 状态字段 ===
    is_published: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        server_default="0",
        nullable=False,
        comment="是否已发布",
    )
    
    is_enabled: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        server_default="1",
        nullable=False,
        comment="是否启用",
    )
    
    def __repr__(self) -> str:
        return f"<Article(id={self.id}, title='{self.title}', category='{self.category}')>"

