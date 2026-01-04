"""
Project Model - 项目（IP）数据模型

定义项目/IP的数据结构，用于多项目管理
支持与 User 模型的关联
"""
import json
from typing import Optional, List, TYPE_CHECKING
from sqlalchemy import (
    String,
    BigInteger,
    Boolean,
    ForeignKey,
    Index,
    JSON,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.user import User


class Project(BaseModel):
    """
    项目/IP 主模型
    
    关联到 User 表，支持多项目管理
    """
    __tablename__ = "projects"
    __table_args__ = (
        Index("ix_projects_user_id", "user_id"),              # user_id 索引
        Index("ix_projects_updated_at", "updated_at"),        # updated_at 索引（排序优化）
        Index("ix_projects_is_deleted", "is_deleted"),        # is_deleted 索引（查询优化）
        {"comment": "项目/IP表"},
    )
    
    # === 关联字段 ===
    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        comment="关联用户ID",
    )
    
    # === 基本信息 ===
    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="项目名称，如'李医生科普IP'",
    )
    
    industry: Mapped[str] = mapped_column(
        String(50),
        default="通用",
        server_default="通用",
        nullable=False,
        comment="赛道，如'医疗健康'、'教育培训'等",
    )
    
    avatar_letter: Mapped[str] = mapped_column(
        String(10),
        default="",
        server_default="",
        nullable=False,
        comment="项目首字母/头像显示字符",
    )
    
    avatar_color: Mapped[str] = mapped_column(
        String(20),
        default="#3B82F6",
        server_default="#3B82F6",
        nullable=False,
        comment="头像背景色",
    )
    
    # === 人设配置（JSON存储） ===
    persona_settings: Mapped[dict] = mapped_column(
        JSON,
        default=dict,
        server_default="{}",
        nullable=False,
        comment="IP人设配置（JSON格式）",
    )
    
    # === 状态字段 ===
    is_deleted: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        server_default="0",
        nullable=False,
        comment="是否已删除（软删除）",
    )
    
    # === 关系定义 ===
    user: Mapped["User"] = relationship(
        "User",
        back_populates="projects",
        lazy="selectin",
    )
    
    def __repr__(self) -> str:
        return f"<Project(id={self.id}, name='{self.name}', user_id={self.user_id})>"
    
    def get_persona_settings_dict(self) -> dict:
        """获取人设配置字典"""
        if isinstance(self.persona_settings, dict):
            return self.persona_settings
        if isinstance(self.persona_settings, str):
            try:
                return json.loads(self.persona_settings)
            except json.JSONDecodeError:
                return {}
        return {}

