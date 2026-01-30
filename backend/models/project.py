"""
Project Model - 项目（IP）数据模型

定义项目/IP的数据结构，用于多项目管理
支持与 User 模型的关联
"""
import json
import enum
from typing import Optional, List, TYPE_CHECKING
from sqlalchemy import (
    String,
    BigInteger,
    Boolean,
    Integer,
    ForeignKey,
    Index,
    JSON,
    Text,
    Enum as SQLEnum,
    TypeDecorator,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import BaseModel
from utils.json_utils import json_dumps, json_loads


class UnicodeJSON(TypeDecorator):
    """
    自定义 JSON 类型，支持中文（ensure_ascii=False）
    
    对于MySQL，JSON类型字段的序列化由驱动处理，我们需要重写序列化逻辑
    使用Text类型存储JSON字符串，确保中文不被转义
    """
    impl = Text
    cache_ok = True
    
    def process_bind_param(self, value, dialect):
        """序列化时使用 ensure_ascii=False"""
        if value is not None:
            if isinstance(value, dict):
                return json_dumps(value)
            return value
        return None
    
    def process_result_value(self, value, dialect):
        """反序列化时正常解析"""
        if value is not None:
            if isinstance(value, str):
                try:
                    return json_loads(value)
                except (json.JSONDecodeError, TypeError):
                    return {}
            return value if isinstance(value, dict) else {}
        return {}

if TYPE_CHECKING:
    from models.user import User


class ProjectStatus(enum.Enum):
    """项目状态枚举"""
    ACTIVE = 1      # 正常使用
    FROZEN = 2      # 已冻结（降级导致）


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
        Index("ix_projects_status", "status"),                # status 索引（状态筛选）
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
    
    # === 人设配置（JSON存储，支持中文） ===
    persona_settings: Mapped[dict] = mapped_column(
        UnicodeJSON,
        default=dict,
        server_default="{}",
        nullable=False,
        comment="IP人设配置（JSON格式）",
    )
    
    # === Master Prompt（独立字段，不限制长度） ===
    master_prompt: Mapped[Optional[str]] = mapped_column(
        Text,
        default=None,
        nullable=True,
        comment="Master Prompt（IP核心特征描述，由Agent自动生成）",
    )
    
    # === 状态字段 ===
    status: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=ProjectStatus.ACTIVE.value,
        server_default="1",
        comment="状态：1-正常, 2-已冻结",
    )
    
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
                return json_loads(self.persona_settings)
            except (json.JSONDecodeError, TypeError):
                return {}
        return {}
    
    @property
    def is_frozen(self) -> bool:
        """是否已冻结"""
        return self.status == ProjectStatus.FROZEN.value
    
    @property
    def is_active_status(self) -> bool:
        """是否正常状态"""
        return self.status == ProjectStatus.ACTIVE.value

