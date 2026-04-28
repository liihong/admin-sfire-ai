"""租户管理（平台管理员） / 租户下拉（所有管理员）"""
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from db import get_db
from core.constants import admin_has_platform_privilege
from core.deps import get_current_admin_user, require_platform_admin
from models.admin_user import AdminUser
from schemas.tenant import TenantCreate, TenantUpdate, TenantQueryParams
from services.tenant_service import TenantService
from utils.response import success, page_response, ResponseMsg

router = APIRouter()


@router.get("/options", summary="租户下拉选项")
async def tenant_options(
    db: AsyncSession = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin_user),
):
    """
    用于新建用户等场景选择租户。
    平台管理员可选全部租户；租户管理员仅返回当前租户。
    注意：与「平台管理员」判定一致（见 admin_has_platform_privilege），
    勿仅用 tenant_id IS NULL，否则主租户 id 回填后会只看到一条。
    """
    svc = TenantService(db)
    if admin_has_platform_privilege(
        tenant_id=current_admin.tenant_id,
        role_id=current_admin.role_id,
    ):
        scoped: Optional[int] = None
    else:
        scoped = current_admin.tenant_id
    opts = await svc.list_options_for_admin(scoped_tenant_id=scoped)
    return success(data=opts)


@router.get("", summary="租户列表（分页）")
async def list_tenants(
    pageNum: int = Query(1, ge=1),
    pageSize: int = Query(10, ge=1, le=1000),
    code: Optional[str] = Query(None),
    name: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    _: AdminUser = Depends(require_platform_admin),
):
    svc = TenantService(db)
    params = TenantQueryParams(pageNum=pageNum, pageSize=pageSize, code=code, name=name)
    items, total = await svc.list_tenants(params)
    return page_response(items=items, total=total, page_num=pageNum, page_size=pageSize)


@router.get("/{tenant_id}", summary="租户详情")
async def get_tenant(
    tenant_id: int,
    db: AsyncSession = Depends(get_db),
    _: AdminUser = Depends(require_platform_admin),
):
    svc = TenantService(db)
    data = await svc.get_by_id(tenant_id)
    return success(data=data)


@router.post("", summary="创建租户")
async def create_tenant(
    body: TenantCreate,
    db: AsyncSession = Depends(get_db),
    _: AdminUser = Depends(require_platform_admin),
):
    svc = TenantService(db)
    data = await svc.create(body)
    return success(data=data, msg=ResponseMsg.CREATED)


@router.put("/{tenant_id}", summary="更新租户")
async def update_tenant(
    tenant_id: int,
    body: TenantUpdate,
    db: AsyncSession = Depends(get_db),
    _: AdminUser = Depends(require_platform_admin),
):
    svc = TenantService(db)
    data = await svc.update(tenant_id, body)
    return success(data=data, msg=ResponseMsg.UPDATED)
