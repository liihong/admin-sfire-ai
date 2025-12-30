"""
算力变动记录模型
记录用户算力的所有变动明细
"""
import enum
from decimal import Decimal
from typing import Optional, TYPE_CHECKING
from sqlalchemy import (
    String,
    Enum as SQLEnum,
    DECIMAL,
    Integer,
    ForeignKey,
    Index,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.user import User


class ComputeType(enum.Enum):
    """
    算力变动类型枚举
    - RECHARGE: 充值（购买算力）
    - CONSUME: 消耗（使用算力）
    - REFUND: 退款（算力退还）
    - REWARD: 奖励（系统奖励、活动奖励）
    - FREEZE: 冻结（任务开始时冻结）
    - UNFREEZE: 解冻（任务取消时解冻）
    - TRANSFER_IN: 转入（他人转账）
    - TRANSFER_OUT: 转出（转账给他人）
    - COMMISSION: 佣金（分销返佣）
    - ADJUSTMENT: 调整（管理员手动调整）
    """
    RECHARGE = "recharge"           # 充值
    CONSUME = "consume"             # 消耗
    REFUND = "refund"               # 退款
    REWARD = "reward"               # 奖励
    FREEZE = "freeze"               # 冻结
    UNFREEZE = "unfreeze"           # 解冻
    TRANSFER_IN = "transfer_in"     # 转入
    TRANSFER_OUT = "transfer_out"   # 转出
    COMMISSION = "commission"       # 分销佣金
    ADJUSTMENT = "adjustment"       # 管理员调整


class ComputeLog(BaseModel):
    """
    算力变动记录模型
    
    核心字段:
        - user_id: 用户ID（外键）
        - type: 变动类型
        - amount: 变动金额（正数表示增加，负数表示减少）
        - before_balance: 变动前余额
        - after_balance: 变动后余额
        - remark: 备注说明
    
    扩展字段:
        - order_id: 关联订单ID（充值/消费时关联）
        - task_id: 关联任务ID（消耗时关联）
        - operator_id: 操作人ID（管理员操作时记录）
    """
    __tablename__ = "compute_logs"
    __table_args__ = (
        Index("ix_compute_logs_user_id", "user_id"),           # user_id 索引
        Index("ix_compute_logs_type", "type"),                 # type 索引
        Index("ix_compute_logs_order_id", "order_id"),         # order_id 索引
        Index("ix_compute_logs_task_id", "task_id"),           # task_id 索引
        Index("ix_compute_logs_user_type", "user_id", "type"), # 复合索引
        {"comment": "算力变动记录表"},
    )
    
    # === 核心字段 ===
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        comment="用户ID",
    )
    
    type: Mapped[ComputeType] = mapped_column(
        SQLEnum(ComputeType, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        comment="变动类型: recharge-充值, consume-消耗, refund-退款, reward-奖励, etc.",
    )
    
    amount: Mapped[Decimal] = mapped_column(
        DECIMAL(16, 4),
        nullable=False,
        comment="变动金额（正数增加，负数减少）",
    )
    
    before_balance: Mapped[Decimal] = mapped_column(
        DECIMAL(16, 4),
        nullable=False,
        comment="变动前余额",
    )
    
    after_balance: Mapped[Decimal] = mapped_column(
        DECIMAL(16, 4),
        nullable=False,
        comment="变动后余额",
    )
    
    remark: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="备注说明",
    )
    
    # === 关联字段 ===
    order_id: Mapped[Optional[str]] = mapped_column(
        String(64),
        nullable=True,
        comment="关联订单ID（充值/消费订单）",
    )
    
    task_id: Mapped[Optional[str]] = mapped_column(
        String(64),
        nullable=True,
        comment="关联任务ID（AI任务）",
    )
    
    operator_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="操作人ID（管理员操作时记录）",
    )
    
    # === 扩展字段（便于小程序同步）===
    source: Mapped[Optional[str]] = mapped_column(
        String(32),
        nullable=True,
        default="admin",
        server_default="admin",
        comment="来源: admin-管理后台, miniapp-小程序, api-接口",
    )
    
    extra_data: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="扩展数据（JSON格式，存储额外信息）",
    )
    
    # === 关系定义 ===
    user: Mapped["User"] = relationship(
        "User",
        back_populates="compute_logs",
    )
    
    def __repr__(self) -> str:
        return (
            f"<ComputeLog(id={self.id}, user_id={self.user_id}, "
            f"type={self.type.value}, amount={self.amount})>"
        )
    
    @property
    def type_name(self) -> str:
        """获取变动类型中文名称"""
        type_names = {
            ComputeType.RECHARGE: "充值",
            ComputeType.CONSUME: "消耗",
            ComputeType.REFUND: "退款",
            ComputeType.REWARD: "奖励",
            ComputeType.FREEZE: "冻结",
            ComputeType.UNFREEZE: "解冻",
            ComputeType.TRANSFER_IN: "转入",
            ComputeType.TRANSFER_OUT: "转出",
            ComputeType.COMMISSION: "分销佣金",
            ComputeType.ADJUSTMENT: "管理员调整",
        }
        return type_names.get(self.type, "未知")
    
    @property
    def is_increase(self) -> bool:
        """是否为增加操作"""
        return self.amount > 0


