"""
工单模型
用于记录开通会员、充值算力等操作，便于财务留痕和后期扩展审批流程
"""
from datetime import datetime
from typing import Optional, TYPE_CHECKING
from sqlalchemy import (
    String,
    BigInteger,
    Text,
    Boolean,
    DateTime,
    Index,
    ForeignKey,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import BaseModel

if TYPE_CHECKING:
    from models.user import User
    from models.admin_user import AdminUser


class TicketType:
    """工单类型"""
    MEMBERSHIP = "membership"  # 开通会员
    RECHARGE = "recharge"     # 充值算力


class TicketStatus:
    """工单状态（预留多种状态便于后期扩展）"""
    PENDING = "pending"       # 待处理
    PROCESSING = "processing"  # 处理中
    COMPLETED = "completed"   # 已完成
    REJECTED = "rejected"     # 已拒绝
    FAILED = "failed"         # 处理失败


class Ticket(BaseModel):
    """
    工单表
    
    用于记录管理员对用户的操作：开通会员、充值算力
    与财务挂钩，记录收费信息；预留审批相关字段便于后期扩展
    """
    __tablename__ = "tickets"
    __table_args__ = (
        Index("ix_tickets_tenant_id", "tenant_id"),
        Index("ix_tickets_type", "type"),
        Index("ix_tickets_status", "status"),
        Index("ix_tickets_user_id", "user_id"),
        Index("ix_tickets_creator_id", "creator_id"),
        Index("ix_tickets_created_at", "created_at"),
        {"comment": "工单表"},
    )

    tenant_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("tenants.id", ondelete="RESTRICT"),
        nullable=False,
        default=1,
        comment="租户ID",
    )
    
    # === 基础字段 ===
    type: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        comment="工单类型：membership-开通会员, recharge-充值算力",
    )
    
    status: Mapped[str] = mapped_column(
        String(32),
        default=TicketStatus.PENDING,
        server_default=TicketStatus.PENDING,
        nullable=False,
        comment="工单状态：pending-待处理, processing-处理中, completed-已完成, rejected-已拒绝, failed-处理失败",
    )
    
    # === 关联字段 ===
    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        comment="目标用户ID",
    )
    
    creator_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("admin_users.id", ondelete="RESTRICT"),
        nullable=False,
        comment="创建人ID（管理员）",
    )
    
    handler_id: Mapped[Optional[int]] = mapped_column(
        BigInteger,
        ForeignKey("admin_users.id", ondelete="SET NULL"),
        nullable=True,
        comment="处理人ID（管理员）",
    )
    
    # === 会员工单特有字段（与财务挂钩）===
    is_paid: Mapped[Optional[bool]] = mapped_column(
        Boolean,
        nullable=True,
        comment="是否已收费（仅会员工单）",
    )
    
    payment_method: Mapped[Optional[str]] = mapped_column(
        String(64),
        nullable=True,
        comment="收费方式：如微信、支付宝、对公转账等（仅会员工单）",
    )
    
    voucher: Mapped[Optional[str]] = mapped_column(
        String(512),
        nullable=True,
        comment="凭证（图片URL或文字说明，仅会员工单）",
    )
    
    period_type: Mapped[Optional[str]] = mapped_column(
        String(16),
        nullable=True,
        comment="会员周期：monthly-月度, quarterly-季度, yearly-年度（仅会员工单）",
    )
    
    # === 扩展数据（JSON，存储类型相关字段）===
    # membership: { level_code, vip_expire_date }
    # recharge: { amount }
    extra_data: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="扩展数据JSON：membership含level_code/vip_expire_date，recharge含amount",
    )
    
    remark: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="备注说明",
    )
    
    # === 处理时间 ===
    handled_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True,
        comment="处理完成时间",
    )
    
    # === 预留：审批相关字段（后期扩展）===
    approver_id: Mapped[Optional[int]] = mapped_column(
        BigInteger,
        ForeignKey("admin_users.id", ondelete="SET NULL"),
        nullable=True,
        comment="审批人ID（预留）",
    )
    
    approved_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True,
        comment="审批时间（预留）",
    )
    
    approval_status: Mapped[Optional[str]] = mapped_column(
        String(32),
        nullable=True,
        comment="审批状态：approved/rejected（预留）",
    )
    
    # === 处理失败原因 ===
    fail_reason: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="处理失败原因（status=failed时）",
    )
    
    # === 关系定义 ===
    user: Mapped[Optional["User"]] = relationship(
        "User",
        foreign_keys=[user_id],
        lazy="selectin",
    )
    
    creator: Mapped[Optional["AdminUser"]] = relationship(
        "AdminUser",
        foreign_keys=[creator_id],
        lazy="selectin",
    )
    
    handler: Mapped[Optional["AdminUser"]] = relationship(
        "AdminUser",
        foreign_keys=[handler_id],
        lazy="selectin",
    )
    
    def __repr__(self) -> str:
        return f"<Ticket(id={self.id}, type='{self.type}', status='{self.status}')>"
