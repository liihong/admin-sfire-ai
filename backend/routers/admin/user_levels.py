"""
管理后台用户等级管理接口
提供用户等级配置的CRUD操作
"""
from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from db import get_db
from core.deps import get_current_admin_user
from models.admin_user import AdminUser
from services.system.user_level import UserLevelService
from schemas.user_level import (
    UserLevelCreate,
    UserLevelUpdate,
    UserLevelResponse,
)
from utils.response import success, page_response
from schemas.common import PageParams

router = APIRouter()


@router.get("", summary="获取用户等级列表")
async def list_user_levels(
    page_params: PageParams = Depends(),
    db: AsyncSession = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin_user),
):
    """获取用户等级列表（分页）"""
    user_level_service = UserLevelService(db)
    
    items, total = await user_level_service.get_list(
        offset=page_params.offset,
        limit=page_params.pageSize,
    )
    
    return page_response(
        items=items,
        total=total,
        page_num=page_params.pageNum,
        page_size=page_params.pageSize,
        msg="获取成功"
    )


@router.get("/all", summary="获取所有启用的用户等级")
async def get_all_enabled_levels(
    db: AsyncSession = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin_user),
):
    """获取所有启用的用户等级（不分页，用于下拉选择）"""
    user_level_service = UserLevelService(db)
    levels = await user_level_service.get_all_enabled_levels()
    
    return success(
        data=[UserLevelResponse.model_validate(level) for level in levels],
        msg="获取成功"
    )


@router.get("/{level_id}", summary="获取用户等级详情")
async def get_user_level(
    level_id: int,
    db: AsyncSession = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin_user),
):
    """获取指定用户等级的详情"""
    user_level_service = UserLevelService(db)
    level = await user_level_service.get_by_id(level_id)
    
    return success(
        data=UserLevelResponse.model_validate(level),
        msg="获取成功"
    )


@router.post("", summary="创建用户等级")
async def create_user_level(
    data: UserLevelCreate,
    db: AsyncSession = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin_user),
):
    """创建新的用户等级配置"""
    user_level_service = UserLevelService(db)
    
    # 检查code是否已存在
    existing = await user_level_service.get_level_by_code(data.code)
    if existing:
        from utils.exceptions import BadRequestException
        raise BadRequestException(f"等级代码 '{data.code}' 已存在")
    
    level = await user_level_service.create(
        data,
        unique_fields={
            "code": {"error_msg": f"等级代码 '{data.code}' 已存在"}
        }
    )
    
    return success(
        data=UserLevelResponse.model_validate(level),
        msg="创建成功"
    )


@router.put("/{level_id}", summary="更新用户等级")
async def update_user_level(
    level_id: int,
    data: UserLevelUpdate,
    db: AsyncSession = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin_user),
):
    """更新用户等级配置"""
    user_level_service = UserLevelService(db)
    
    level = await user_level_service.update(level_id, data)
    
    return success(
        data=UserLevelResponse.model_validate(level),
        msg="更新成功"
    )


@router.delete("/{level_id}", summary="删除用户等级")
async def delete_user_level(
    level_id: int,
    db: AsyncSession = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin_user),
):
    """删除用户等级配置（硬删除）"""
    user_level_service = UserLevelService(db)
    
    await user_level_service.delete(level_id, hard_delete=True)
    
    return success(msg="删除成功")

