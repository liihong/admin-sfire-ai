"""
首页配置模型
用于管理小程序首页的各种配置项
"""
from typing import Optional
from sqlalchemy import (
    String,
    BigInteger,
    Boolean,
    Text,
    Index,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class HomeConfig(BaseModel):
    """
    首页配置模型
    
    用于存储小程序首页的各种配置项，支持不同类型的配置值
    """
    __tablename__ = "home_configs"
    __table_args__ = (
        Index("ix_home_configs_config_key", "config_key", unique=True),
        Index("ix_home_configs_is_enabled", "is_enabled"),
        {"comment": "首页配置表"},
    )
    
    # === 基础字段 ===
    config_key: Mapped[str] = mapped_column(
        String(64),
        unique=True,
        nullable=False,
        comment="配置键（唯一标识）",
    )
    
    config_value: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="配置值（JSON格式字符串）",
    )
    
    config_type: Mapped[str] = mapped_column(
        String(16),
        default="string",
        server_default="string",
        nullable=False,
        comment="配置类型: string-字符串, json-JSON对象, array-数组",
    )
    
    description: Mapped[Optional[str]] = mapped_column(
        String(256),
        nullable=True,
        comment="配置说明",
    )
    
    # === 状态字段 ===
    is_enabled: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        server_default="1",
        nullable=False,
        comment="是否启用",
    )
    
    def __repr__(self) -> str:
        return f"<HomeConfig(id={self.id}, config_key='{self.config_key}', type='{self.config_type}')>"

