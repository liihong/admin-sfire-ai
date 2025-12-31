"""
管理员用户模型
用于后台管理系统的用户，与微信小程序用户（User）分离
"""
from typing import Optional, TYPE_CHECKING
from sqlalchemy import (
    String,
    BigInteger,
    Boolean,
    ForeignKey,
    Index,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.role import Role


class AdminUser(BaseModel):
    """
    管理员用户模型
    
    用于后台管理系统的用户，与微信小程序用户（User）分离
    
    核心字段:
        - username: 用户名（唯一，带索引）
        - password_hash: 密码哈希值
        - email: 邮箱
        - role_id: 角色ID（关联Role表）
        - is_active: 是否激活
        - is_deleted: 是否已删除（软删除）
    """
    __tablename__ = "admin_users"
    __table_args__ = (
        Index("ix_admin_users_username", "username"),        # username 索引
        Index("ix_admin_users_email", "email"),               # email 索引
        Index("ix_admin_users_role_id", "role_id"),           # role_id 索引
        {"comment": "管理员用户表"},
    )
    
    # === 核心字段 ===
    username: Mapped[str] = mapped_column(
        String(64),
        unique=True,
        nullable=False,
        comment="用户名",
    )
    
    password_hash: Mapped[Optional[str]] = mapped_column(
        String(256),
        nullable=True,
        comment="密码哈希值",
    )
    
    email: Mapped[Optional[str]] = mapped_column(
        String(128),
        nullable=True,
        comment="邮箱",
    )
    
    # === 角色关联 ===
    role_id: Mapped[Optional[int]] = mapped_column(
        BigInteger,
        ForeignKey("roles.id", ondelete="SET NULL"),
        nullable=True,
        comment="角色ID",
    )
    
    # === 状态字段 ===
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        server_default="1",
        nullable=False,
        comment="是否激活",
    )
    
    is_deleted: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        server_default="0",
        nullable=False,
        comment="是否已删除（软删除）",
    )
    
    remark: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="备注信息",
    )
    
    # === 关系定义 ===
    role: Mapped[Optional["Role"]] = relationship(
        "Role",
        back_populates="admin_users",
        foreign_keys=[role_id],
    )
    
    def __repr__(self) -> str:
        return f"<AdminUser(id={self.id}, username='{self.username}', role_id={self.role_id})>"

