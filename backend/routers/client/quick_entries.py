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
    db: AsyncSession = Depends(get_db),
):
    """
    获取启用的快捷入口列表
    
    只返回 status=1（启用）的入口，按 priority 排序
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
    
    # 查询数据（按 priority 排序）
    query = select(QuickEntry)
    if conditions:
        query = query.where(and_(*conditions))
    query = query.order_by(asc(QuickEntry.priority))
    
    result = await db.execute(query)
    entries = result.scalars().all()
    
    # 格式化响应
    entry_list = [quick_entry_service._format_response(entry) for entry in entries]
    
    return success(data={"entries": entry_list}, msg="获取成功")

