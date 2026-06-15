"""
顶妈（dingma）产品知识库模型

存储全量配方数据；文案智能体仅注入 copywriting_facts 字段。
"""
from typing import Optional

from sqlalchemy import String, Integer, Text, Index, BigInteger, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column

from models.base import BaseModel


class DingmaProductKnowledge(BaseModel):
    """
    顶妈产品知识库

    - pack_formula / recipe_detail：全量存储，供未来售后智能体使用
    - copywriting_facts：文案智能体注入，防编造
    """

    __tablename__ = "dingma_product_knowledge"
    __table_args__ = (
        Index("ix_dpk_tenant_id", "tenant_id"),
        Index("ix_dpk_category_code", "category_code"),
        Index("ix_dpk_status", "status"),
        Index("ix_dpk_tenant_product_code", "tenant_id", "product_code", unique=True),
        {"comment": "顶妈产品知识库"},
    )

    tenant_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("tenants.id", ondelete="RESTRICT"),
        nullable=False,
        comment="租户ID（dingma）",
    )

    category_code: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        comment="品类编码，如 mixian、wonton",
    )

    category_name: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        comment="品类名称，如 米线、馄饨",
    )

    product_code: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        comment="产品稳定编码，租户内唯一",
    )

    product_name: Mapped[str] = mapped_column(
        String(128),
        nullable=False,
        comment="产品名称",
    )

    aliases: Mapped[Optional[list]] = mapped_column(
        JSON,
        nullable=True,
        comment="别名列表，用于模糊匹配",
    )

    pack_formula: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="出货配比（含克重/包数），售后智能体使用",
    )

    recipe_detail: Mapped[Optional[dict]] = mapped_column(
        JSON,
        nullable=True,
        comment="制作步骤与配料详情 JSON，售后智能体使用",
    )

    copywriting_facts: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="文案事实（含/不含/可写/不可写），文案智能体注入",
    )

    source_version: Mapped[Optional[str]] = mapped_column(
        String(32),
        nullable=True,
        comment="课件版本，如 2026-01",
    )

    status: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
        comment="状态：1-启用 0-禁用",
    )

    sort_order: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="排序",
    )

    def __repr__(self) -> str:
        return f"<DingmaProductKnowledge(code={self.product_code}, name={self.product_name})>"
