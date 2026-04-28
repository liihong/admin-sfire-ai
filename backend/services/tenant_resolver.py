"""
微信小程序 AppID → 租户解析（默认主租户=1）

未配置 tenants 表或未匹配时使用 DEFAULT_TENANT_ID，保证主小程序行为不变。
"""
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from core.tenant_constants import DEFAULT_TENANT_ID
from models.tenant import Tenant


async def resolve_tenant_id_by_wechat_app_id(
    db: AsyncSession,
    wechat_app_id: Optional[str] = None,
) -> int:
    """
    - wechat_app_id 为空则用 settings.WECHAT_APP_ID；
    - 在 tenants.wechat_app_id 中查找；若无记录则退回主租户 DEFAULT_TENANT_ID。
    """
    aid = (wechat_app_id or settings.WECHAT_APP_ID or "").strip()
    if not aid:
        return DEFAULT_TENANT_ID
    row = (
        await db.execute(select(Tenant.id).where(Tenant.wechat_app_id == aid))
    ).scalar_one_or_none()
    if row is not None:
        return int(row)
    return DEFAULT_TENANT_ID
