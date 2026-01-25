"""
快捷入口配置模型
用于管理"今天拍点啥"和"快捷指令库"的动态配置
"""
import enum
from typing import Optional
from sqlalchemy import (
    String,
    BigInteger,
    Integer,
    Text,
    Index,
    Enum as SQLEnum,
)
from sqlalchemy.orm import Mapped, mapped_column

from models.base import BaseModel


class EntryType(enum.Enum):
    """入口类型枚举"""
    CATEGORY = "category"      # 今天拍点啥
    COMMAND = "command"        # 快捷指令库


class ActionType(enum.Enum):
    """动作类型枚举"""
    AGENT = "agent"            # 调用 Agent（通过 agent_id）
    SKILL = "skill"            # 调用 Skill（通过 skill_id）
    PROMPT = "prompt"          # 硬编码的 System Prompt


class EntryTag(enum.Enum):
    """入口标签枚举"""
    NONE = "none"              # 无标签
    NEW = "new"                # 新上线
    HOT = "hot"                # 最热门


class QuickEntry(BaseModel):
    """
    快捷入口配置表
    
    用于统一管理"今天拍点啥"和"快捷指令库"的配置
    """
    __tablename__ = "quick_entries"
    __table_args__ = (
        Index("ix_quick_entries_type", "type"),
        Index("ix_quick_entries_status", "status"),
        Index("ix_quick_entries_priority", "priority"),
        Index("ix_quick_entries_tag", "tag"),
        Index("ix_quick_entries_unique_key", "unique_key", unique=True),
        {"comment": "快捷入口配置表"},
    )
    
    # === 基础标识字段 ===
    unique_key: Mapped[str] = mapped_column(
        String(64),
        unique=True,
        nullable=False,
        comment="唯一标识（如：story, opinion, agent_001）",
    )
    
    type: Mapped[EntryType] = mapped_column(
        SQLEnum(EntryType, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        comment="入口类型: category-今天拍点啥, command-快捷指令库",
    )
    
    # === 显示字段 ===
    title: Mapped[str] = mapped_column(
        String(128),
        nullable=False,
        comment="标题（主标题）",
    )
    
    subtitle: Mapped[Optional[str]] = mapped_column(
        String(256),
        nullable=True,
        comment="副标题（描述信息）",
    )
    
    icon_class: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        comment="图标类名（RemixIcon 类名，如：ri-book-line）",
    )
    
    bg_color: Mapped[Optional[str]] = mapped_column(
        String(16),
        nullable=True,
        comment="背景色（十六进制颜色，如：#F69C0E）",
    )
    
    # === 动作配置字段 ===
    action_type: Mapped[ActionType] = mapped_column(
        SQLEnum(ActionType, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        comment="动作类型: agent-调用Agent, skill-调用Skill, prompt-硬编码Prompt",
    )
    
    # action_value 根据 action_type 存储不同内容：
    # - agent: 存储 agent_id (整数)
    # - skill: 存储 skill_id (整数)
    # - prompt: 存储 System Prompt 文本
    action_value: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="动作值（根据action_type：agent_id/skill_id/prompt文本）",
    )
    
    # === 标签字段 ===
    tag: Mapped[EntryTag] = mapped_column(
        SQLEnum(EntryTag, values_callable=lambda x: [e.value for e in x]),
        default=EntryTag.NONE,
        server_default="none",
        nullable=False,
        comment="标签: none-无标签, new-新上线, hot-最热门",
    )
    
    # === 排序和状态字段 ===
    priority: Mapped[int] = mapped_column(
        Integer,
        default=0,
        server_default="0",
        nullable=False,
        comment="排序权重（数字越小越靠前）",
    )
    
    status: Mapped[int] = mapped_column(
        Integer,
        default=1,
        server_default="1",
        nullable=False,
        comment="状态：0-禁用, 1-启用, 2-即将上线",
    )
    
    def __repr__(self) -> str:
        return f"<QuickEntry(id={self.id}, key='{self.unique_key}', type='{self.type.value}')>"

