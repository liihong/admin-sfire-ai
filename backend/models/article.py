"""
文章模型
用于管理小程序首页的文章内容（创始人故事、运营干货、客户案例）
"""
import enum
from typing import Optional, List
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
    Enum as SQLEnum,
)
from sqlalchemy.orm import Mapped, mapped_column

from models.base import BaseModel


class ArticleCategory(enum.Enum):
    """文章类型枚举"""
    FOUNDER_STORY = "founder_story"      # 创始人故事
    OPERATION_ARTICLE = "operation_article"  # 运营干货
    CUSTOMER_CASE = "customer_case"      # 客户案例
    ANNOUNCEMENT = "announcement"        # 公告


class Article(BaseModel):
    """
    文章模型
    
    用于存储小程序首页的文章内容
    支持三种类型：创始人故事、运营干货、客户案例
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
    category: Mapped[ArticleCategory] = mapped_column(
        SQLEnum(ArticleCategory, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        comment="文章类型: founder_story-创始人故事, operation_article-运营干货, customer_case-客户案例, announcement-公告",
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
        return f"<Article(id={self.id}, title='{self.title}', category='{self.category.value}')>"

