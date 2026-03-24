"""
工具包配置服务
"""
from typing import List, Tuple

from sqlalchemy import select, func, or_, and_, asc
from sqlalchemy.ext.asyncio import AsyncSession

from models.tool_package import ToolPackage
from schemas.tool_package import (
    ToolPackageCreate,
    ToolPackageUpdate,
    ToolPackageQueryParams,
)
from utils.exceptions import NotFoundException, BadRequestException
from services.base import BaseService


class ToolPackageService(BaseService):
    """工具包配置"""

    def __init__(self, db: AsyncSession):
        super().__init__(db, ToolPackage, "工具包", check_soft_delete=False)

    def _to_dict(self, row: ToolPackage) -> dict:
        return {
            "id": row.id,
            "code": row.code,
            "name": row.name,
            "description": row.description,
            "icon": row.icon,
            "sort_order": row.sort_order,
            "status": row.status,
            "created_at": row.created_at.isoformat() if row.created_at else None,
            "updated_at": row.updated_at.isoformat() if row.updated_at else None,
        }

    async def list_page(self, params: ToolPackageQueryParams) -> Tuple[List[dict], int]:
        q = select(ToolPackage)
        conditions = []
        if params.status is not None:
            conditions.append(ToolPackage.status == params.status)
        if params.keyword:
            kw = f"%{params.keyword.strip()}%"
            conditions.append(
                or_(
                    ToolPackage.name.like(kw),
                    ToolPackage.code.like(kw),
                )
            )
        if conditions:
            q = q.where(and_(*conditions))

        count_q = select(func.count(ToolPackage.id))
        if conditions:
            count_q = count_q.where(and_(*conditions))
        total = (await self.db.execute(count_q)).scalar_one()

        q = q.order_by(asc(ToolPackage.sort_order), asc(ToolPackage.id)).offset(
            params.offset
        ).limit(params.pageSize)
        rows = (await self.db.execute(q)).scalars().all()
        return [self._to_dict(r) for r in rows], total

    async def list_enabled_public(self) -> List[dict]:
        q = (
            select(ToolPackage)
            .where(ToolPackage.status == 1)
            .order_by(asc(ToolPackage.sort_order), asc(ToolPackage.id))
        )
        rows = (await self.db.execute(q)).scalars().all()
        return [self._to_dict(r) for r in rows]

    async def get_detail(self, pk: int) -> dict:
        row = await super().get_by_id(pk)
        return self._to_dict(row)

    async def get_by_code(self, code: str) -> dict:
        code = code.strip().lower()
        q = select(ToolPackage).where(ToolPackage.code == code)
        row = (await self.db.execute(q)).scalar_one_or_none()
        if not row:
            raise NotFoundException("工具包不存在")
        return self._to_dict(row)

    async def get_public_by_code(self, code: str) -> dict:
        data = await self.get_by_code(code)
        if data["status"] != 1:
            raise NotFoundException("工具包不存在或已停用")
        return data

    async def create(self, body: ToolPackageCreate) -> dict:
        exists = await self.db.execute(
            select(ToolPackage.id).where(ToolPackage.code == body.code).limit(1)
        )
        if exists.scalar_one_or_none():
            raise BadRequestException(f"code 已存在: {body.code}")
        row = ToolPackage(
            code=body.code,
            name=body.name,
            description=body.description,
            icon=body.icon,
            sort_order=body.sort_order,
            status=body.status,
        )
        self.db.add(row)
        await self.db.flush()
        await self.db.refresh(row)
        return self._to_dict(row)

    async def update(self, pk: int, body: ToolPackageUpdate) -> dict:
        row = await super().get_by_id(pk)
        data = body.model_dump(exclude_unset=True)
        if "code" in data and data["code"] != row.code:
            exists = await self.db.execute(
                select(ToolPackage.id).where(ToolPackage.code == data["code"]).limit(1)
            )
            if exists.scalar_one_or_none():
                raise BadRequestException(f"code 已存在: {data['code']}")
        for k, v in data.items():
            setattr(row, k, v)
        await self.db.flush()
        await self.db.refresh(row)
        return self._to_dict(row)

    async def update_sort(self, items: List[tuple[int, int]]) -> None:
        for pk, sort_order in items:
            row = await super().get_by_id(pk)
            row.sort_order = sort_order
        await self.db.flush()
