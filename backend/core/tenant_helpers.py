"""
租户访问控制辅助函数（B 端列表/写入过滤）

平台超级管理员：AdminUser.tenant_id IS NULL，不按租户过滤。
租户管理员：仅能访问本 tenant_id 数据。
"""
from __future__ import annotations

from typing import Optional, Sequence, Any, Union, Dict

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import ColumnElement

from core.tenant_constants import DEFAULT_TENANT_ID
from models.tenant import Tenant
from utils.exceptions import BadRequestException

# 登录名命中时，将数据范围改到 tenants.code 对应租户（修正误绑在主租户 id 或 tenant_id=NULL 的子品牌后台）
_AGENT_SCOPE_LOGIN_TO_TENANT_CODE: dict[str, str] = {
    "dingma": "dingma",
    "dingma_admin": "dingma",
}


def _login_brand_tenant_code(username: Optional[str]) -> Optional[str]:
    u = (username or "").strip().lower()
    code = _AGENT_SCOPE_LOGIN_TO_TENANT_CODE.get(u)
    if code is None and u.startswith("dingma_"):
        code = "dingma"
    return code


async def _tenant_id_by_code(db: AsyncSession, code: str) -> Optional[int]:
    r = await db.execute(select(Tenant.id).where(Tenant.code == code))
    alt = r.scalar_one_or_none()
    return int(alt) if alt is not None else None


async def resolve_admin_agent_scope_tenant_id(
    db: AsyncSession,
    *,
    admin_tenant_id: Optional[int],
    admin_username: Optional[str],
) -> Optional[int]:
    """
    B 端按租户隔离的数据范围 tenant_id（智能体、Banner、文章、快捷入口、首页配置、小程序用户、租户管理员等）。

    - admin.tenant_id 为空：一般为平台管理员，返回 None（不按租户过滤）。
      若登录名对应已知子品牌（如 dingma），则解析为该品牌在 tenants 表中的 id，
      避免子品牌管理员被误配成 tenant_id=NULL 时看到全平台数据。
    - 否则返回管理员所属租户；若为默认主租户 id 且登录名对应子品牌，
      则解析为该品牌租户 id（历史上误绑在主租户下的账号）。
    """
    brand_code = _login_brand_tenant_code(admin_username)

    if admin_tenant_id is None:
        if brand_code is None:
            return None
        return await _tenant_id_by_code(db, brand_code)

    tid = int(admin_tenant_id)
    if tid != DEFAULT_TENANT_ID:
        return tid

    if brand_code is None:
        return tid

    alt = await _tenant_id_by_code(db, brand_code)
    return alt if alt is not None else tid


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

