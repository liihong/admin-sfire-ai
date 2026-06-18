"""
顶妈知识库 v2 后台管理服务
"""
from __future__ import annotations

from typing import List, Optional, Tuple

from loguru import logger
from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from models.dingma_knowledge import (
    DingmaKnowledgeComponent,
    DingmaKnowledgeSku,
    DingmaSkuComponentLink,
)
from schemas.dingma.knowledge import (
    ComponentCreate,
    ComponentQueryParams,
    ComponentResponse,
    ComponentUpdate,
    SkuCategoryResponse,
    SkuComponentLinkSchema,
    SkuCreate,
    SkuQueryParams,
    SkuResponse,
    SkuUpdate,
)
from services.base import BaseService
from services.dingma.knowledge import DingmaKnowledgeService
from utils.exceptions import BadRequestException, ForbiddenException, NotFoundException


class DingmaKnowledgeAdminService(BaseService):
    """顶妈知识库 CRUD"""

    def __init__(self, db: AsyncSession):
        super().__init__(db, DingmaKnowledgeSku, "知识库", check_soft_delete=False)

    async def _resolve_tenant_id(self, scoped_tenant_id: Optional[int]) -> int:
        dingma_tenant_id = await DingmaKnowledgeService.resolve_tenant_id(self.db)
        if scoped_tenant_id is not None and int(scoped_tenant_id) != dingma_tenant_id:
            raise ForbiddenException("仅顶妈（dingma）租户可管理知识库")
        return dingma_tenant_id

    @staticmethod
    def _serialize_links(sku: DingmaKnowledgeSku) -> List[dict]:
        links: List[dict] = []
        for link in sorted(sku.component_links or [], key=lambda x: (x.sort_order, x.id)):
            comp = link.component
            links.append(
                SkuComponentLinkSchema(
                    component_code=comp.component_code if comp else "",
                    component_name=comp.component_name if comp else None,
                    role=link.role,
                    process_focus=link.process_focus,
                    display_label=link.display_label,
                    sort_order=link.sort_order,
                ).model_dump()
            )
        return links

    def _sku_to_response(self, sku: DingmaKnowledgeSku) -> dict:
        payload = {
            "id": sku.id,
            "tenant_id": sku.tenant_id,
            "sku_code": sku.sku_code,
            "sku_name": sku.sku_name,
            "category_code": sku.category_code,
            "category_name": sku.category_name,
            "aliases": sku.aliases or [],
            "pack_formula": sku.pack_formula,
            "guardrail": sku.guardrail,
            "process_copywriting": sku.process_copywriting,
            "source_version": sku.source_version,
            "status": sku.status,
            "sort_order": sku.sort_order,
            "created_at": sku.created_at,
            "updated_at": sku.updated_at,
            "component_links": self._serialize_links(sku),
        }
        return SkuResponse.model_validate(payload).model_dump()

    async def _get_sku(self, item_id: int, tenant_id: int) -> DingmaKnowledgeSku:
        result = await self.db.execute(
            select(DingmaKnowledgeSku)
            .options(
                selectinload(DingmaKnowledgeSku.component_links).selectinload(
                    DingmaSkuComponentLink.component
                )
            )
            .where(and_(DingmaKnowledgeSku.id == item_id, DingmaKnowledgeSku.tenant_id == tenant_id))
        )
        sku = result.scalar_one_or_none()
        if sku is None:
            raise NotFoundException(msg="SKU 不存在")
        return sku

    async def _get_component(self, item_id: int, tenant_id: int) -> DingmaKnowledgeComponent:
        result = await self.db.execute(
            select(DingmaKnowledgeComponent).where(
                and_(
                    DingmaKnowledgeComponent.id == item_id,
                    DingmaKnowledgeComponent.tenant_id == tenant_id,
                )
            )
        )
        comp = result.scalar_one_or_none()
        if comp is None:
            raise NotFoundException(msg="组件不存在")
        return comp

    async def _resolve_component_id(self, tenant_id: int, component_code: str) -> int:
        result = await self.db.execute(
            select(DingmaKnowledgeComponent.id).where(
                and_(
                    DingmaKnowledgeComponent.tenant_id == tenant_id,
                    DingmaKnowledgeComponent.component_code == component_code,
                )
            )
        )
        comp_id = result.scalar_one_or_none()
        if comp_id is None:
            raise BadRequestException(f"组件编码 {component_code} 不存在")
        return int(comp_id)

    async def _sync_sku_links(
        self,
        sku: DingmaKnowledgeSku,
        links: Optional[List[SkuComponentLinkSchema]],
        tenant_id: int,
    ) -> None:
        if links is None:
            return

        # 清空旧关联后重建
        for old in list(sku.component_links or []):
            await self.db.delete(old)
        await self.db.flush()

        for idx, link in enumerate(links):
            comp_id = await self._resolve_component_id(tenant_id, link.component_code)
            self.db.add(
                DingmaSkuComponentLink(
                    sku_id=sku.id,
                    component_id=comp_id,
                    role=link.role,
                    process_focus=link.process_focus,
                    display_label=link.display_label,
                    sort_order=link.sort_order if link.sort_order else idx,
                )
            )

    # ---------- SKU ----------

    async def get_sku_list(
        self, params: SkuQueryParams, scoped_tenant_id: Optional[int] = None
    ) -> Tuple[List[dict], int]:
        tenant_id = await self._resolve_tenant_id(scoped_tenant_id)
        conditions = [DingmaKnowledgeSku.tenant_id == tenant_id]
        if params.category_code:
            conditions.append(DingmaKnowledgeSku.category_code == params.category_code)
        if params.status is not None:
            conditions.append(DingmaKnowledgeSku.status == params.status)
        if params.keyword:
            kw = f"%{params.keyword.strip()}%"
            conditions.append(
                or_(
                    DingmaKnowledgeSku.sku_name.like(kw),
                    DingmaKnowledgeSku.sku_code.like(kw),
                )
            )

        offset = (params.pageNum - 1) * params.pageSize
        total = int(
            (
                await self.db.execute(
                    select(func.count(DingmaKnowledgeSku.id)).where(and_(*conditions))
                )
            ).scalar()
            or 0
        )
        result = await self.db.execute(
            select(DingmaKnowledgeSku)
            .options(
                selectinload(DingmaKnowledgeSku.component_links).selectinload(
                    DingmaSkuComponentLink.component
                )
            )
            .where(and_(*conditions))
            .order_by(DingmaKnowledgeSku.sort_order, DingmaKnowledgeSku.id)
            .offset(offset)
            .limit(params.pageSize)
        )
        items = [self._sku_to_response(row) for row in result.scalars().all()]
        return items, total

    async def get_sku_detail(self, item_id: int, scoped_tenant_id: Optional[int] = None) -> dict:
        tenant_id = await self._resolve_tenant_id(scoped_tenant_id)
        sku = await self._get_sku(item_id, tenant_id)
        return self._sku_to_response(sku)

    async def create_sku(self, data: SkuCreate, scoped_tenant_id: Optional[int] = None) -> dict:
        tenant_id = await self._resolve_tenant_id(scoped_tenant_id)
        exists = await self.db.execute(
            select(DingmaKnowledgeSku.id).where(
                and_(
                    DingmaKnowledgeSku.tenant_id == tenant_id,
                    DingmaKnowledgeSku.sku_code == data.sku_code,
                )
            )
        )
        if exists.scalar_one_or_none():
            raise BadRequestException(f"SKU 编码 {data.sku_code} 已存在")

        payload = data.model_dump(exclude={"component_links"})
        payload["tenant_id"] = tenant_id
        sku = DingmaKnowledgeSku(**payload)
        self.db.add(sku)
        await self.db.flush()
        await self._sync_sku_links(sku, data.component_links, tenant_id)
        await self.db.refresh(sku)
        sku = await self._get_sku(sku.id, tenant_id)
        logger.info(f"[DingmaKnowledge] 创建 SKU: {sku.sku_name}")
        return self._sku_to_response(sku)

    async def update_sku(
        self, item_id: int, data: SkuUpdate, scoped_tenant_id: Optional[int] = None
    ) -> dict:
        tenant_id = await self._resolve_tenant_id(scoped_tenant_id)
        sku = await self._get_sku(item_id, tenant_id)
        update_data = data.model_dump(exclude_unset=True, exclude={"component_links"})
        for field, value in update_data.items():
            setattr(sku, field, value)
        await self._sync_sku_links(sku, data.component_links, tenant_id)
        await self.db.flush()
        sku = await self._get_sku(sku.id, tenant_id)
        return self._sku_to_response(sku)

    async def delete_sku(self, item_id: int, scoped_tenant_id: Optional[int] = None) -> None:
        tenant_id = await self._resolve_tenant_id(scoped_tenant_id)
        sku = await self._get_sku(item_id, tenant_id)
        await self.db.delete(sku)
        await self.db.flush()

    async def update_sku_status(
        self, item_id: int, status: int, scoped_tenant_id: Optional[int] = None
    ) -> dict:
        if status not in (0, 1):
            raise BadRequestException("状态值必须为 0 或 1")
        tenant_id = await self._resolve_tenant_id(scoped_tenant_id)
        sku = await self._get_sku(item_id, tenant_id)
        sku.status = status
        await self.db.flush()
        return self._sku_to_response(sku)

    async def get_sku_categories(self, scoped_tenant_id: Optional[int] = None) -> List[dict]:
        tenant_id = await self._resolve_tenant_id(scoped_tenant_id)
        result = await self.db.execute(
            select(
                DingmaKnowledgeSku.category_code,
                DingmaKnowledgeSku.category_name,
                func.count(DingmaKnowledgeSku.id),
            )
            .where(DingmaKnowledgeSku.tenant_id == tenant_id)
            .group_by(DingmaKnowledgeSku.category_code, DingmaKnowledgeSku.category_name)
            .order_by(DingmaKnowledgeSku.category_code)
        )
        return [
            SkuCategoryResponse(
                category_code=row[0], category_name=row[1], count=int(row[2])
            ).model_dump()
            for row in result.all()
        ]

    # ---------- Component ----------

    async def get_component_list(
        self, params: ComponentQueryParams, scoped_tenant_id: Optional[int] = None
    ) -> Tuple[List[dict], int]:
        tenant_id = await self._resolve_tenant_id(scoped_tenant_id)
        conditions = [DingmaKnowledgeComponent.tenant_id == tenant_id]
        if params.component_type:
            conditions.append(DingmaKnowledgeComponent.component_type == params.component_type)
        if params.status is not None:
            conditions.append(DingmaKnowledgeComponent.status == params.status)
        if params.keyword:
            kw = f"%{params.keyword.strip()}%"
            conditions.append(
                or_(
                    DingmaKnowledgeComponent.component_name.like(kw),
                    DingmaKnowledgeComponent.component_code.like(kw),
                )
            )

        offset = (params.pageNum - 1) * params.pageSize
        total = int(
            (
                await self.db.execute(
                    select(func.count(DingmaKnowledgeComponent.id)).where(and_(*conditions))
                )
            ).scalar()
            or 0
        )
        result = await self.db.execute(
            select(DingmaKnowledgeComponent)
            .where(and_(*conditions))
            .order_by(DingmaKnowledgeComponent.sort_order, DingmaKnowledgeComponent.id)
            .offset(offset)
            .limit(params.pageSize)
        )
        items = [ComponentResponse.model_validate(row).model_dump() for row in result.scalars().all()]
        return items, total

    async def get_component_detail(
        self, item_id: int, scoped_tenant_id: Optional[int] = None
    ) -> dict:
        tenant_id = await self._resolve_tenant_id(scoped_tenant_id)
        comp = await self._get_component(item_id, tenant_id)
        return ComponentResponse.model_validate(comp).model_dump()

    async def create_component(
        self, data: ComponentCreate, scoped_tenant_id: Optional[int] = None
    ) -> dict:
        tenant_id = await self._resolve_tenant_id(scoped_tenant_id)
        exists = await self.db.execute(
            select(DingmaKnowledgeComponent.id).where(
                and_(
                    DingmaKnowledgeComponent.tenant_id == tenant_id,
                    DingmaKnowledgeComponent.component_code == data.component_code,
                )
            )
        )
        if exists.scalar_one_or_none():
            raise BadRequestException(f"组件编码 {data.component_code} 已存在")

        payload = data.model_dump()
        payload["tenant_id"] = tenant_id
        comp = DingmaKnowledgeComponent(**payload)
        self.db.add(comp)
        await self.db.flush()
        await self.db.refresh(comp)
        return ComponentResponse.model_validate(comp).model_dump()

    async def update_component(
        self, item_id: int, data: ComponentUpdate, scoped_tenant_id: Optional[int] = None
    ) -> dict:
        tenant_id = await self._resolve_tenant_id(scoped_tenant_id)
        comp = await self._get_component(item_id, tenant_id)
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(comp, field, value)
        await self.db.flush()
        await self.db.refresh(comp)
        return ComponentResponse.model_validate(comp).model_dump()

    async def delete_component(
        self, item_id: int, scoped_tenant_id: Optional[int] = None
    ) -> None:
        tenant_id = await self._resolve_tenant_id(scoped_tenant_id)
        comp = await self._get_component(item_id, tenant_id)
        await self.db.delete(comp)
        await self.db.flush()

    async def update_component_status(
        self, item_id: int, status: int, scoped_tenant_id: Optional[int] = None
    ) -> dict:
        if status not in (0, 1):
            raise BadRequestException("状态值必须为 0 或 1")
        tenant_id = await self._resolve_tenant_id(scoped_tenant_id)
        comp = await self._get_component(item_id, tenant_id)
        comp.status = status
        await self.db.flush()
        return ComponentResponse.model_validate(comp).model_dump()

    async def list_component_options(self, scoped_tenant_id: Optional[int] = None) -> List[dict]:
        """组件下拉（SKU 关联编辑用）"""
        tenant_id = await self._resolve_tenant_id(scoped_tenant_id)
        result = await self.db.execute(
            select(DingmaKnowledgeComponent)
            .where(
                and_(
                    DingmaKnowledgeComponent.tenant_id == tenant_id,
                    DingmaKnowledgeComponent.status == 1,
                )
            )
            .order_by(DingmaKnowledgeComponent.sort_order, DingmaKnowledgeComponent.id)
        )
        return [
            {
                "component_code": c.component_code,
                "component_name": c.component_name,
                "component_type": c.component_type,
            }
            for c in result.scalars().all()
        ]
