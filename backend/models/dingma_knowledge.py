"""
顶妈（dingma）产品知识库 v2

三层结构：
- DingmaKnowledgeComponent：可复用组件/子配方（酱料、母馅、辣油等）
- DingmaKnowledgeSku：对外成品 SKU
- DingmaSkuComponentLink：成品 ↔ 组件关联（含制作过程焦点 role/process_focus）
"""
from typing import Optional

from sqlalchemy import String, Integer, Text, Index, BigInteger, ForeignKey, JSON, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import BaseModel


class DingmaKnowledgeComponent(BaseModel):
    """组件/子配方：存全量 recipe_detail + 过程文案事实"""

    __tablename__ = "dingma_knowledge_component"
    __table_args__ = (
        Index("ix_dkc_tenant_id", "tenant_id"),
        Index("ix_dkc_component_type", "component_type"),
        Index("ix_dkc_status", "status"),
        Index("ix_dkc_tenant_code", "tenant_id", "component_code", unique=True),
        {"comment": "顶妈知识库-组件/子配方"},
    )

    tenant_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("tenants.id", ondelete="RESTRICT"),
        nullable=False,
        comment="租户ID（dingma）",
    )
    component_code: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        comment="组件稳定编码，租户内唯一",
    )
    component_name: Mapped[str] = mapped_column(
        String(128),
        nullable=False,
        comment="组件名称",
    )
    component_type: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="sauce",
        comment="组件类型：sauce/filling_base/condiment/pickle/dough/other",
    )
    aliases: Mapped[Optional[list]] = mapped_column(JSON, nullable=True, comment="别名列表")
    pack_formula: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="出货/用法说明")
    recipe_detail: Mapped[Optional[dict]] = mapped_column(
        JSON, nullable=True, comment="全量配方（售后智能体用）"
    )
    guardrail: Mapped[Optional[dict]] = mapped_column(
        JSON,
        nullable=True,
        comment="文案护栏 JSON：contains/excludes/forbidden/writable_tags",
    )
    process_copywriting: Mapped[Optional[dict]] = mapped_column(
        JSON,
        nullable=True,
        comment="制作过程文案 JSON：scene_keywords/focus_label/writable_ingredients/scene_hint 等",
    )
    source_version: Mapped[Optional[str]] = mapped_column(String(32), nullable=True, comment="课件版本")
    status: Mapped[int] = mapped_column(Integer, nullable=False, default=1, comment="1启用 0禁用")
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0, comment="排序")

    sku_links: Mapped[list["DingmaSkuComponentLink"]] = relationship(
        "DingmaSkuComponentLink",
        back_populates="component",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<DingmaKnowledgeComponent(code={self.component_code}, name={self.component_name})>"


class DingmaKnowledgeSku(BaseModel):
    """成品 SKU：对外售卖产品"""

    __tablename__ = "dingma_knowledge_sku"
    __table_args__ = (
        Index("ix_dks_tenant_id", "tenant_id"),
        Index("ix_dks_category_code", "category_code"),
        Index("ix_dks_status", "status"),
        Index("ix_dks_tenant_code", "tenant_id", "sku_code", unique=True),
        {"comment": "顶妈知识库-成品SKU"},
    )

    tenant_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("tenants.id", ondelete="RESTRICT"),
        nullable=False,
        comment="租户ID（dingma）",
    )
    sku_code: Mapped[str] = mapped_column(String(64), nullable=False, comment="SKU稳定编码")
    sku_name: Mapped[str] = mapped_column(String(128), nullable=False, comment="SKU名称")
    category_code: Mapped[str] = mapped_column(String(32), nullable=False, comment="品类编码")
    category_name: Mapped[str] = mapped_column(String(64), nullable=False, comment="品类名称")
    aliases: Mapped[Optional[list]] = mapped_column(JSON, nullable=True, comment="别名列表")
    pack_formula: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="出货配比")
    guardrail: Mapped[Optional[dict]] = mapped_column(
        JSON,
        nullable=True,
        comment="成品文案护栏 JSON：contains/excludes/forbidden/writable_tags",
    )
    process_copywriting: Mapped[Optional[dict]] = mapped_column(
        JSON,
        nullable=True,
        comment="SKU 级过程文案（无关联组件或 inline 配方时使用）",
    )
    source_version: Mapped[Optional[str]] = mapped_column(String(32), nullable=True, comment="课件版本")
    status: Mapped[int] = mapped_column(Integer, nullable=False, default=1, comment="1启用 0禁用")
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0, comment="排序")

    component_links: Mapped[list["DingmaSkuComponentLink"]] = relationship(
        "DingmaSkuComponentLink",
        back_populates="sku",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<DingmaKnowledgeSku(code={self.sku_code}, name={self.sku_name})>"


class DingmaSkuComponentLink(BaseModel):
    """成品 ↔ 组件关联"""

    __tablename__ = "dingma_sku_component_link"
    __table_args__ = (
        Index("ix_dscl_sku_id", "sku_id"),
        Index("ix_dscl_component_id", "component_id"),
        Index("ix_dscl_sku_component", "sku_id", "component_id", unique=True),
        {"comment": "顶妈知识库-SKU组件关联"},
    )

    sku_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("dingma_knowledge_sku.id", ondelete="CASCADE"),
        nullable=False,
        comment="SKU ID",
    )
    component_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("dingma_knowledge_component.id", ondelete="CASCADE"),
        nullable=False,
        comment="组件 ID",
    )
    role: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="other",
        comment="primary_sauce/filling_base/condiment/side/flavor_addon/other",
    )
    process_focus: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        comment="制作过程场景是否以该组件为主",
    )
    display_label: Mapped[Optional[str]] = mapped_column(
        String(64), nullable=True, comment="关联展示名（可选）"
    )
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0, comment="排序")

    sku: Mapped["DingmaKnowledgeSku"] = relationship("DingmaKnowledgeSku", back_populates="component_links")
    component: Mapped["DingmaKnowledgeComponent"] = relationship(
        "DingmaKnowledgeComponent", back_populates="sku_links"
    )

    def __repr__(self) -> str:
        return f"<DingmaSkuComponentLink(sku_id={self.sku_id}, component_id={self.component_id}, role={self.role})>"
