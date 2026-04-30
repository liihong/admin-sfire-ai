"""
Quick Entry Management Endpoints
快捷入口管理相关接口
"""
from typing import Optional
from fastapi import APIRouter, Depends, Query, Body
from sqlalchemy.ext.asyncio import AsyncSession

from db import get_db
from core.deps import get_current_admin_user
from core.tenant_helpers import resolve_admin_agent_scope_tenant_id
from models.admin_user import AdminUser
from schemas.quick_entry import (
    QuickEntryCreate,
    QuickEntryUpdate,
    QuickEntryQueryParams,
    QuickEntrySortRequest,
    QuickEntryStatusRequest,
)
from services.resource import QuickEntryService
from utils.response import success, page_response, ResponseMsg

router = APIRouter()


async def _admin_scope_tid(db: AsyncSession, admin: AdminUser) -> Optional[int]:
    """与智能体、小程序用户一致：登录名纠偏 + 严格租户隔离"""
    return await resolve_admin_agent_scope_tenant_id(
        db,
        admin_tenant_id=admin.tenant_id,
        admin_username=admin.username,
    )


@router.get("", summary="获取快捷入口列表")
async def get_quick_entries(
    pageNum: int = Query(1, ge=1, description="页码"),
    pageSize: int = Query(10, ge=1, le=1000, description="每页数量"),
    type: Optional[str] = Query(None, description="入口类型筛选（category/command）"),
    status: Optional[int] = Query(None, ge=0, le=2, description="状态筛选（0-禁用, 1-启用, 2-即将上线）"),
    tag: Optional[str] = Query(None, description="标签筛选（none/new/hot）"),
    title: Optional[str] = Query(None, description="标题（模糊搜索）"),
    db: AsyncSession = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin_user),
):
    """
    获取快捷入口列表（分页）
    
    支持按类型、状态、标签、标题筛选；租户管理员仅本租户数据。
    """
    quick_entry_service = QuickEntryService(db)
    scope_tid = await _admin_scope_tid(db, current_admin)

    params = QuickEntryQueryParams(
        pageNum=pageNum,
        pageSize=pageSize,
        type=type,
        status=status,
        tag=tag,
        title=title,
    )

    entries, total = await quick_entry_service.get_quick_entries(
        params, scoped_tenant_id=scope_tid
    )

    return page_response(
        items=entries,
        total=total,
        page_num=pageNum,
        page_size=pageSize,
    )


@router.get("/{entry_id}", summary="获取快捷入口详情")
async def get_quick_entry(
    entry_id: int,
    db: AsyncSession = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin_user),
):
    """获取快捷入口详情"""
    quick_entry_service = QuickEntryService(db)
    entry = await quick_entry_service.get_quick_entry_by_id(
        entry_id, scoped_tenant_id=await _admin_scope_tid(db, current_admin)
    )
    return success(data=entry)


@router.post("", summary="创建快捷入口")
async def create_quick_entry(
    entry_data: QuickEntryCreate,
    db: AsyncSession = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin_user),
):
    """创建新快捷入口"""
    quick_entry_service = QuickEntryService(db)
    entry = await quick_entry_service.create_quick_entry(
        entry_data,
        scoped_tenant_id=await _admin_scope_tid(db, current_admin),
    )
    return success(data=entry, msg=ResponseMsg.CREATED)


@router.put("/{entry_id}", summary="更新快捷入口")
async def update_quick_entry(
    entry_id: int,
    entry_data: QuickEntryUpdate,
    db: AsyncSession = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin_user),
):
    """更新快捷入口信息"""
    quick_entry_service = QuickEntryService(db)
    entry = await quick_entry_service.update_quick_entry(
        entry_id,
        entry_data,
        scoped_tenant_id=await _admin_scope_tid(db, current_admin),
    )
    return success(data=entry, msg=ResponseMsg.UPDATED)


@router.delete("/{entry_id}", summary="删除快捷入口")
async def delete_quick_entry(
    entry_id: int,
    db: AsyncSession = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin_user),
):
    """删除快捷入口"""
    quick_entry_service = QuickEntryService(db)
    await quick_entry_service.delete_quick_entry(
        entry_id, scoped_tenant_id=await _admin_scope_tid(db, current_admin)
    )
    return success(msg=ResponseMsg.DELETED)


@router.put("/{entry_id}/status", summary="更新快捷入口状态")
async def update_quick_entry_status(
    entry_id: int,
    request: QuickEntryStatusRequest,
    db: AsyncSession = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin_user),
):
    """启用/禁用快捷入口或设置为即将上线"""
    quick_entry_service = QuickEntryService(db)
    entry = await quick_entry_service.update_quick_entry_status(
        entry_id,
        request.status,
        scoped_tenant_id=await _admin_scope_tid(db, current_admin),
    )
    return success(data=entry, msg=ResponseMsg.UPDATED)


@router.put("/sort", summary="批量更新快捷入口排序")
async def update_quick_entry_sort(
    request: QuickEntrySortRequest,
    db: AsyncSession = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin_user),
):
    """批量更新快捷入口排序"""
    quick_entry_service = QuickEntryService(db)
    await quick_entry_service.update_quick_entry_sort(
        request.items,
        scoped_tenant_id=await _admin_scope_tid(db, current_admin),
    )
    return success(msg="排序更新成功")
