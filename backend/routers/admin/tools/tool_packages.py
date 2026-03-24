"""
B 端工具包配置 CRUD
"""
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from db import get_db
from core.deps import get_current_user
from models.admin_user import AdminUser
from schemas.tool_package import (
    ToolPackageCreate,
    ToolPackageUpdate,
    ToolPackageQueryParams,
    ToolPackageSortRequest,
)
from services.tools.tool_package_service import ToolPackageService
from utils.response import success, page_response, ResponseMsg

router = APIRouter()


@router.put("/sort/batch", summary="批量调整排序")
async def sort_tool_packages(
    body: ToolPackageSortRequest,
    _: AdminUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    svc = ToolPackageService(db)
    await svc.update_sort([(x.id, x.sort_order) for x in body.items])
    return success(msg=ResponseMsg.UPDATED)


@router.get("", summary="工具包分页列表")
async def list_tool_packages(
    pageNum: int = Query(1, ge=1),
    pageSize: int = Query(10, ge=1, le=1000),
    status: Optional[int] = Query(None, ge=0, le=1),
    keyword: Optional[str] = Query(None),
    _: AdminUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    svc = ToolPackageService(db)
    params = ToolPackageQueryParams(
        pageNum=pageNum, pageSize=pageSize, status=status, keyword=keyword
    )
    items, total = await svc.list_page(params)
    return page_response(
        items=items, total=total, page_num=pageNum, page_size=pageSize
    )


@router.get("/{package_id}", summary="工具包详情")
async def get_tool_package(
    package_id: int,
    _: AdminUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    svc = ToolPackageService(db)
    data = await svc.get_detail(package_id)
    return success(data=data)


@router.post("", summary="创建工具包")
async def create_tool_package(
    body: ToolPackageCreate,
    _: AdminUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    svc = ToolPackageService(db)
    data = await svc.create(body)
    return success(data=data, msg=ResponseMsg.CREATED)


@router.put("/{package_id}", summary="更新工具包")
async def update_tool_package(
    package_id: int,
    body: ToolPackageUpdate,
    _: AdminUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    svc = ToolPackageService(db)
    data = await svc.update(package_id, body)
    return success(data=data, msg=ResponseMsg.UPDATED)


@router.delete("/{package_id}", summary="删除工具包")
async def delete_tool_package(
    package_id: int,
    _: AdminUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    svc = ToolPackageService(db)
    await svc.delete(package_id, hard_delete=True)
    return success(msg=ResponseMsg.DELETED)
