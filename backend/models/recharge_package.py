"""
充值套餐模型
用于管理算力充值套餐配置
"""
from decimal import Decimal
from typing import Optional, TYPE_CHECKING
from sqlalchemy import (
    String,
    DECIMAL,
    Integer,
    Boolean,
    JSON,
    Text,
    Index,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import BaseModel

if TYPE_CHECKING:
    from models.compute import ComputeLog


class RechargePackage(BaseModel):
    """
    充值套餐模型
    
    用于存储和管理算力充值套餐配置
    """
    __tablename__ = "recharge_packages"
    __table_args__ = (
        Index("ix_recharge_packages_status", "status"),
        Index("ix_recharge_packages_sort_order", "sort_order"),
        Index("ix_recharge_packages_is_popular", "is_popular"),
        {"comment": "充值套餐表"},
    )
    
    # === 基础信息 ===
    name: Mapped[str] = mapped_column(
        String(128),
        nullable=False,
        comment="套餐名称（如'新人尝鲜包'）",
    )
    
    price: Mapped[Decimal] = mapped_column(
        DECIMAL(10, 2),
        nullable=False,
        comment="销售价格（元）",
    )
    
    power_amount: Mapped[Decimal] = mapped_column(
        DECIMAL(16, 0),
        nullable=False,
        comment="获得算力（火源币）",
    )
    
    # === 展示信息 ===
    unit_price: Mapped[Optional[str]] = mapped_column(
        String(32),
        nullable=True,
        comment="实际单价（1:121格式，计算字段）",
    )
    
    tag: Mapped[Optional[str]] = mapped_column(
        JSON,
        nullable=True,
        comment="标签（如['最划算', '限购一次']，JSON格式）",
    )
    
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="运营建议/描述",
    )
    
    article_count: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="约可生成文案数量（计算字段）",
    )
    
    # === 排序和状态 ===
    sort_order: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
        comment="排序（数字越小越靠前）",
    )
    
    status: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
        server_default="1",
        comment="状态：0-禁用, 1-启用",
    )
    
    is_popular: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="0",
        comment="是否主推款",
    )
    
    # === 关系定义 ===
    compute_logs: Mapped[list["ComputeLog"]] = relationship(
        "ComputeLog",
        back_populates="package",
        foreign_keys="[ComputeLog.package_id]",
    )
    
    def __repr__(self) -> str:
        return (
            f"<RechargePackage(id={self.id}, name={self.name}, "
            f"price={self.price}, power_amount={self.power_amount})>"
        )
    
    @property
    def is_enabled(self) -> bool:
        """是否启用"""
        return self.status == 1





