"""
数据字典管理 Endpoints
提供字典类型和字典项的 CRUD 接口
"""
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from db import get_db
from schemas.dictionary import (
    DictCreate,
    DictUpdate,
    DictQueryParams,
    DictResponse,
    DictWithItemsResponse,
    DictItemCreate,
    DictItemUpdate,
    DictItemQueryParams,
    DictItemResponse,
)
from services.dictionary import DictionaryService
from utils.response import success, page_response

router = APIRouter()


# ============== 字典类型接口 ==============

@router.get("", summary="获取字典类型列表")
async def get_dict_list(
    pageNum: int = Query(1, ge=1, description="页码"),
    pageSize: int = Query(10, ge=1, le=100, description="每页数量"),
    dict_code: Optional[str] = Query(None, description="字典编码（精确匹配）"),
    dict_name: Optional[str] = Query(None, description="字典名称（模糊查询）"),
    is_enabled: Optional[bool] = Query(None, description="是否启用"),
    db: AsyncSession = Depends(get_db),
):
    """
    获取字典类型列表（分页）
    
    支持按编码、名称、启用状态筛选
    """
    service = DictionaryService(db)
    
    params = DictQueryParams(
        pageNum=pageNum,
        pageSize=pageSize,
        dict_code=dict_code,
        dict_name=dict_name,
        is_enabled=is_enabled,
    )
    
    items, total = await service.get_dict_list(params)
    
    return page_response(
        items=[DictResponse.model_validate(item).model_dump() for item in items],
        total=total,
        page_num=pageNum,
        page_size=pageSize,
    )


@router.get("/all", summary="获取所有字典类型")
async def get_all_dicts(
    is_enabled: Optional[bool] = Query(None, description="是否启用"),
    db: AsyncSession = Depends(get_db),
):
    """
    获取所有字典类型（不分页，用于下拉选择）
    """
    service = DictionaryService(db)
    
    params = DictQueryParams(
        pageNum=1,
        pageSize=1000,  # 获取所有
        is_enabled=is_enabled,
    )
    
    items, _ = await service.get_dict_list(params)
    
    return success(
        data=[DictResponse.model_validate(item).model_dump() for item in items]
    )


@router.get("/{dict_id}", summary="获取字典类型详情")
async def get_dict_detail(
    dict_id: int,
    with_items: bool = Query(False, description="是否包含字典项"),
    db: AsyncSession = Depends(get_db),
):
    """获取字典类型详情"""
    service = DictionaryService(db)
    dict_obj = await service.get_dict_by_id(dict_id, with_items=with_items)
    
    if with_items:
        response = DictWithItemsResponse.model_validate(dict_obj)
    else:
        response = DictResponse.model_validate(dict_obj)
    
    return success(data=response.model_dump())


@router.post("", summary="创建字典类型")
async def create_dict(
    data: DictCreate,
    db: AsyncSession = Depends(get_db),
):
    """创建字典类型"""
    service = DictionaryService(db)
    dict_obj = await service.create_dict(data)
    await db.commit()
    
    return success(
        data=DictResponse.model_validate(dict_obj).model_dump(),
        msg="创建成功"
    )


@router.put("/{dict_id}", summary="更新字典类型")
async def update_dict(
    dict_id: int,
    data: DictUpdate,
    db: AsyncSession = Depends(get_db),
):
    """更新字典类型"""
    service = DictionaryService(db)
    dict_obj = await service.update_dict(dict_id, data)
    await db.commit()
    
    return success(
        data=DictResponse.model_validate(dict_obj).model_dump(),
        msg="更新成功"
    )


@router.delete("/{dict_id}", summary="删除字典类型")
async def delete_dict(
    dict_id: int,
    db: AsyncSession = Depends(get_db),
):
    """删除字典类型（级联删除所有字典项）"""
    service = DictionaryService(db)
    await service.delete_dict(dict_id)
    await db.commit()
    
    return success(msg="删除成功")


# ============== 字典项接口 ==============

@router.get("/items/list", summary="获取字典项列表")
async def get_dict_item_list(
    pageNum: int = Query(1, ge=1, description="页码"),
    pageSize: int = Query(10, ge=1, le=100, description="每页数量"),
    dict_id: Optional[int] = Query(None, description="关联字典ID"),
    dict_code: Optional[str] = Query(None, description="字典编码"),
    item_value: Optional[str] = Query(None, description="选项值（模糊查询）"),
    item_label: Optional[str] = Query(None, description="显示标签（模糊查询）"),
    is_enabled: Optional[bool] = Query(None, description="是否启用"),
    db: AsyncSession = Depends(get_db),
):
    """
    获取字典项列表（分页）
    
    支持按字典ID、编码、选项值、标签、启用状态筛选
    """
    service = DictionaryService(db)
    
    params = DictItemQueryParams(
        pageNum=pageNum,
        pageSize=pageSize,
        dict_id=dict_id,
        dict_code=dict_code,
        item_value=item_value,
        item_label=item_label,
        is_enabled=is_enabled,
    )
    
    items, total = await service.get_item_list(params)
    
    return page_response(
        items=[DictItemResponse.model_validate(item).model_dump() for item in items],
        total=total,
        page_num=pageNum,
        page_size=pageSize,
    )


@router.get("/items/by-code/{dict_code}", summary="根据字典编码获取字典项")
async def get_items_by_code(
    dict_code: str,
    enabled_only: bool = Query(True, description="是否只返回启用的项"),
    db: AsyncSession = Depends(get_db),
):
    """
    根据字典编码获取所有字典项（用于下拉选项）
    
    返回格式：[{label: "显示标签", value: "选项值"}]
    """
    service = DictionaryService(db)
    items = await service.get_items_by_code(dict_code, enabled_only=enabled_only)
    
    return success(data=[item.model_dump() for item in items])


@router.get("/items/{item_id}", summary="获取字典项详情")
async def get_dict_item_detail(
    item_id: int,
    db: AsyncSession = Depends(get_db),
):
    """获取字典项详情"""
    service = DictionaryService(db)
    item = await service.get_item_by_id(item_id)
    
    return success(data=DictItemResponse.model_validate(item).model_dump())


@router.post("/items", summary="创建字典项")
async def create_dict_item(
    data: DictItemCreate,
    db: AsyncSession = Depends(get_db),
):
    """创建字典项"""
    service = DictionaryService(db)
    item = await service.create_item(data)
    await db.commit()
    
    return success(
        data=DictItemResponse.model_validate(item).model_dump(),
        msg="创建成功"
    )


@router.put("/items/{item_id}", summary="更新字典项")
async def update_dict_item(
    item_id: int,
    data: DictItemUpdate,
    db: AsyncSession = Depends(get_db),
):
    """更新字典项"""
    service = DictionaryService(db)
    item = await service.update_item(item_id, data)
    await db.commit()
    
    return success(
        data=DictItemResponse.model_validate(item).model_dump(),
        msg="更新成功"
    )


@router.delete("/items/{item_id}", summary="删除字典项")
async def delete_dict_item(
    item_id: int,
    db: AsyncSession = Depends(get_db),
):
    """删除字典项"""
    service = DictionaryService(db)
    await service.delete_item(item_id)
    await db.commit()
    
    return success(msg="删除成功")















