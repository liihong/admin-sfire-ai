"""
技能库模型
用于管理可复用的技能模板
"""
from typing import Optional
from sqlalchemy import String, Integer, Text, Index
from sqlalchemy.orm import Mapped, mapped_column

from models.base import BaseModel


class SkillLibrary(BaseModel):
    """
    技能库模型

    核心字段:
        - name: 技能名称
        - category: 分类（model/hook/rule/audit）
        - meta_description: 特征描述（用于路由匹配）
        - content: 实际Prompt片段
        - status: 状态（1-启用, 0-禁用）
    """
    __tablename__ = "skill_library"
    __table_args__ = (
        Index("ix_skill_library_category", "category"),
        Index("ix_skill_library_status", "status"),
        {"comment": "技能库表"},
    )

    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="技能名称",
    )

    category: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="分类：model/hook/rule/audit",
    )

    meta_description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="特征简述(路由用)",
    )

    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="实际Prompt片段",
    )

    status: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
        comment="状态：1-启用 0-禁用",
    )

    def __repr__(self) -> str:
        return f"<SkillLibrary(id={self.id}, name={self.name}, category={self.category})>"

    @property
    def is_active(self) -> bool:
        """是否启用"""
        return self.status == 1
