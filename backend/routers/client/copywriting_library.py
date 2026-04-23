"""
Client Copywriting Library Endpoints
C端文案库接口（小程序）

独立业务线：不依赖 inspirations / AI对话。
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from core.deps import get_current_miniprogram_user
from db import get_db
from models.user import User
from schemas.copywriting_library import (
    CopywritingEntryCreate,
    CopywritingEntryUpdate,
    CopywritingEntryQueryParams,
    CopywritingPublishDataUpdate,
    CopywritingEntryResponse,
)
from services.resource.copywriting_library import CopywritingLibraryService
from utils.response import success, page_response

router = APIRouter()


@router.post("", summary="保存文案到文案库")
async def create_entry(
    data: CopywritingEntryCreate,
    current_user: User = Depends(get_current_miniprogram_user),
    db: AsyncSession = Depends(get_db),
):
    """
    创建文案库条目。

    最小必填：content + project_id
    """
    service = CopywritingLibraryService(db)
    entry = await service.create_entry(user_id=current_user.id, data=data)
    return success(data=CopywritingEntryResponse.from_orm_with_project(entry).model_dump(), msg="保存成功")


@router.get("", summary="获取文案库列表")
async def list_entries(
    pageNum: int = Query(default=1, ge=1, description="页码"),
    pageSize: int = Query(default=10, ge=1, le=1000, description="每页数量"),
    project_id: int = Query(..., description="项目ID（必填）"),
    status: str | None = Query(default=None, description="状态筛选：draft/todo/published/archived"),
    tag: str | None = Query(default=None, description="标签筛选（单个标签）"),
    keyword: str | None = Query(default=None, description="关键词搜索"),
    sort_by: str | None = Query(default="created_at", description="排序字段：created_at/updated_at"),
    sort_order: str | None = Query(default="desc", description="排序方向：asc/desc"),
    current_user: User = Depends(get_current_miniprogram_user),
    db: AsyncSession = Depends(get_db),
):
    params = CopywritingEntryQueryParams(
        pageNum=pageNum,
        pageSize=pageSize,
        project_id=project_id,
        status=status,
        tag=tag,
        keyword=keyword,
        sort_by=sort_by,
        sort_order=sort_order,
    )

    service = CopywritingLibraryService(db)
    result = await service.list_entries(user_id=current_user.id, params=params)

    items = [CopywritingEntryResponse.from_orm_with_project(x).model_dump() for x in result.list]
    return page_response(
        items=items,
        total=result.total,
        page_num=result.pageNum,
        page_size=result.pageSize,
        msg="获取成功",
    )


@router.get("/{entry_id}", summary="获取文案库详情")
async def get_entry_detail(
    entry_id: int,
    current_user: User = Depends(get_current_miniprogram_user),
    db: AsyncSession = Depends(get_db),
):
    service = CopywritingLibraryService(db)
    entry = await service.get_entry_by_id(entry_id=entry_id, user_id=current_user.id)
    return success(data=CopywritingEntryResponse.from_orm_with_project(entry).model_dump(), msg="获取成功")


@router.put("/{entry_id}", summary="更新文案库条目")
async def update_entry(
    entry_id: int,
    data: CopywritingEntryUpdate,
    current_user: User = Depends(get_current_miniprogram_user),
    db: AsyncSession = Depends(get_db),
):
    service = CopywritingLibraryService(db)
    entry = await service.update_entry(entry_id=entry_id, user_id=current_user.id, data=data)
    return success(data=CopywritingEntryResponse.from_orm_with_project(entry).model_dump(), msg="更新成功")


@router.delete("/{entry_id}", summary="删除文案库条目")
async def delete_entry(
    entry_id: int,
    current_user: User = Depends(get_current_miniprogram_user),
    db: AsyncSession = Depends(get_db),
):
    service = CopywritingLibraryService(db)
    await service.delete_entry(entry_id=entry_id, user_id=current_user.id)
    return success(msg="删除成功")


@router.post("/{entry_id}/publish-data", summary="补录发布数据并标记为已发布")
async def update_publish_data(
    entry_id: int,
    data: CopywritingPublishDataUpdate,
    current_user: User = Depends(get_current_miniprogram_user),
    db: AsyncSession = Depends(get_db),
):
    service = CopywritingLibraryService(db)
    entry = await service.update_publish_data(entry_id=entry_id, user_id=current_user.id, data=data)
    return success(data=CopywritingEntryResponse.from_orm_with_project(entry).model_dump(), msg="保存成功")

