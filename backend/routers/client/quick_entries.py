"""
Quick Entry Client Endpoints
快捷入口客户端接口
"""
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from db import get_db
from models.quick_entry import EntryType
from services.resource import QuickEntryService
from utils.response import success
from core.client_public_scope import resolve_optional_public_tenant_id
from core.tenant_constants import DEFAULT_TENANT_ID

router = APIRouter()


@router.get("", summary="获取启用的快捷入口列表")
async def get_quick_entries(
    type: Optional[str] = Query(None, description="入口类型筛选（category-今天拍点啥, command-快捷指令库）"),
    agent_type: Optional[str] = Query(None, description="Agent类型筛选（关联sys_dict id=3的字典项）"),
    scoped_tenant_id: Optional[int] = Depends(resolve_optional_public_tenant_id),
    db: AsyncSession = Depends(get_db),
):
    """
    获取启用的快捷入口列表

    按租户隔离：Query tenant_id / appid 或 Header 解析租户；均未命中时默认主租户（与 C 端智能体列表一致）。
    只返回 status=1（启用）的入口，按 priority 排序。
    根据 agent_type 增加 agent_type_name 字段，显示数据字典对应的名称。
    """
    quick_entry_service = QuickEntryService(db)

    effective_tenant_id = (
        scoped_tenant_id if scoped_tenant_id is not None else DEFAULT_TENANT_ID
    )

    entry_type_enum = EntryType(type) if type else None

    entry_list = await quick_entry_service.list_public_enabled_entries(
        effective_tenant_id,
        entry_type=entry_type_enum,
        agent_type=agent_type,
    )

    return success(data={"entries": entry_list}, msg="获取成功")
