"""
数据字典模型
用于管理系统中的各种选项配置（如行业赛道、语气风格等）
"""
from typing import Optional, List, TYPE_CHECKING
from sqlalchemy import (
    String,
    BigInteger,
    Integer,
    Boolean,
    Text,
    ForeignKey,
    Index,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import BaseModel

if TYPE_CHECKING:
    pass


class Dictionary(BaseModel):
    """
    字典类型表
    
    用于定义字典分类，如：
        - industry: 行业赛道
        - tone: 语气风格
    """
    __tablename__ = "sys_dict"
    __table_args__ = (
        Index("ix_sys_dict_code", "dict_code", unique=True),
        Index("ix_sys_dict_is_enabled", "is_enabled"),
        Index("ix_sys_dict_sort_order", "sort_order"),
        {"comment": "数据字典类型表"},
    )
    
    # === 基础字段 ===
    dict_code: Mapped[str] = mapped_column(
        String(64),
        unique=True,
        nullable=False,
        comment="字典编码（唯一标识）",
    )
    
    dict_name: Mapped[str] = mapped_column(
        String(128),
        nullable=False,
        comment="字典名称",
    )
    
    description: Mapped[Optional[str]] = mapped_column(
        String(256),
        nullable=True,
        comment="字典描述",
    )
    
    # === 状态字段 ===
    is_enabled: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        server_default="1",
        nullable=False,
        comment="是否启用",
    )
    
    sort_order: Mapped[int] = mapped_column(
        Integer,
        default=0,
        server_default="0",
        nullable=False,
        comment="排序顺序（越小越靠前）",
    )
    
    # === 关联关系 ===
    items: Mapped[List["DictionaryItem"]] = relationship(
        "DictionaryItem",
        back_populates="dictionary",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    
    def __repr__(self) -> str:
        return f"<Dictionary(id={self.id}, code='{self.dict_code}', name='{self.dict_name}')>"


class DictionaryItem(BaseModel):
    """
    字典项表
    
    存储具体的字典选项值
    """
    __tablename__ = "sys_dict_item"
    __table_args__ = (
        Index("ix_sys_dict_item_dict_id", "dict_id"),
        Index("ix_sys_dict_item_is_enabled", "is_enabled"),
        Index("ix_sys_dict_item_sort_order", "sort_order"),
        {"comment": "数据字典项表"},
    )
    
    # === 关联字段 ===
    dict_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("sys_dict.id", ondelete="CASCADE"),
        nullable=False,
        comment="关联字典ID",
    )
    
    # === 基础字段 ===
    item_value: Mapped[str] = mapped_column(
        String(128),
        nullable=False,
        comment="选项值",
    )
    
    item_label: Mapped[str] = mapped_column(
        String(128),
        nullable=False,
        comment="显示标签",
    )
    
    description: Mapped[Optional[str]] = mapped_column(
        String(256),
        nullable=True,
        comment="选项描述",
    )
    
    # === 状态字段 ===
    is_enabled: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        server_default="1",
        nullable=False,
        comment="是否启用",
    )
    
    sort_order: Mapped[int] = mapped_column(
        Integer,
        default=0,
        server_default="0",
        nullable=False,
        comment="排序顺序（越小越靠前）",
    )
    
    # === 关联关系 ===
    dictionary: Mapped["Dictionary"] = relationship(
        "Dictionary",
        back_populates="items",
    )
    
    def __repr__(self) -> str:
        return f"<DictionaryItem(id={self.id}, value='{self.item_value}', label='{self.item_label}')>"






