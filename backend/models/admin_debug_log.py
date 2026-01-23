"""
Admin调试日志模型
用于记录Admin调试接口的成本，不扣除算力但用于成本分析
"""
from typing import Optional
from sqlalchemy import (
    String,
    BigInteger,
    Integer,
    DECIMAL,
    Index,
    DateTime,
)
from sqlalchemy.sql import func
from sqlalchemy.orm import Mapped, mapped_column

from models.base import BaseModel


class AdminDebugLog(BaseModel):
    """
    Admin调试日志模型
    
    核心字段:
        - admin_user_id: 管理员ID
        - agent_id: 调试的Agent ID
        - model_id: 使用的模型ID
        - input_tokens: 输入Token数
        - output_tokens: 输出Token数
        - estimated_cost: 预估成本
        - debug_type: 调试类型（routing_test/prompt_preview/execution_test）
    """
    __tablename__ = "admin_debug_logs"
    __table_args__ = (
        Index("ix_admin_debug_logs_admin_user_id", "admin_user_id"),
        Index("ix_admin_debug_logs_agent_id", "agent_id"),
        Index("ix_admin_debug_logs_created_at", "created_at"),
        {"comment": "Admin调试日志表"},
    )
    
    # === 关联字段 ===
    admin_user_id: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
        comment="管理员ID",
    )
    
    agent_id: Mapped[Optional[int]] = mapped_column(
        BigInteger,
        nullable=True,
        comment="调试的Agent ID",
    )
    
    model_id: Mapped[Optional[int]] = mapped_column(
        BigInteger,
        nullable=True,
        comment="使用的模型ID",
    )
    
    # === Token统计 ===
    input_tokens: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="输入Token数",
    )
    
    output_tokens: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="输出Token数",
    )
    
    # === 成本统计 ===
    estimated_cost: Mapped[float] = mapped_column(
        DECIMAL(10, 4),
        nullable=False,
        default=0,
        comment="预估成本（火源币）",
    )
    
    # === 调试类型 ===
    debug_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="调试类型：routing_test-路由测试, prompt_preview-Prompt预览, execution_test-执行测试",
    )
    
    def __repr__(self) -> str:
        return f"<AdminDebugLog(id={self.id}, admin_user_id={self.admin_user_id}, debug_type={self.debug_type})>"



