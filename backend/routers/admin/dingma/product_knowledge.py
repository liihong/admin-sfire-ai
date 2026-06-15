"""
顶妈产品知识库（配方）管理接口

运营可在后台维护产品配方、文案事实与别名，无需改 JSON 重跑 seed。
"""
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from core.deps import get_current_admin_user
from core.tenant_helpers import resolve_admin_agent_scope_tenant_id
from db import get_db
from models.admin_user import AdminUser
from schemas.dingma.product_knowledge import (
    ProductKnowledgeCreate,
    ProductKnowledgeQueryParams,
    ProductKnowledgeUpdate,
)
from services.dingma.product_knowledge_admin import DingmaProductKnowledgeAdminService
from utils.response import success, page_response, ResponseMsg

router = APIRouter()


async def _admin_scope_tid(db: AsyncSession, admin: AdminUser) -> Optional[int]:
    """与智能体、快捷入口一致：登录名纠偏 + 严格租户隔离"""
    return await resolve_admin_agent_scope_tenant_id(
        db,
        admin_tenant_id=admin.tenant_id,
        admin_username=admin.username,
    )


@router.get("", summary="获取产品知识库列表")
async def get_product_knowledge_list(
    pageNum: int = Query(1, ge=1, description="页码"),
    pageSize: int = Query(10, ge=1, le=200, description="每页数量"),
    category_code: Optional[str] = Query(None, description="品类编码筛选"),
    product_name: Optional[str] = Query(None, description="产品名称模糊搜索"),
    product_code: Optional[str] = Query(None, description="产品编码精确搜索"),
    status: Optional[int] = Query(None, ge=0, le=1, description="状态：1启用 0禁用"),
    keyword: Optional[str] = Query(None, description="关键词（产品名/编码/文案事实）"),
    db: AsyncSession = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin_user),
):
    """分页查询顶妈产品知识库；dingma 租户管理员仅本租户数据。"""
    service = DingmaProductKnowledgeAdminService(db)
    params = ProductKnowledgeQueryParams(
        pageNum=pageNum,
        pageSize=pageSize,
        category_code=category_code,
        product_name=product_name,
        product_code=product_code,
        status=status,
        keyword=keyword,
    )
    items, total = await service.get_list(
        params,
        scoped_tenant_id=await _admin_scope_tid(db, current_admin),
    )
    return page_response(
        items=items,
        total=total,
        page_num=pageNum,
        page_size=pageSize,
    )


@router.get("/categories", summary="获取品类列表")
async def get_product_knowledge_categories(
    db: AsyncSession = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin_user),
):
    """获取品类统计，用于筛选下拉。"""
    service = DingmaProductKnowledgeAdminService(db)
    categories = await service.get_categories(
        scoped_tenant_id=await _admin_scope_tid(db, current_admin),
    )
    return success(data=categories, msg="获取成功")


@router.get("/{item_id}", summary="获取产品知识库详情")
async def get_product_knowledge_detail(
    item_id: int,
    db: AsyncSession = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin_user),
):
    """获取单条产品知识库详情（含配方全字段）。"""
    service = DingmaProductKnowledgeAdminService(db)
    item = await service.get_detail(
        item_id,
        scoped_tenant_id=await _admin_scope_tid(db, current_admin),
    )
    return success(data=item, msg="获取成功")


@router.post("", summary="创建产品知识库")
async def create_product_knowledge(
    data: ProductKnowledgeCreate,
    db: AsyncSession = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin_user),
):
    """创建新产品知识库记录；product_code 租户内唯一。"""
    service = DingmaProductKnowledgeAdminService(db)
    item = await service.create_item(
        data,
        scoped_tenant_id=await _admin_scope_tid(db, current_admin),
    )
    await db.commit()
    return success(data=item, msg=ResponseMsg.CREATED)


@router.put("/{item_id}", summary="更新产品知识库")
async def update_product_knowledge(
    item_id: int,
    data: ProductKnowledgeUpdate,
    db: AsyncSession = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin_user),
):
    """更新产品知识库；支持编辑配方、文案事实、别名等全字段。"""
    service = DingmaProductKnowledgeAdminService(db)
    item = await service.update_item(
        item_id,
        data,
        scoped_tenant_id=await _admin_scope_tid(db, current_admin),
    )
    await db.commit()
    return success(data=item, msg=ResponseMsg.UPDATED)


@router.patch("/{item_id}/status", summary="更新启用状态")
async def update_product_knowledge_status(
    item_id: int,
    status: int = Query(..., ge=0, le=1, description="状态：1启用 0禁用"),
    db: AsyncSession = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin_user),
):
    """启用/禁用产品知识库记录。"""
    service = DingmaProductKnowledgeAdminService(db)
    item = await service.update_status(
        item_id,
        status,
        scoped_tenant_id=await _admin_scope_tid(db, current_admin),
    )
    await db.commit()
    return success(data=item, msg=ResponseMsg.UPDATED)


@router.delete("/{item_id}", summary="删除产品知识库")
async def delete_product_knowledge(
    item_id: int,
    db: AsyncSession = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin_user),
):
    """删除产品知识库记录。"""
    service = DingmaProductKnowledgeAdminService(db)
    await service.delete_item(
        item_id,
        scoped_tenant_id=await _admin_scope_tid(db, current_admin),
    )
    await db.commit()
    return success(msg=ResponseMsg.DELETED)
