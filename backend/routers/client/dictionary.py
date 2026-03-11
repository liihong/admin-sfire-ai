"""
Dictionary Client Endpoints
数据字典客户端接口 - 供小程序/PC端获取字典选项
"""
from typing import Optional
from fastapi import APIRouter, Depends, Query

from db import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from services.system.dictionary import DictionaryService
from utils.response import success

router = APIRouter()


@router.get("/items", summary="根据字典ID获取字典项列表")
async def get_dict_items(
    dict_id: int = Query(..., description="字典ID"),
    enabled_only: Optional[bool] = Query(True, description="是否只返回启用的项"),
    db: AsyncSession = Depends(get_db),
):
    """
    根据 dict_id 查询 sys_dict_item 字典项列表
    
    返回格式: [{ label, value }, ...]
    用于下拉选项、表单选择等场景
    """
    service = DictionaryService(db)
    items = await service.get_items_by_dict_id(dict_id=dict_id, enabled_only=enabled_only)
    return success(data={"items": items}, msg="获取成功")
