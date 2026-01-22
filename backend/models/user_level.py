"""
用户等级配置模型
用于管理系统中的用户等级配置（normal/vip/svip/max）
"""
from typing import Optional
from sqlalchemy import (
    String,
    Integer,
    Boolean,
    Index,
)
from sqlalchemy.orm import Mapped, mapped_column

from models.base import BaseModel


class UserLevel(BaseModel):
    """
    用户等级配置表
    
    用于定义用户等级及其权限配置：
        - normal: 观望者
        - vip: 个人创作者
        - svip: 小工作室
        - max: 矩阵大佬/B端
    """
    __tablename__ = "user_levels"
    __table_args__ = (
        Index("ix_user_levels_code", "code", unique=True),
        Index("ix_user_levels_is_enabled", "is_enabled"),
        Index("ix_user_levels_sort_order", "sort_order"),
        {"comment": "用户等级配置表"},
    )
    
    # === 基础字段 ===
    code: Mapped[str] = mapped_column(
        String(32),
        unique=True,
        nullable=False,
        comment="等级代码：normal-观望者, vip-个人创作者, svip-小工作室, max-矩阵大佬",
    )
    
    name: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        comment="等级名称（中文显示）",
    )
    
    # === 权限配置字段 ===
    max_ip_count: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="最大IP数量（NULL表示不限制）",
    )
    
    ip_type: Mapped[str] = mapped_column(
        String(16),
        default="permanent",
        server_default="permanent",
        nullable=False,
        comment="IP类型：temporary-临时, permanent-永久",
    )
    
    daily_tokens_limit: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="每日AI能量限制（NULL表示无限制，normal用户限制3次）",
    )
    
    can_use_advanced_agent: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        server_default="0",
        nullable=False,
        comment="是否可使用高级智能体",
    )
    
    unlimited_conversations: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        server_default="0",
        nullable=False,
        comment="是否无限制对话",
    )
    
    # === 状态字段 ===
    is_enabled: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        server_default="1",
        nullable=False,
        comment="是否启用该等级",
    )
    
    sort_order: Mapped[int] = mapped_column(
        Integer,
        default=0,
        server_default="0",
        nullable=False,
        comment="排序顺序（数字越小越靠前）",
    )
    
    def __repr__(self) -> str:
        return f"<UserLevel(id={self.id}, code='{self.code}', name='{self.name}')>"

