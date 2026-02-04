"""
管理员操作日志模型
用于记录所有管理员对用户的操作（充值、修改等级等）
"""
from typing import Optional, TYPE_CHECKING
from sqlalchemy import (
    String,
    BigInteger,
    Text,
    Index,
    ForeignKey,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import BaseModel

if TYPE_CHECKING:
    from models.admin_user import AdminUser
    from models.user import User


class OperationType:
    """操作类型常量"""
    RECHARGE = "recharge"           # 充值
    DEDUCT = "deduct"               # 扣费
    CHANGE_LEVEL = "change_level"   # 修改等级
    CHANGE_STATUS = "change_status" # 修改状态
    RESET_PASSWORD = "reset_password" # 重置密码


class AdminOperationLog(BaseModel):
    """
    管理员操作日志模型
    
    用于记录所有管理员对用户的操作，便于审计和追溯
    """
    __tablename__ = "admin_operation_logs"
    __table_args__ = (
        Index("ix_admin_operation_logs_admin_user_id", "admin_user_id"),
        Index("ix_admin_operation_logs_user_id", "user_id"),
        Index("ix_admin_operation_logs_operation_type", "operation_type"),
        Index("ix_admin_operation_logs_created_at", "created_at"),
        {"comment": "管理员操作日志表"},
    )
    
    # === 关联字段 ===
    admin_user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("admin_users.id", ondelete="SET NULL"),
        nullable=False,
        comment="操作管理员ID",
    )
    
    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        comment="目标用户ID",
    )
    
    # === 操作信息 ===
    operation_type: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        comment="操作类型: recharge-充值, deduct-扣费, change_level-修改等级, change_status-修改状态, reset_password-重置密码",
    )
    
    operation_detail: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="操作详情（JSON格式，记录操作前后的变化）",
    )
    
    remark: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="备注说明",
    )
    
    # === 关系定义 ===
    admin_user: Mapped[Optional["AdminUser"]] = relationship(
        "AdminUser",
        foreign_keys=[admin_user_id],
        lazy="selectin",
    )
    
    user: Mapped[Optional["User"]] = relationship(
        "User",
        foreign_keys=[user_id],
        lazy="selectin",
    )
    
    def __repr__(self) -> str:
        return f"<AdminOperationLog(id={self.id}, admin_user_id={self.admin_user_id}, operation_type={self.operation_type})>"

