"""
Copywriting Library Model - 文案库数据模型

该表用于存储用户在某个IP(Project)下沉淀的可复用文案素材。
注意：此功能为独立业务线，不依赖 inspirations / AI对话等体系。
"""

import enum
import json
from datetime import datetime
from typing import Optional, List, TYPE_CHECKING

from sqlalchemy import (
    String,
    BigInteger,
    Text,
    ForeignKey,
    Index,
    JSON,
    Integer,
    DateTime,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import BaseModel

if TYPE_CHECKING:
    from models.user import User
    from models.project import Project


class CopywritingEntryStatus(enum.Enum):
    """文案条目状态枚举（面向拍摄/发布流程）"""

    DRAFT = "draft"  # 草稿
    TODO = "todo"  # 待拍摄
    PUBLISHED = "published"  # 已发布
    ARCHIVED = "archived"  # 归档


class CopywritingLibraryEntry(BaseModel):
    """
    文案库条目

    归属关系：
    - user_id: 所属用户
    - project_id: 所属IP项目（必填，用于“每个IP一套文案库”隔离）
    """

    __tablename__ = "copywriting_library_entries"
    __table_args__ = (
        Index("ix_cle_user_id", "user_id"),
        Index("ix_cle_project_id", "project_id"),
        Index("ix_cle_user_project", "user_id", "project_id"),
        Index("ix_cle_status", "status"),
        Index("ix_cle_created_at", "created_at"),
        {"comment": "文案库条目表（按用户+项目隔离）"},
    )

    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        comment="用户ID",
    )

    project_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        comment="项目/IP ID",
    )

    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="文案正文",
    )

    tags: Mapped[Optional[dict]] = mapped_column(
        JSON,
        nullable=True,
        comment="标签数组（JSON格式，如 [\"种草\", \"开场\"]）",
    )

    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=CopywritingEntryStatus.TODO.value,
        server_default=CopywritingEntryStatus.TODO.value,
        comment="状态：draft/todo/published/archived",
    )

    # ===== 发布后数据（用户补录）=====
    views: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        default=None,
        comment="播放/曝光量（可选）",
    )
    likes: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        default=None,
        comment="点赞数（可选）",
    )
    comments: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        default=None,
        comment="评论数（可选）",
    )
    shares: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        default=None,
        comment="转发/分享数（可选）",
    )

    published_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True,
        default=None,
        comment="发布时间（可选，补录数据时可写入）",
    )

    # ===== 关系（selectin 避免N+1）=====
    user: Mapped["User"] = relationship("User", lazy="selectin")
    project: Mapped["Project"] = relationship("Project", lazy="selectin")

    def get_tags_list(self) -> List[str]:
        """获取标签列表（兼容 JSON / 字符串异常数据）"""
        if isinstance(self.tags, list):
            return [str(x) for x in self.tags if str(x).strip()]
        if isinstance(self.tags, str):
            try:
                raw = json.loads(self.tags)
                if isinstance(raw, list):
                    return [str(x) for x in raw if str(x).strip()]
            except json.JSONDecodeError:
                return []
        return []

    def set_tags_list(self, tags: List[str]) -> None:
        """设置标签列表（会做基础清洗）"""
        cleaned = []
        for t in tags or []:
            s = str(t).strip()
            if not s:
                continue
            cleaned.append(s)
        self.tags = cleaned

