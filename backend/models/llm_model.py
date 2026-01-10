"""
大模型管理模型
用于管理各种 LLM 模型的配置信息
"""
from datetime import datetime
from typing import Optional, TYPE_CHECKING
from sqlalchemy import (
    String,
    BigInteger,
    Integer,
    Boolean,
    Text,
    DECIMAL,
    DateTime,
    Index,
)
from sqlalchemy.orm import Mapped, mapped_column

from models.base import BaseModel


class LLMModel(BaseModel):
    """
    大模型配置模型
    
    核心字段:
        - name: 模型显示名称（如 "GPT-4o"）
        - model_id: 模型标识（如 "gpt-4o"）
        - provider: 提供商（openai/anthropic/deepseek）
        - api_key: API Key（加密存储）
        - base_url: API 基础 URL
        - is_enabled: 是否启用
        - total_tokens_used: 累计使用的 token 数
        - balance: 账户余额
        - balance_updated_at: 余额更新时间
        - sort_order: 排序顺序
        - remark: 备注
    """
    __tablename__ = "llm_models"
    __table_args__ = (
        Index("ix_llm_models_provider", "provider"),
        Index("ix_llm_models_is_enabled", "is_enabled"),
        Index("ix_llm_models_sort_order", "sort_order"),
        {"comment": "大模型配置表"},
    )
    
    # === 基础字段 ===
    name: Mapped[str] = mapped_column(
        String(128),
        nullable=False,
        comment="模型显示名称",
    )
    
    model_id: Mapped[str] = mapped_column(
        String(128),
        nullable=False,
        comment="模型标识（API 中的模型名称）",
    )
    
    provider: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        comment="提供商：openai/anthropic/deepseek",
    )
    
    # === API 配置 ===
    api_key: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="API Key（加密存储）",
    )
    
    base_url: Mapped[Optional[str]] = mapped_column(
        String(512),
        nullable=True,
        comment="API 基础 URL（为空则使用默认 URL）",
    )
    
    # === 状态和统计 ===
    is_enabled: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        server_default="1",
        nullable=False,
        comment="是否启用",
    )
    
    total_tokens_used: Mapped[int] = mapped_column(
        BigInteger,
        default=0,
        server_default="0",
        nullable=False,
        comment="累计使用的 token 数",
    )
    
    balance: Mapped[Optional[float]] = mapped_column(
        DECIMAL(16, 4),
        nullable=True,
        comment="账户余额",
    )
    
    balance_updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True,
        comment="余额更新时间",
    )
    
    # === 其他字段 ===
    sort_order: Mapped[int] = mapped_column(
        Integer,
        default=0,
        server_default="0",
        nullable=False,
        comment="排序顺序（数字越小越靠前）",
    )
    
    remark: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="备注信息",
    )

    # === 算力计算配置字段 ===
    rate_multiplier: Mapped[float] = mapped_column(
        DECIMAL(4, 2),
        default=1.00,
        server_default="1.00",
        nullable=False,
        comment="模型倍率系数 (用于算力计算)",
    )

    base_fee: Mapped[float] = mapped_column(
        DECIMAL(16, 4),
        default=10.0000,
        server_default="10.0000",
        nullable=False,
        comment="基础调度费(火源币),无论请求是否成功,只要通过内容审查就扣除",
    )

    input_weight: Mapped[float] = mapped_column(
        DECIMAL(4, 2),
        default=1.00,
        server_default="1.00",
        nullable=False,
        comment="输入Token权重,相对便宜",
    )

    output_weight: Mapped[float] = mapped_column(
        DECIMAL(4, 2),
        default=3.00,
        server_default="3.00",
        nullable=False,
        comment="输出Token权重,较贵,是价值核心",
    )

    max_tokens_per_request: Mapped[int] = mapped_column(
        Integer,
        default=4096,
        server_default="4096",
        nullable=False,
        comment="单次请求最大Token数,用于预冻结估算",
    )

    def __repr__(self) -> str:
        return f"<LLMModel(id={self.id}, name={self.name}, provider={self.provider})>"
    
    @property
    def has_api_key(self) -> bool:
        """是否已配置 API Key"""
        return bool(self.api_key)

