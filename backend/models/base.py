"""
Base Model with common fields
"""
from datetime import datetime
from typing import Optional
from sqlalchemy import BigInteger, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column

from db.session import Base


class TimestampMixin:
    """时间戳混入类"""
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=func.now(),
        comment="创建时间"
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        default=func.now(),
        onupdate=func.now(),
        comment="更新时间"
    )


class BaseModel(Base, TimestampMixin):
    """
    基础模型类
    
    包含通用字段：id, created_at, updated_at
    """
    __abstract__ = True
    
    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
        comment="主键ID"
    )
