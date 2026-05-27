"""
C 端公开接口可选租户范围（Query / Header → tenant id）

供首页、文章列表等匿名也可访问的接口使用；与 JWT 内 tid 无关。
"""
from typing import Optional, TYPE_CHECKING

from fastapi import Depends, Header, Query
from sqlalchemy.ext.asyncio import AsyncSession

from core.tenant_constants import DEFAULT_TENANT_ID, effective_tenant_id
from db import get_db
from services.tenant_resolver import resolve_client_public_tenant_id

if TYPE_CHECKING:
    from models.user import User


async def resolve_optional_public_tenant_id(
    tenant_id: Optional[str] = Query(
        None,
        description="租户主键（数字）或租户代码（如 dingma）；与 appid 同时出现时 appid 优先",
    ),
    appid: Optional[str] = Query(None, description="微信小程序 AppID"),
    x_wechat_app_id: Optional[str] = Header(None, alias="X-Wechat-App-Id"),
    x_tenant_code: Optional[str] = Header(None, alias="X-Tenant-Code"),
    db: AsyncSession = Depends(get_db),
) -> Optional[int]:
    wx = (x_wechat_app_id or appid or "").strip() or None
    tid_raw = (tenant_id or x_tenant_code or "").strip() or None
    return await resolve_client_public_tenant_id(
        db,
        tenant_id_raw=tid_raw,
        wechat_app_id=wx,
    )


def resolve_client_effective_tenant_id(
    current_user: Optional["User"],
    scoped_public_tenant_id: Optional[int],
) -> int:
    """
    C 端有效租户：优先 Query/Header 解析（子小程序显式传 tenant_id/appid），
    否则已登录用户归属租户，最后回落主租户。
    """
    if scoped_public_tenant_id is not None:
        return scoped_public_tenant_id
    if current_user is not None:
        return effective_tenant_id(current_user.tenant_id)
    return DEFAULT_TENANT_ID
