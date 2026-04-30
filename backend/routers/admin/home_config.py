"""
Home Config Management Endpoints
首页配置管理相关接口
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from typing import Optional

from db import get_db
from core.deps import get_current_admin_user
from core.tenant_helpers import resolve_admin_agent_scope_tenant_id
from models.admin_user import AdminUser
from schemas.home_config import (
    HomeConfigUpdate,
    HomeConfigBatchUpdate,
)
from services.system import HomeConfigService
from utils.response import success, ResponseMsg

router = APIRouter()


async def _admin_scope_tid(db: AsyncSession, admin: AdminUser) -> Optional[int]:
    """与智能体、小程序用户一致：登录名纠偏 + 严格租户隔离"""
    return await resolve_admin_agent_scope_tenant_id(
        db,
        admin_tenant_id=admin.tenant_id,
        admin_username=admin.username,
    )


@router.get("", summary="获取所有配置")
async def get_all_configs(
    use_cache: bool = Query(True, description="是否使用缓存"),
    db: AsyncSession = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin_user),
):
    """
    获取所有首页配置
    
    租户管理员仅返回本租户配置项。
    """
    config_service = HomeConfigService(db)
    configs = await config_service.get_all_configs(
        scoped_tenant_id=await _admin_scope_tid(db, current_admin),
    )
    return success(data={"list": configs, "total": len(configs)})


@router.get("/{config_key}", summary="获取指定配置")
async def get_config(
    config_key: str,
    use_cache: bool = Query(True, description="是否使用缓存"),
    db: AsyncSession = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin_user),
):
    """
    根据配置键获取配置
    
    Args:
        config_key: 配置键，如 home_title, home_subtitle 等
    """
    config_service = HomeConfigService(db)
    config = await config_service.get_config_by_key(
        config_key,
        scoped_tenant_id=await _admin_scope_tid(db, current_admin),
        use_cache=use_cache,
    )
    return success(data=config)


@router.put("/{config_key}", summary="更新配置")
async def update_config(
    config_key: str,
    config_data: HomeConfigUpdate,
    db: AsyncSession = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin_user),
):
    """
    更新指定配置
    
    Args:
        config_key: 配置键
        config_data: 配置更新数据
    """
    config_service = HomeConfigService(db)
    config = await config_service.update_config(
        config_key,
        config_data,
        scoped_tenant_id=await _admin_scope_tid(db, current_admin),
    )
    return success(data=config, msg=ResponseMsg.UPDATED)


@router.post("/batch", summary="批量更新配置")
async def batch_update_configs(
    batch_data: HomeConfigBatchUpdate,
    db: AsyncSession = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin_user),
):
    """
    批量更新配置
    
    可以一次性更新多个配置项
    """
    config_service = HomeConfigService(db)
    configs = await config_service.batch_update_configs(
        batch_data,
        scoped_tenant_id=await _admin_scope_tid(db, current_admin),
    )
    return success(data={"list": configs, "total": len(configs)}, msg="批量更新成功")

