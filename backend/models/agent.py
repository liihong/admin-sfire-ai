"""
智能体（AI Agent）模型
用于管理AI智能体的配置信息
"""
from typing import Optional
from sqlalchemy import (
    String,
    BigInteger,
    Integer,
    Boolean,
    Text,
    DECIMAL,
    Index,
    JSON,
)
from sqlalchemy.orm import Mapped, mapped_column

from models.base import BaseModel


class Agent(BaseModel):
    """
    智能体模型
    
    核心字段:
        - name: 智能体名称
        - icon: 图标URL或图标标识
        - description: 描述信息
        - system_prompt: 系统提示词
        - model: 使用的AI模型
        - config: 配置参数（JSON格式）
        - sort_order: 排序顺序
        - status: 状态（0-下架, 1-上架）
        - usage_count: 使用次数
    """
    __tablename__ = "agents"
    __table_args__ = (
        Index("ix_agents_status", "status"),
        Index("ix_agents_sort_order", "sort_order"),
        {"comment": "智能体配置表"},
    )
    
    # === 基础字段 ===
    name: Mapped[str] = mapped_column(
        String(128),
        nullable=False,
        comment="智能体名称",
    )
    
    icon: Mapped[str] = mapped_column(
        String(256),
        nullable=False,
        comment="图标URL或图标标识",
    )
    
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="描述信息",
    )
    
    system_prompt: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="系统提示词",
    )
    
    model: Mapped[str] = mapped_column(
        String(128),
        nullable=False,
        comment="使用的AI模型",
    )
    
    # === 配置参数（JSON格式存储）===
    config: Mapped[Optional[dict]] = mapped_column(
        JSON,
        nullable=True,
        comment="配置参数（temperature, max_tokens等）",
    )
    
    # === 排序和状态 ===
    sort_order: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="排序顺序（数字越小越靠前）",
    )
    
    status: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="状态：0-下架, 1-上架",
    )
    
    # === 统计字段 ===
    usage_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="使用次数",
    )
    
    def __repr__(self) -> str:
        return f"<Agent(id={self.id}, name={self.name}, status={self.status})>"
    
    @property
    def is_active(self) -> bool:
        """是否上架"""
        return self.status == 1




