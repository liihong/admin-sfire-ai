"""
算力变动记录模型
记录用户算力的所有变动明细
"""
import enum
from decimal import Decimal
from typing import Optional, TYPE_CHECKING
from datetime import datetime
from sqlalchemy import (
    String,
    Enum as SQLEnum,
    DECIMAL,
    BigInteger,
    ForeignKey,
    Index,
    Text,
    DateTime,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import BaseModel

if TYPE_CHECKING:
    from models.user import User
    from models.recharge_package import RechargePackage


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
        # 订单号唯一索引（充值订单的order_id必须唯一）
        # 注意：需要在数据库迁移脚本中添加唯一约束：UNIQUE KEY `uk_compute_logs_order_id` (`order_id`) WHERE `type` = 'recharge' AND `order_id` IS NOT NULL
        {"comment": "算力变动记录表"},
    )
    
    # === 核心字段 ===
    user_id: Mapped[int] = mapped_column(
        BigInteger,  # 改为 BigInteger 以匹配 users.id 的类型
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
        DECIMAL(16, 0),
        nullable=False,
        comment="变动金额（正数增加，负数减少）",
    )

    before_balance: Mapped[Decimal] = mapped_column(
        DECIMAL(16, 0),
        nullable=False,
        comment="变动前余额",
    )

    after_balance: Mapped[Decimal] = mapped_column(
        DECIMAL(16, 0),
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
        BigInteger,  # 改为 BigInteger 以匹配 users.id 的类型
        nullable=True,
        comment="操作人ID（管理员操作时记录）",
    )
    
    # === 支付相关字段 ===
    payment_amount: Mapped[Optional[Decimal]] = mapped_column(
        DECIMAL(10, 2),
        nullable=True,
        comment="支付金额（元）",
    )
    
    payment_status: Mapped[Optional[str]] = mapped_column(
        String(32),
        nullable=True,
        default="pending",
        server_default="pending",
        comment="支付状态：pending-待支付, paid-已支付, failed-支付失败, cancelled-已取消",
    )
    
    payment_time: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True,
        comment="支付时间",
    )
    
    wechat_transaction_id: Mapped[Optional[str]] = mapped_column(
        String(64),
        nullable=True,
        comment="微信交易号",
    )
    
    order_expire_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True,
        comment="订单过期时间（待支付订单超过此时间后自动失效）",
    )
    
    package_id: Mapped[Optional[int]] = mapped_column(
        BigInteger,
        ForeignKey("recharge_packages.id", ondelete="SET NULL"),
        nullable=True,
        comment="关联套餐ID",
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
    
    package: Mapped[Optional["RechargePackage"]] = relationship(
        "RechargePackage",
        back_populates="compute_logs",
        foreign_keys=[package_id],
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






