"""
用户模型
支持用户分级（普通/会员/合伙人）和分销关联
设计考虑与小程序数据库同步
"""
from decimal import Decimal
from datetime import datetime
from typing import Optional, List, TYPE_CHECKING
from sqlalchemy import (
    String,
    DECIMAL,
    BigInteger,
    Boolean,
    ForeignKey,
    Index,
    Text,
    DateTime,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import BaseModel

if TYPE_CHECKING:
    from models.compute import ComputeLog
    from models.project import Project
    from models.conversation import Conversation
    from models.user_level import UserLevel as UserLevelModel


class User(BaseModel):
    """
    用户模型
    
    核心字段:
        - username: 用户名（唯一，带索引）
        - level: 用户等级（普通/会员/合伙人）
        - balance: 算力余额
        - frozen_balance: 冻结中的算力
        - parent_id: 上级用户ID（分销关联）
    
    扩展字段（便于小程序同步）:
        - openid: 微信小程序 openid
        - unionid: 微信 unionid（跨平台用户识别）
        - phone: 手机号
        - avatar: 头像URL
        - nickname: 昵称
        - partner_balance: 合伙人资产余额
        - vip_expire_date: 会员到期时间
    """
    __tablename__ = "users"
    __table_args__ = (
        Index("ix_users_username", "username"),        # username 索引
        Index("ix_users_openid", "openid"),            # openid 索引（小程序查询优化）
        Index("ix_users_parent_id", "parent_id"),      # parent_id 索引（分销查询优化）
        Index("ix_users_level_code", "level_code"),    # level_code 索引（按等级筛选）
        Index("ix_users_is_deleted", "is_deleted"),   # is_deleted 索引（查询优化）
        Index("ix_users_created_at", "created_at"),    # created_at 索引（排序优化）
        Index("ix_users_is_active", "is_active"),      # is_active 索引（筛选优化）
        {"comment": "用户表"},
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
    
    level_code: Mapped[Optional[str]] = mapped_column(
        String(32),
        ForeignKey("user_levels.code", ondelete="RESTRICT"),
        default="normal",
        server_default="normal",
        nullable=False,
        comment="用户等级代码（外键关联user_levels表）：normal/vip/svip/max",
    )
    
    balance: Mapped[Decimal] = mapped_column(
        DECIMAL(16, 0),
        default=Decimal("0"),
        server_default="0",
        nullable=False,
        comment="算力余额",
    )

    frozen_balance: Mapped[Decimal] = mapped_column(
        DECIMAL(16, 0),
        default=Decimal("0"),
        server_default="0",
        nullable=False,
        comment="冻结中的算力（处理中的任务占用）",
    )

    version: Mapped[int] = mapped_column(
        BigInteger,
        default=0,
        server_default="0",
        nullable=False,
        comment="版本号（乐观锁，防止并发更新冲突）",
    )

    partner_balance: Mapped[Decimal] = mapped_column(
        DECIMAL(16, 0),
        default=Decimal("0"),
        server_default="0",
        nullable=False,
        comment="合伙人资产余额",
    )
    
    vip_expire_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True,
        comment="会员到期时间",
    )
    
    # === 分销关联 ===
    parent_id: Mapped[Optional[int]] = mapped_column(
        BigInteger,  # 改为 BigInteger 以匹配 id 的类型
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        comment="上级用户ID（分销推荐人）",
    )
    
    # === 小程序同步字段 ===
    openid: Mapped[Optional[str]] = mapped_column(
        String(128),
        unique=True,
        nullable=True,
        comment="微信小程序 openid",
    )
    
    unionid: Mapped[Optional[str]] = mapped_column(
        String(128),
        nullable=True,
        comment="微信 unionid（跨平台用户识别）",
    )
    
    phone: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True,
        comment="手机号",
    )
    
    nickname: Mapped[Optional[str]] = mapped_column(
        String(64),
        nullable=True,
        comment="用户昵称",
    )
    
    avatar: Mapped[Optional[str]] = mapped_column(
        String(512),
        nullable=True,
        comment="头像URL",
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
    # 自引用关系 - 分销层级
    parent: Mapped[Optional["User"]] = relationship(
        "User",
        remote_side="User.id",
        back_populates="children",
        foreign_keys=[parent_id],
    )
    
    children: Mapped[List["User"]] = relationship(
        "User",
        back_populates="parent",
        foreign_keys=[parent_id],
    )
    
    # 算力变动记录关系
    compute_logs: Mapped[List["ComputeLog"]] = relationship(
        "ComputeLog",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="dynamic",
    )
    
    # 项目关系
    projects: Mapped[List["Project"]] = relationship(
        "Project",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="dynamic",
    )
    
    # 对话会话关系
    conversations: Mapped[List["Conversation"]] = relationship(
        "Conversation",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="dynamic",
    )
    
    # 用户等级关系
    user_level: Mapped[Optional["UserLevelModel"]] = relationship(
        "UserLevel",
        primaryjoin="User.level_code == UserLevel.code",
        lazy="selectin",
    )
    
    def __repr__(self) -> str:
        return f"<User(id={self.id}, username='{self.username}', level_code={self.level_code})>"
    
    @property
    def available_balance(self) -> Decimal:
        """可用余额 = 总余额 - 冻结余额"""
        return self.balance - self.frozen_balance
    
    @property
    def level_name(self) -> str:
        """获取等级中文名称"""
        if self.user_level:
            return self.user_level.name
        return "未知"
