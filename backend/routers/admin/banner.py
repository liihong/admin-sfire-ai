"""
Banner Management Endpoints
Banner管理相关接口
"""
from typing import Optional
from fastapi import APIRouter, Depends, Query, Body
from sqlalchemy.ext.asyncio import AsyncSession

from db import get_db
from core.deps import get_current_admin_user
from core.tenant_helpers import resolve_admin_agent_scope_tenant_id
from models.admin_user import AdminUser
from schemas.banner import (
    BannerCreate,
    BannerUpdate,
    BannerQueryParams,
    BannerSortRequest,
    BannerStatusRequest,
)
from services.resource import BannerService
from utils.response import success, page_response, ResponseMsg

router = APIRouter()


async def _admin_scope_tid(db: AsyncSession, admin: AdminUser) -> Optional[int]:
    """与智能体、小程序用户一致：登录名纠偏 + 严格租户隔离"""
    return await resolve_admin_agent_scope_tenant_id(
        db,
        admin_tenant_id=admin.tenant_id,
        admin_username=admin.username,
    )


@router.get("", summary="获取Banner列表")
async def get_banners(
    pageNum: int = Query(1, ge=1, description="页码"),
    pageSize: int = Query(10, ge=1, le=1000, description="每页数量"),
    title: Optional[str] = Query(None, description="标题（模糊搜索）"),
    position: Optional[str] = Query(None, description="位置筛选"),
    is_enabled: Optional[bool] = Query(None, description="是否启用"),
    db: AsyncSession = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin_user),
):
    """
    获取Banner列表（分页）
    
    支持按标题、位置、状态筛选；租户管理员仅本租户数据。
    """
    banner_service = BannerService(db)
    scope_tid = await _admin_scope_tid(db, current_admin)

    params = BannerQueryParams(
        pageNum=pageNum,
        pageSize=pageSize,
        title=title,
        position=position,
        is_enabled=is_enabled,
    )

    banners, total = await banner_service.get_banners(params, scoped_tenant_id=scope_tid)

    return page_response(
        items=banners,
        total=total,
        page_num=pageNum,
        page_size=pageSize,
    )


@router.get("/{banner_id}", summary="获取Banner详情")
async def get_banner(
    banner_id: int,
    db: AsyncSession = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin_user),
):
    """获取Banner详情"""
    banner_service = BannerService(db)
    banner = await banner_service.get_banner_by_id(
        banner_id, scoped_tenant_id=await _admin_scope_tid(db, current_admin)
    )
    return success(data=banner)


@router.post("", summary="创建Banner")
async def create_banner(
    banner_data: BannerCreate,
    db: AsyncSession = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin_user),
):
    """创建新Banner"""
    banner_service = BannerService(db)
    banner = await banner_service.create_banner(
        banner_data,
        scoped_tenant_id=await _admin_scope_tid(db, current_admin),
    )
    return success(data=banner, msg=ResponseMsg.CREATED)


@router.put("/{banner_id}", summary="更新Banner")
async def update_banner(
    banner_id: int,
    banner_data: BannerUpdate,
    db: AsyncSession = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin_user),
):
    """更新Banner信息"""
    banner_service = BannerService(db)
    banner = await banner_service.update_banner(
        banner_id,
        banner_data,
        scoped_tenant_id=await _admin_scope_tid(db, current_admin),
    )
    return success(data=banner, msg=ResponseMsg.UPDATED)


@router.delete("/{banner_id}", summary="删除Banner")
async def delete_banner(
    banner_id: int,
    db: AsyncSession = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin_user),
):
    """删除Banner"""
    banner_service = BannerService(db)
    await banner_service.delete_banner(
        banner_id, scoped_tenant_id=await _admin_scope_tid(db, current_admin)
    )
    return success(msg=ResponseMsg.DELETED)


@router.put("/{banner_id}/status", summary="更新Banner状态")
async def update_banner_status(
    banner_id: int,
    request: BannerStatusRequest,
    db: AsyncSession = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin_user),
):
    """启用/禁用Banner"""
    banner_service = BannerService(db)
    banner = await banner_service.update_banner_status(
        banner_id,
        request.is_enabled,
        scoped_tenant_id=await _admin_scope_tid(db, current_admin),
    )
    return success(data=banner, msg=ResponseMsg.UPDATED)


@router.put("/sort", summary="批量更新Banner排序")
async def update_banner_sort(
    request: BannerSortRequest,
    db: AsyncSession = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin_user),
):
    """批量更新Banner排序"""
    banner_service = BannerService(db)
    await banner_service.update_banner_sort(
        request.items,
        scoped_tenant_id=await _admin_scope_tid(db, current_admin),
    )
    return success(msg="排序更新成功")
