"""
顶妈知识库 v2 管理接口

- /skus：成品 SKU
- /components：组件/子配方
"""
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from core.deps import get_current_admin_user
from core.tenant_helpers import resolve_admin_agent_scope_tenant_id
from db import get_db
from models.admin_user import AdminUser
from schemas.dingma.knowledge import (
    ComponentCreate,
    ComponentQueryParams,
    ComponentUpdate,
    SkuCreate,
    SkuQueryParams,
    SkuUpdate,
)
from services.dingma.knowledge_admin import DingmaKnowledgeAdminService
from utils.response import success, page_response, ResponseMsg

router = APIRouter()


async def _admin_scope_tid(db: AsyncSession, admin: AdminUser) -> Optional[int]:
    return await resolve_admin_agent_scope_tenant_id(
        db,
        admin_tenant_id=admin.tenant_id,
        admin_username=admin.username,
    )


# ---------- SKU ----------

@router.get("/skus", summary="获取成品 SKU 列表")
async def get_sku_list(
    pageNum: int = Query(1, ge=1),
    pageSize: int = Query(10, ge=1, le=200),
    category_code: Optional[str] = Query(None),
    status: Optional[int] = Query(None, ge=0, le=1),
    keyword: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin_user),
):
    service = DingmaKnowledgeAdminService(db)
    params = SkuQueryParams(
        pageNum=pageNum,
        pageSize=pageSize,
        category_code=category_code,
        status=status,
        keyword=keyword,
    )
    items, total = await service.get_sku_list(
        params, scoped_tenant_id=await _admin_scope_tid(db, current_admin)
    )
    return page_response(items=items, total=total, page_num=pageNum, page_size=pageSize)


@router.get("/skus/categories", summary="获取 SKU 品类统计")
async def get_sku_categories(
    db: AsyncSession = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin_user),
):
    service = DingmaKnowledgeAdminService(db)
    categories = await service.get_sku_categories(
        scoped_tenant_id=await _admin_scope_tid(db, current_admin)
    )
    return success(data=categories, msg="获取成功")


@router.get("/skus/{item_id}", summary="获取 SKU 详情")
async def get_sku_detail(
    item_id: int,
    db: AsyncSession = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin_user),
):
    service = DingmaKnowledgeAdminService(db)
    item = await service.get_sku_detail(item_id, scoped_tenant_id=await _admin_scope_tid(db, current_admin))
    return success(data=item, msg="获取成功")


@router.post("/skus", summary="创建 SKU")
async def create_sku(
    data: SkuCreate,
    db: AsyncSession = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin_user),
):
    service = DingmaKnowledgeAdminService(db)
    item = await service.create_sku(data, scoped_tenant_id=await _admin_scope_tid(db, current_admin))
    await db.commit()
    return success(data=item, msg=ResponseMsg.CREATED)


@router.put("/skus/{item_id}", summary="更新 SKU")
async def update_sku(
    item_id: int,
    data: SkuUpdate,
    db: AsyncSession = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin_user),
):
    service = DingmaKnowledgeAdminService(db)
    item = await service.update_sku(item_id, data, scoped_tenant_id=await _admin_scope_tid(db, current_admin))
    await db.commit()
    return success(data=item, msg=ResponseMsg.UPDATED)


@router.patch("/skus/{item_id}/status", summary="更新 SKU 状态")
async def update_sku_status(
    item_id: int,
    status: int = Query(..., ge=0, le=1),
    db: AsyncSession = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin_user),
):
    service = DingmaKnowledgeAdminService(db)
    item = await service.update_sku_status(
        item_id, status, scoped_tenant_id=await _admin_scope_tid(db, current_admin)
    )
    await db.commit()
    return success(data=item, msg=ResponseMsg.UPDATED)


@router.delete("/skus/{item_id}", summary="删除 SKU")
async def delete_sku(
    item_id: int,
    db: AsyncSession = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin_user),
):
    service = DingmaKnowledgeAdminService(db)
    await service.delete_sku(item_id, scoped_tenant_id=await _admin_scope_tid(db, current_admin))
    await db.commit()
    return success(msg=ResponseMsg.DELETED)


# ---------- Component ----------

@router.get("/components/options", summary="组件下拉选项")
async def get_component_options(
    db: AsyncSession = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin_user),
):
    service = DingmaKnowledgeAdminService(db)
    options = await service.list_component_options(
        scoped_tenant_id=await _admin_scope_tid(db, current_admin)
    )
    return success(data=options, msg="获取成功")


@router.get("/components", summary="获取组件列表")
async def get_component_list(
    pageNum: int = Query(1, ge=1),
    pageSize: int = Query(10, ge=1, le=200),
    component_type: Optional[str] = Query(None),
    status: Optional[int] = Query(None, ge=0, le=1),
    keyword: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin_user),
):
    service = DingmaKnowledgeAdminService(db)
    params = ComponentQueryParams(
        pageNum=pageNum,
        pageSize=pageSize,
        component_type=component_type,
        status=status,
        keyword=keyword,
    )
    items, total = await service.get_component_list(
        params, scoped_tenant_id=await _admin_scope_tid(db, current_admin)
    )
    return page_response(items=items, total=total, page_num=pageNum, page_size=pageSize)


@router.get("/components/{item_id}", summary="获取组件详情")
async def get_component_detail(
    item_id: int,
    db: AsyncSession = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin_user),
):
    service = DingmaKnowledgeAdminService(db)
    item = await service.get_component_detail(
        item_id, scoped_tenant_id=await _admin_scope_tid(db, current_admin)
    )
    return success(data=item, msg="获取成功")


@router.post("/components", summary="创建组件")
async def create_component(
    data: ComponentCreate,
    db: AsyncSession = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin_user),
):
    service = DingmaKnowledgeAdminService(db)
    item = await service.create_component(
        data, scoped_tenant_id=await _admin_scope_tid(db, current_admin)
    )
    await db.commit()
    return success(data=item, msg=ResponseMsg.CREATED)


@router.put("/components/{item_id}", summary="更新组件")
async def update_component(
    item_id: int,
    data: ComponentUpdate,
    db: AsyncSession = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin_user),
):
    service = DingmaKnowledgeAdminService(db)
    item = await service.update_component(
        item_id, data, scoped_tenant_id=await _admin_scope_tid(db, current_admin)
    )
    await db.commit()
    return success(data=item, msg=ResponseMsg.UPDATED)


@router.patch("/components/{item_id}/status", summary="更新组件状态")
async def update_component_status(
    item_id: int,
    status: int = Query(..., ge=0, le=1),
    db: AsyncSession = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin_user),
):
    service = DingmaKnowledgeAdminService(db)
    item = await service.update_component_status(
        item_id, status, scoped_tenant_id=await _admin_scope_tid(db, current_admin)
    )
    await db.commit()
    return success(data=item, msg=ResponseMsg.UPDATED)


@router.delete("/components/{item_id}", summary="删除组件")
async def delete_component(
    item_id: int,
    db: AsyncSession = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin_user),
):
    service = DingmaKnowledgeAdminService(db)
    await service.delete_component(item_id, scoped_tenant_id=await _admin_scope_tid(db, current_admin))
    await db.commit()
    return success(msg=ResponseMsg.DELETED)
