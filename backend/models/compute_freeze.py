"""
算力冻结记录模型（幂等性保证）
用于实现原子化扣减和幂等性控制
"""
import enum
from decimal import Decimal
from typing import Optional
from sqlalchemy import (
    String,
    Enum as SQLEnum,
    DECIMAL,
    BigInteger,
    Index,
    DateTime,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from models.base import BaseModel


class FreezeStatus(enum.Enum):
    """冻结状态枚举"""
    FROZEN = "frozen"       # 已冻结
    SETTLED = "settled"     # 已结算
    REFUNDED = "refunded"   # 已退还
    FAILED = "failed"       # 失败


class ComputeFreezeLog(BaseModel):
    """
    算力冻结记录模型（幂等性保证）

    核心作用：
        1. 幂等性控制：通过request_id确保同一请求只冻结一次
        2. 原子化冻结：配合原子SQL实现无锁冻结
        3. 审计追溯：记录所有冻结操作的完整生命周期

    使用场景：
        - AI对话前预冻结算力
        - 其他需要先冻结后结算的业务

    生命周期：
        1. 创建时状态为 FROZEN
        2. 任务成功后状态变为 SETTLED（结算）
        3. 任务失败后状态变为 REFUNDED（退款）
    """
    __tablename__ = "compute_freeze_logs"
    __table_args__ = (
        Index("ix_compute_freeze_logs_request_id", "request_id", unique=True),  # ✅ 唯一索引（幂等性核心）
        Index("ix_compute_freeze_logs_user_id", "user_id"),
        Index("ix_compute_freeze_logs_status", "status"),
        Index("ix_compute_freeze_logs_created_at", "created_at"),
        {"comment": "算力冻结记录表（幂等性保证）"},
    )

    # === 核心字段（幂等性控制） ===
    request_id: Mapped[str] = mapped_column(
        String(128),
        nullable=False,
        unique=True,  # ✅ 数据库唯一约束（幂等性保证）
        comment="请求ID（全局唯一，用于幂等性控制）",
    )

    user_id: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
        comment="用户ID",
    )

    amount: Mapped[Decimal] = mapped_column(
        DECIMAL(10, 4),
        nullable=False,
        comment="冻结金额",
    )

    status: Mapped[str] = mapped_column(
        SQLEnum(FreezeStatus, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        default=FreezeStatus.FROZEN.value,
        server_default=FreezeStatus.FROZEN.value,
        comment="状态: frozen-已冻结, settled-已结算, refunded-已退还, failed-失败",
    )

    # === 业务关联字段 ===
    model_id: Mapped[Optional[int]] = mapped_column(
        BigInteger,
        nullable=True,
        comment="关联的模型ID",
    )

    conversation_id: Mapped[Optional[int]] = mapped_column(
        BigInteger,
        nullable=True,
        comment="关联的会话ID",
    )

    # === 金额追踪字段 ===
    estimated_cost: Mapped[Optional[Decimal]] = mapped_column(
        DECIMAL(10, 4),
        nullable=True,
        comment="预估消耗",
    )

    actual_cost: Mapped[Optional[Decimal]] = mapped_column(
        DECIMAL(10, 4),
        nullable=True,
        comment="实际消耗（结算时填写）",
    )

    # === Token统计 ===
    input_tokens: Mapped[Optional[int]] = mapped_column(
        BigInteger,
        nullable=True,
        comment="输入Token数（结算时填写）",
    )

    output_tokens: Mapped[Optional[int]] = mapped_column(
        BigInteger,
        nullable=True,
        comment="输出Token数（结算时填写）",
    )

    # === 时间戳 ===
    frozen_at: Mapped[DateTime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=func.now(),
        comment="冻结时间",
    )

    settled_at: Mapped[Optional[DateTime]] = mapped_column(
        DateTime,
        nullable=True,
        comment="结算时间",
    )

    refunded_at: Mapped[Optional[DateTime]] = mapped_column(
        DateTime,
        nullable=True,
        comment="退款时间",
    )

    # === 备注和扩展 ===
    remark: Mapped[Optional[str]] = mapped_column(
        String(512),
        nullable=True,
        comment="备注说明",
    )

    extra_data: Mapped[Optional[str]] = mapped_column(
        String(1024),
        nullable=True,
        comment="扩展数据（JSON格式）",
    )

    def __repr__(self) -> str:
        return (
            f"<ComputeFreezeLog(id={self.id}, request_id={self.request_id}, "
            f"user_id={self.user_id}, amount={self.amount}, status={self.status})>"
        )

    @property
    def is_frozen(self) -> bool:
        """是否处于冻结状态"""
        return self.status == FreezeStatus.FROZEN.value

    @property
    def is_settled(self) -> bool:
        """是否已结算"""
        return self.status == FreezeStatus.SETTLED.value

    @property
    def is_refunded(self) -> bool:
        """是否已退款"""
        return self.status == FreezeStatus.REFUNDED.value

    @property
    def can_settle(self) -> bool:
        """是否可以结算"""
        return self.status == FreezeStatus.FROZEN.value

    @property
    def can_refund(self) -> bool:
        """是否可以退款"""
        return self.status == FreezeStatus.FROZEN.value
