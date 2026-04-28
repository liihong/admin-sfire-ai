"""租户管理"""
from typing import List, Tuple, Optional

from sqlalchemy import select, func, update, and_
from sqlalchemy.ext.asyncio import AsyncSession

from models.tenant import Tenant
from schemas.tenant import TenantCreate, TenantUpdate, TenantQueryParams
from utils.exceptions import NotFoundException, BadRequestException


class TenantService:
    def __init__(self, db: AsyncSession):
        self.db = db

    def _to_dict(self, t: Tenant) -> dict:
        return {
            "id": t.id,
            "code": t.code,
            "name": t.name,
            "is_default": bool(t.is_default),
            "remark": t.remark,
            "wechat_app_id": t.wechat_app_id,
            "created_at": t.created_at.isoformat() if t.created_at else None,
            "updated_at": t.updated_at.isoformat() if t.updated_at else None,
        }

    async def list_tenants(
        self,
        params: TenantQueryParams,
    ) -> Tuple[List[dict], int]:
        conditions = []
        if params.code:
            conditions.append(Tenant.code.like(f"%{params.code}%"))
        if params.name:
            conditions.append(Tenant.name.like(f"%{params.name}%"))

        total_q = select(func.count(Tenant.id))
        q = select(Tenant).order_by(Tenant.id.asc())
        if conditions:
            where_clause = and_(*conditions)
            total_q = total_q.where(where_clause)
            q = q.where(where_clause)
        total = (await self.db.execute(total_q)).scalar() or 0

        q = q.offset(params.offset).limit(params.pageSize)
        rows = (await self.db.execute(q)).scalars().all()
        return [self._to_dict(t) for t in rows], total

    async def list_options(self) -> List[dict]:
        q = select(Tenant).order_by(Tenant.id.asc())
        rows = (await self.db.execute(q)).scalars().all()
        return [{"id": t.id, "code": t.code, "name": t.name} for t in rows]

    async def list_options_for_admin(self, *, scoped_tenant_id: Optional[int]) -> List[dict]:
        """平台管理员返回全部；租户管理员仅返回本租户。"""
        if scoped_tenant_id is None:
            return await self.list_options()
        q = select(Tenant).where(Tenant.id == scoped_tenant_id)
        row = (await self.db.execute(q)).scalar_one_or_none()
        if not row:
            return []
        return [{"id": row.id, "code": row.code, "name": row.name}]

    async def get_by_id(self, tenant_id: int) -> dict:
        result = await self.db.execute(select(Tenant).where(Tenant.id == tenant_id))
        t = result.scalar_one_or_none()
        if not t:
            raise NotFoundException(msg="租户不存在")
        return self._to_dict(t)

    async def _unset_other_defaults(self, except_id: Optional[int] = None) -> None:
        stmt = update(Tenant).values(is_default=False)
        if except_id is not None:
            stmt = stmt.where(Tenant.id != except_id)
        await self.db.execute(stmt)

    async def create(self, data: TenantCreate) -> dict:
        dup = await self.db.execute(select(Tenant.id).where(Tenant.code == data.code))
        if dup.scalar_one_or_none():
            raise BadRequestException(msg="租户代码已存在")

        if data.is_default:
            await self._unset_other_defaults()

        tenant = Tenant(
            code=data.code.strip(),
            name=data.name.strip(),
            is_default=data.is_default,
            remark=data.remark,
            wechat_app_id=data.wechat_app_id,
        )
        self.db.add(tenant)
        await self.db.commit()
        await self.db.refresh(tenant)
        return self._to_dict(tenant)

    async def update(self, tenant_id: int, data: TenantUpdate) -> dict:
        result = await self.db.execute(select(Tenant).where(Tenant.id == tenant_id))
        tenant = result.scalar_one_or_none()
        if not tenant:
            raise NotFoundException(msg="租户不存在")

        patch = data.model_dump(exclude_unset=True)
        if "code" in patch and patch["code"] and patch["code"] != tenant.code:
            dup = await self.db.execute(
                select(Tenant.id).where(Tenant.code == patch["code"], Tenant.id != tenant_id)
            )
            if dup.scalar_one_or_none():
                raise BadRequestException(msg="租户代码已占用")

        if patch.get("is_default") is True:
            await self._unset_other_defaults(except_id=tenant_id)

        for k, v in patch.items():
            setattr(tenant, k, v)

        await self.db.commit()
        await self.db.refresh(tenant)
        return self._to_dict(tenant)
