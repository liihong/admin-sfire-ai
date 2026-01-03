"""
Home Config Management Endpoints
首页配置管理相关接口
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.schemas.home_config import (
    HomeConfigUpdate,
    HomeConfigBatchUpdate,
)
from app.services.home_config import HomeConfigService
from app.utils.response import success, ResponseMsg

router = APIRouter()


@router.get("", summary="获取所有配置")
async def get_all_configs(
    use_cache: bool = Query(True, description="是否使用缓存"),
    db: AsyncSession = Depends(get_db),
):
    """
    获取所有首页配置
    
    返回所有配置项的列表
    """
    config_service = HomeConfigService(db)
    configs = await config_service.get_all_configs()
    return success(data={"list": configs, "total": len(configs)})


@router.get("/{config_key}", summary="获取指定配置")
async def get_config(
    config_key: str,
    use_cache: bool = Query(True, description="是否使用缓存"),
    db: AsyncSession = Depends(get_db),
):
    """
    根据配置键获取配置
    
    Args:
        config_key: 配置键，如 home_title, home_subtitle 等
    """
    config_service = HomeConfigService(db)
    config = await config_service.get_config_by_key(config_key, use_cache=use_cache)
    return success(data=config)


@router.put("/{config_key}", summary="更新配置")
async def update_config(
    config_key: str,
    config_data: HomeConfigUpdate,
    db: AsyncSession = Depends(get_db),
):
    """
    更新指定配置
    
    Args:
        config_key: 配置键
        config_data: 配置更新数据
    """
    config_service = HomeConfigService(db)
    config = await config_service.update_config(config_key, config_data)
    return success(data=config, msg=ResponseMsg.UPDATED)


@router.post("/batch", summary="批量更新配置")
async def batch_update_configs(
    batch_data: HomeConfigBatchUpdate,
    db: AsyncSession = Depends(get_db),
):
    """
    批量更新配置
    
    可以一次性更新多个配置项
    """
    config_service = HomeConfigService(db)
    configs = await config_service.batch_update_configs(batch_data)
    return success(data={"list": configs, "total": len(configs)}, msg="批量更新成功")

