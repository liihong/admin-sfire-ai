"""C 端租户公开配置"""
from typing import Optional

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from core.client_public_scope import resolve_optional_public_tenant_id
from db import get_db
from services.tenant_service import TenantService
from utils.response import success

router = APIRouter()


@router.get("/config", summary="获取租户公开配置")
async def get_tenant_public_config(
    scoped_tenant_id: Optional[int] = Depends(resolve_optional_public_tenant_id),
    db: AsyncSession = Depends(get_db),
):
    """
    返回当前租户公开配置（无需登录）。

    - release_review_enabled: 是否开启上线审查；开启时小程序隐藏会员权益入口
    """
    svc = TenantService(db)
    data = await svc.get_public_config_for_scope(scoped_tenant_id)
    return success(data=data, msg="获取成功")
