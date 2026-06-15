"""
顶妈产品知识库后台管理服务
"""
from __future__ import annotations

from typing import List, Optional, Tuple

from loguru import logger
from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.dingma_product_knowledge import DingmaProductKnowledge
from schemas.dingma.product_knowledge import (
    ProductKnowledgeCategoryResponse,
    ProductKnowledgeCreate,
    ProductKnowledgeQueryParams,
    ProductKnowledgeResponse,
    ProductKnowledgeUpdate,
)
from services.base import BaseService
from services.dingma.constants import DINGMA_TENANT_CODE
from services.dingma.knowledge import DingmaKnowledgeService
from utils.exceptions import BadRequestException, ForbiddenException, NotFoundException


class DingmaProductKnowledgeAdminService(BaseService):
    """顶妈产品知识库 CRUD 服务"""

    def __init__(self, db: AsyncSession):
        super().__init__(db, DingmaProductKnowledge, "产品知识库", check_soft_delete=False)

    async def _resolve_manage_tenant_id(self, scoped_tenant_id: Optional[int]) -> int:
        """
        解析可管理的 dingma 租户 ID。

        - 平台管理员：管理 dingma 租户数据
        - dingma 租户管理员：仅管理本租户
        - 其他租户管理员：拒绝访问
        """
        dingma_tenant_id = await DingmaKnowledgeService.resolve_tenant_id(self.db)

        if scoped_tenant_id is not None and int(scoped_tenant_id) != dingma_tenant_id:
            raise ForbiddenException("仅顶妈（dingma）租户可管理产品知识库")

        return dingma_tenant_id

    async def _get_scoped_item(
        self,
        item_id: int,
        scoped_tenant_id: Optional[int],
    ) -> DingmaProductKnowledge:
        """按 ID 获取记录并校验租户范围"""
        tenant_id = await self._resolve_manage_tenant_id(scoped_tenant_id)
        result = await self.db.execute(
            select(DingmaProductKnowledge).where(
                and_(
                    DingmaProductKnowledge.id == item_id,
                    DingmaProductKnowledge.tenant_id == tenant_id,
                )
            )
        )
        item = result.scalar_one_or_none()
        if item is None:
            raise NotFoundException(msg="产品知识库记录不存在")
        return item

    @staticmethod
    def _to_response(item: DingmaProductKnowledge) -> dict:
        """序列化为统一响应结构"""
        return ProductKnowledgeResponse.model_validate(item).model_dump()

    async def get_list(
        self,
        params: ProductKnowledgeQueryParams,
        scoped_tenant_id: Optional[int] = None,
    ) -> Tuple[List[dict], int]:
        """分页列表"""
        tenant_id = await self._resolve_manage_tenant_id(scoped_tenant_id)
        conditions = [DingmaProductKnowledge.tenant_id == tenant_id]

        if params.category_code:
            conditions.append(DingmaProductKnowledge.category_code == params.category_code)
        if params.product_code:
            conditions.append(DingmaProductKnowledge.product_code == params.product_code)
        if params.status is not None:
            conditions.append(DingmaProductKnowledge.status == params.status)
        if params.product_name:
            keyword = f"%{params.product_name.strip()}%"
            conditions.append(DingmaProductKnowledge.product_name.like(keyword))
        if params.keyword:
            keyword = f"%{params.keyword.strip()}%"
            conditions.append(
                or_(
                    DingmaProductKnowledge.product_name.like(keyword),
                    DingmaProductKnowledge.product_code.like(keyword),
                    DingmaProductKnowledge.copywriting_facts.like(keyword),
                )
            )

        offset = (params.pageNum - 1) * params.pageSize

        # 统计总数
        count_query = select(func.count(DingmaProductKnowledge.id)).where(and_(*conditions))
        total_result = await self.db.execute(count_query)
        total = int(total_result.scalar() or 0)

        # 查询数据（多字段排序）
        query = (
            select(DingmaProductKnowledge)
            .where(and_(*conditions))
            .order_by(
                DingmaProductKnowledge.sort_order.asc(),
                DingmaProductKnowledge.id.asc(),
            )
            .offset(offset)
            .limit(params.pageSize)
        )
        result = await self.db.execute(query)
        items = [self._to_response(row) for row in result.scalars().all()]
        return items, total

    async def get_detail(
        self,
        item_id: int,
        scoped_tenant_id: Optional[int] = None,
    ) -> dict:
        """获取详情"""
        item = await self._get_scoped_item(item_id, scoped_tenant_id)
        return self._to_response(item)

    async def get_categories(
        self,
        scoped_tenant_id: Optional[int] = None,
    ) -> List[dict]:
        """获取品类统计（用于筛选下拉）"""
        tenant_id = await self._resolve_manage_tenant_id(scoped_tenant_id)
        result = await self.db.execute(
            select(
                DingmaProductKnowledge.category_code,
                DingmaProductKnowledge.category_name,
                func.count(DingmaProductKnowledge.id),
            )
            .where(DingmaProductKnowledge.tenant_id == tenant_id)
            .group_by(
                DingmaProductKnowledge.category_code,
                DingmaProductKnowledge.category_name,
            )
            .order_by(DingmaProductKnowledge.category_code.asc())
        )
        rows = result.all()
        return [
            ProductKnowledgeCategoryResponse(
                category_code=row[0],
                category_name=row[1],
                count=int(row[2]),
            ).model_dump()
            for row in rows
        ]

    async def create_item(
        self,
        data: ProductKnowledgeCreate,
        scoped_tenant_id: Optional[int] = None,
    ) -> dict:
        """创建产品知识库记录"""
        tenant_id = await self._resolve_manage_tenant_id(scoped_tenant_id)

        existing = await self.db.execute(
            select(DingmaProductKnowledge.id).where(
                and_(
                    DingmaProductKnowledge.tenant_id == tenant_id,
                    DingmaProductKnowledge.product_code == data.product_code,
                )
            )
        )
        if existing.scalar_one_or_none() is not None:
            raise BadRequestException(f"产品编码 {data.product_code} 已存在")

        payload = data.model_dump()
        payload["tenant_id"] = tenant_id
        item = DingmaProductKnowledge(**payload)
        self.db.add(item)
        await self.db.flush()
        await self.db.refresh(item)
        logger.info(
            f"[DingmaProductKnowledge] 创建成功: {item.product_name} ({item.product_code})"
        )
        return self._to_response(item)

    async def update_item(
        self,
        item_id: int,
        data: ProductKnowledgeUpdate,
        scoped_tenant_id: Optional[int] = None,
    ) -> dict:
        """更新产品知识库记录"""
        item = await self._get_scoped_item(item_id, scoped_tenant_id)
        update_data = data.model_dump(exclude_unset=True)

        for field, value in update_data.items():
            setattr(item, field, value)

        await self.db.flush()
        await self.db.refresh(item)
        logger.info(
            f"[DingmaProductKnowledge] 更新成功: {item.product_name} (ID={item.id})"
        )
        return self._to_response(item)

    async def delete_item(
        self,
        item_id: int,
        scoped_tenant_id: Optional[int] = None,
    ) -> None:
        """删除产品知识库记录（物理删除）"""
        item = await self._get_scoped_item(item_id, scoped_tenant_id)
        await self.db.delete(item)
        await self.db.flush()
        logger.info(
            f"[DingmaProductKnowledge] 删除成功: {item.product_name} (ID={item.id})"
        )

    async def update_status(
        self,
        item_id: int,
        status: int,
        scoped_tenant_id: Optional[int] = None,
    ) -> dict:
        """更新启用状态"""
        if status not in (0, 1):
            raise BadRequestException("状态值必须为 0 或 1")
        item = await self._get_scoped_item(item_id, scoped_tenant_id)
        item.status = status
        await self.db.flush()
        await self.db.refresh(item)
        return self._to_response(item)
