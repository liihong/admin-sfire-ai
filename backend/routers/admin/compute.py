"""
算力明细管理接口
提供系统统计、用户汇总、用户流水明细
"""
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from db import get_db
from core.deps import get_current_admin_user
from core.tenant_helpers import resolve_admin_agent_scope_tenant_id
from models.admin_user import AdminUser
from services.resource import ComputeService
from utils.response import success, page_response

router = APIRouter()


async def _admin_scope_tid(db: AsyncSession, admin: AdminUser) -> Optional[int]:
    return await resolve_admin_agent_scope_tenant_id(
        db,
        admin_tenant_id=admin.tenant_id,
        admin_username=admin.username,
    )


@router.get("/stats", summary="获取系统算力统计")
async def get_compute_stats(
    db: AsyncSession = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin_user),
):
    """
    获取系统级算力统计
    - totalConsume: 系统总消耗
    - totalRecharge: 系统总充值
    """
    service = ComputeService(db)
    scope_tid = await _admin_scope_tid(db, current_admin)
    data = await service.get_system_statistics(scoped_tenant_id=scope_tid)
    return success(data=data, msg="获取成功")


@router.get("/users", summary="获取用户算力汇总列表")
async def get_compute_user_summary(
    pageNum: int = Query(1, ge=1, description="页码"),
    pageSize: int = Query(10, ge=1, le=100, description="每页数量"),
    username: Optional[str] = Query(None, description="用户名模糊搜索"),
    startTime: Optional[str] = Query(None, description="开始时间 ISO 格式"),
    endTime: Optional[str] = Query(None, description="结束时间 ISO 格式"),
    db: AsyncSession = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin_user),
):
    """
    获取用户算力汇总列表（分页）
    按用户分组统计总消耗、总充值
    """
    service = ComputeService(db)
    scope_tid = await _admin_scope_tid(db, current_admin)
    items, total = await service.get_user_summary_list(
        page_num=pageNum,
        page_size=pageSize,
        username=username,
        start_time=startTime,
        end_time=endTime,
        scoped_tenant_id=scope_tid,
    )
    return page_response(
        items=items,
        total=total,
        page_num=pageNum,
        page_size=pageSize,
        msg="获取成功",
    )


@router.get("/users/{user_id}/logs", summary="获取用户算力流水明细")
async def get_user_compute_logs(
    user_id: int,
    pageNum: int = Query(1, ge=1, description="页码"),
    pageSize: int = Query(10, ge=1, le=100, description="每页数量"),
    type: Optional[str] = Query(None, description="流水类型：consume/recharge"),
    db: AsyncSession = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin_user),
):
    """
    获取指定用户的算力消耗和充值明细
    支持按类型筛选（consume-消耗, recharge-充值）
    """
    service = ComputeService(db)
    scope_tid = await _admin_scope_tid(db, current_admin)
    result = await service.get_user_compute_logs(
        user_id=user_id,
        page_num=pageNum,
        page_size=pageSize,
        log_type=type,
        scoped_tenant_id=scope_tid,
    )
    return page_response(
        items=result.list,
        total=result.total,
        page_num=result.pageNum,
        page_size=result.pageSize,
        msg="获取成功",
    )
