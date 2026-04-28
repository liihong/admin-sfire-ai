"""
租户访问控制辅助函数（B 端列表/写入过滤）

平台超级管理员：AdminUser.tenant_id IS NULL，不按租户过滤。
租户管理员：仅能访问本 tenant_id 数据。
"""
from typing import Optional, Sequence, Any, Union, Dict

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import ColumnElement

from models.tenant import Tenant
from utils.exceptions import BadRequestException


def tenant_filter_expression(
    tenant_column,
    *,
    admin_tenant_id: Optional[int],
) -> Union[ColumnElement[Any], bool]:
    """
    - admin_tenant_id is None（平台管理员）→ 不加租户限制（返回恒真占位，调用方可省略追加）
    - 否则 tenant_column == admin_tenant_id
    """
    from sqlalchemy import true as sql_true

    if admin_tenant_id is None:
        return sql_true()
    return tenant_column == admin_tenant_id


def extend_conditions_with_tenant(
    conditions: Sequence,
    tenant_column,
    *,
    admin_tenant_id: Optional[int],
):
    """若当前管理员有租户限定，则在 conditions 上追加 tenant 条件。"""
    merged = list(conditions)
    if admin_tenant_id is not None:
        merged.append(tenant_column == admin_tenant_id)
    return merged


async def ensure_tenant_id_exists(db: AsyncSession, tenant_id: int) -> Tenant:
    """校验租户存在；不存在则抛出 BadRequest。"""
    result = await db.execute(select(Tenant).where(Tenant.id == tenant_id))
    t = result.scalar_one_or_none()
    if not t:
        raise BadRequestException(msg="租户不存在")
    return t


async def tenant_names_by_ids(db: AsyncSession, tenant_ids: set[int]) -> Dict[int, str]:
    """批量解析租户名称。"""
    if not tenant_ids:
        return {}
    result = await db.execute(select(Tenant.id, Tenant.name).where(Tenant.id.in_(tenant_ids)))
    return {row[0]: row[1] for row in result.all()}

