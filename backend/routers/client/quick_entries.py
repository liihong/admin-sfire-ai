"""
Quick Entry Client Endpoints
快捷入口客户端接口
"""
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, asc, and_
from sqlalchemy.ext.asyncio import AsyncSession

from db import get_db
from models.quick_entry import QuickEntry, EntryType
from services.resource import QuickEntryService
from utils.response import success

router = APIRouter()


@router.get("", summary="获取启用的快捷入口列表")
async def get_quick_entries(
    type: Optional[str] = Query(None, description="入口类型筛选（category-今天拍点啥, command-快捷指令库）"),
    agent_type: Optional[str] = Query(None, description="Agent类型筛选（关联sys_dict id=3的字典项）"),
    db: AsyncSession = Depends(get_db),
):
    """
    获取启用的快捷入口列表
    
    只返回 status=1（启用）的入口，按 priority 排序
    根据 agent_type 增加 agent_type_name 字段，显示数据字典对应的名称
    """
    quick_entry_service = QuickEntryService(db)
    
    # 构建查询条件
    conditions = []
    
    # 只返回启用的入口
    conditions.append(QuickEntry.status == 1)
    
    # 按类型筛选
    if type:
        type_enum = EntryType(type)
        conditions.append(QuickEntry.type == type_enum)
    
    # 按 agent_type 筛选
    if agent_type:
        conditions.append(QuickEntry.agent_type == agent_type)
    
    # 查询数据（按 priority 排序）
    query = select(QuickEntry)
    if conditions:
        query = query.where(and_(*conditions))
    query = query.order_by(asc(QuickEntry.priority))
    
    result = await db.execute(query)
    entries = result.scalars().all()
    
    # 查询 agent_type 对应的字典名称（sys_dict id=3）
    agent_types = {e.agent_type for e in entries if e.agent_type}
    agent_type_names = await quick_entry_service._get_agent_type_names(agent_types)
    
    # 格式化响应，附加 agent_type_name
    entry_list = []
    for entry in entries:
        item = quick_entry_service._format_response(
            entry,
            agent_type_names.get(entry.agent_type) if entry.agent_type else None,
        )
        entry_list.append(item)
    
    return success(data={"entries": entry_list}, msg="获取成功")

