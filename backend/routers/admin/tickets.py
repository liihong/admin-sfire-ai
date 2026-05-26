"""
工单管理接口
用于创建、查询、处理工单（开通会员、充值算力）
"""
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from db import get_db
from core.deps import get_current_admin_user
from core.tenant_helpers import resolve_admin_agent_scope_tenant_id
from models.admin_user import AdminUser
from schemas.ticket import TicketCreate, TicketQueryParams
from services.ticket import TicketService
from utils.response import success, page_response, ResponseMsg

router = APIRouter()


async def _admin_scope_tid(db: AsyncSession, admin: AdminUser) -> Optional[int]:
    return await resolve_admin_agent_scope_tenant_id(
        db,
        admin_tenant_id=admin.tenant_id,
        admin_username=admin.username,
    )


@router.get("", summary="获取工单列表")
async def get_tickets(
    pageNum: int = Query(1, ge=1, description="页码"),
    pageSize: int = Query(10, ge=1, le=100, description="每页数量"),
    type: Optional[str] = Query(None, description="工单类型：membership/recharge"),
    status: Optional[str] = Query(None, description="工单状态"),
    user_id: Optional[int] = Query(None, description="目标用户ID"),
    creator_id: Optional[int] = Query(None, description="创建人ID"),
    db: AsyncSession = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin_user),
):
    """获取工单列表（分页），支持按类型、状态、用户筛选"""
    params = TicketQueryParams(
        pageNum=pageNum,
        pageSize=pageSize,
        type=type,
        status=status,
        user_id=user_id,
        creator_id=creator_id,
    )
    service = TicketService(db)
    scope_tid = await _admin_scope_tid(db, current_admin)
    items, total = await service.get_ticket_list(params, scoped_tenant_id=scope_tid)
    return page_response(
        items=items,
        total=total,
        page_num=pageNum,
        page_size=pageSize,
    )


@router.get("/{ticket_id}", summary="获取工单详情")
async def get_ticket(
    ticket_id: int,
    db: AsyncSession = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin_user),
):
    """获取工单详情"""
    service = TicketService(db)
    scope_tid = await _admin_scope_tid(db, current_admin)
    data = await service.get_ticket_detail(ticket_id, scoped_tenant_id=scope_tid)
    return success(data=data)


@router.post("", summary="创建工单")
async def create_ticket(
    data: TicketCreate,
    current_admin: AdminUser = Depends(get_current_admin_user),
    db=Depends(get_db),
):
    """创建工单（开通会员或充值算力）"""
    service = TicketService(db)
    scope_tid = await _admin_scope_tid(db, current_admin)
    ticket = await service.create_ticket(
        data,
        creator_id=current_admin.id,
        scoped_tenant_id=scope_tid,
    )
    return success(data={"id": ticket.id}, msg=ResponseMsg.CREATED)


@router.post("/{ticket_id}/handle", summary="处理工单")
async def handle_ticket(
    ticket_id: int,
    current_admin: AdminUser = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """处理工单：执行开通会员或充值算力"""
    service = TicketService(db)
    scope_tid = await _admin_scope_tid(db, current_admin)
    data = await service.handle_ticket(
        ticket_id,
        handler_id=current_admin.id,
        scoped_tenant_id=scope_tid,
    )
    return success(data=data, msg="处理成功")
