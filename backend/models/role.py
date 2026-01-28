"""
角色模型
后台管理员角色，关联admin_users表的role_id字段
"""
from typing import Optional, List, TYPE_CHECKING
from sqlalchemy import String, Integer, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import BaseModel

if TYPE_CHECKING:
    from models.admin_user import AdminUser


class Role(BaseModel):
    """
    角色模型（后台管理员角色）
    
    用于后台管理系统的角色权限管理，关联admin_users表
    """
    __tablename__ = "roles"
    __table_args__ = (
        Index("ix_roles_code", "code", unique=True),  # code唯一索引
        {"comment": "角色表"},
    )
    
    code: Mapped[str] = mapped_column(
        String(32),
        unique=True,
        nullable=False,
        comment="角色代码（normal/member/partner），用于后台管理员角色",
    )
    
    name: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        comment="角色名称",
    )
    
    description: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        comment="角色描述",
    )
    
    sort_order: Mapped[int] = mapped_column(
        Integer,
        default=0,
        server_default="0",
        nullable=False,
        comment="排序顺序",
    )
    
    # === 关系定义 ===
    admin_users: Mapped[List["AdminUser"]] = relationship(
        "AdminUser",
        back_populates="role",
        foreign_keys="AdminUser.role_id",
    )
    
    def __repr__(self) -> str:
        return f"<Role(id={self.id}, code='{self.code}', name='{self.name}')>"

