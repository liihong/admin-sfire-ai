"""
Inspiration Model - 灵感数据模型

定义灵感的数据结构，用于存储用户的灵感记录
支持与 User 和 Project 模型的关联
"""
import enum
import json
from datetime import datetime
from typing import Optional, List, TYPE_CHECKING
from sqlalchemy import (
    String,
    BigInteger,
    Boolean,
    Text,
    ForeignKey,
    Index,
    JSON,
    DateTime,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import BaseModel

if TYPE_CHECKING:
    from models.user import User
    from models.project import Project


class InspirationStatus(enum.Enum):
    """灵感状态枚举"""
    ACTIVE = "active"       # 活跃
    ARCHIVED = "archived"  # 归档
    DELETED = "deleted"    # 已删除（软删除）


class Inspiration(BaseModel):
    """
    灵感模型
    
    关联到 User 表，可选关联到 Project 表
    支持标签、置顶、生成内容等功能
    """
    __tablename__ = "inspirations"
    __table_args__ = (
        Index("ix_inspirations_user_status", "user_id", "status"),  # 用户ID和状态联合索引
        Index("ix_inspirations_project_id", "project_id"),          # 项目ID索引
        Index("ix_inspirations_created_at", "created_at"),         # 创建时间索引
        Index("ix_inspirations_pinned_created", "is_pinned", "created_at"),  # 置顶和时间联合索引
        {"comment": "灵感表"},
    )
    
    # === 关联字段 ===
    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        comment="用户ID",
    )
    
    project_id: Mapped[Optional[int]] = mapped_column(
        BigInteger,
        ForeignKey("projects.id", ondelete="SET NULL"),
        nullable=True,
        comment="项目ID（可选，关联到具体项目）",
    )
    
    # === 内容字段 ===
    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="灵感内容（限制500字符）",
    )
    
    tags: Mapped[Optional[dict]] = mapped_column(
        JSON,
        nullable=True,
        comment="标签数组（JSON格式，如 [\"#视频脚本\", \"#文案想法\"]）",
    )
    
    # === 状态字段 ===
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=InspirationStatus.ACTIVE.value,
        server_default="active",
        comment="状态：active-活跃, archived-归档, deleted-已删除",
    )
    
    is_pinned: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="0",
        comment="是否置顶",
    )
    
    # === 生成内容字段 ===
    generated_content: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="已生成的口播文案（可选）",
    )
    
    generated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True,
        comment="生成时间（可选）",
    )
    
    # === 关系定义 ===
    user: Mapped["User"] = relationship(
        "User",
        lazy="selectin",
    )
    
    project: Mapped[Optional["Project"]] = relationship(
        "Project",
        lazy="selectin",
    )
    
    def __repr__(self) -> str:
        return f"<Inspiration(id={self.id}, user_id={self.user_id}, content='{self.content[:30]}...')>"
    
    def get_tags_list(self) -> List[str]:
        """获取标签列表"""
        if isinstance(self.tags, list):
            return self.tags
        if isinstance(self.tags, str):
            try:
                return json.loads(self.tags)
            except json.JSONDecodeError:
                return []
        return []
    
    def set_tags_list(self, tags: List[str]) -> None:
        """设置标签列表"""
        self.tags = tags
    
    @property
    def is_active(self) -> bool:
        """是否活跃状态"""
        return self.status == InspirationStatus.ACTIVE.value
    
    @property
    def is_archived(self) -> bool:
        """是否已归档"""
        return self.status == InspirationStatus.ARCHIVED.value
    
    @property
    def is_deleted_status(self) -> bool:
        """是否已删除（软删除）"""
        return self.status == InspirationStatus.DELETED.value
    
    @property
    def has_generated_content(self) -> bool:
        """是否有已生成的内容"""
        return bool(self.generated_content and self.generated_content.strip())

