"""
文章管理 Endpoints
文章管理相关接口（管理后台）
"""
from typing import Optional
from fastapi import APIRouter, Depends, Query, Body
from sqlalchemy.ext.asyncio import AsyncSession

from db import get_db
from core.deps import get_current_admin_user
from core.tenant_helpers import resolve_admin_agent_scope_tenant_id
from models.admin_user import AdminUser
from schemas.article import (
    ArticleCategoryCode,
    ArticleCreate,
    ArticleUpdate,
    ArticleQueryParams,
    ArticleStatusRequest,
)
from services.resource import ArticleService
from utils.response import success, page_response, ResponseMsg

router = APIRouter()


async def _admin_scope_tid(db: AsyncSession, admin: AdminUser) -> Optional[int]:
    """与智能体、小程序用户一致：登录名纠偏 + 严格租户隔离"""
    return await resolve_admin_agent_scope_tenant_id(
        db,
        admin_tenant_id=admin.tenant_id,
        admin_username=admin.username,
    )


@router.get("", summary="获取文章列表")
async def get_articles(
    pageNum: int = Query(1, ge=1, description="页码"),
    pageSize: int = Query(10, ge=1, le=1000, description="每页数量"),
    category: Optional[ArticleCategoryCode] = Query(
        None,
        description="文章类型筛选（sys_dict article_category 的 item_value：01-04）",
    ),
    title: Optional[str] = Query(None, description="标题（模糊搜索）"),
    tag: Optional[str] = Query(None, description="标签筛选"),
    is_published: Optional[bool] = Query(None, description="是否已发布"),
    is_enabled: Optional[bool] = Query(None, description="是否启用"),
    db: AsyncSession = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin_user),
):
    """
    获取文章列表（分页）
    
    支持按类型、标题、标签、发布状态、启用状态筛选；租户管理员仅本租户数据。
    """
    article_service = ArticleService(db)
    scope_tid = await _admin_scope_tid(db, current_admin)

    params = ArticleQueryParams(
        pageNum=pageNum,
        pageSize=pageSize,
        category=category,
        title=title,
        tag=tag,
        is_published=is_published,
        is_enabled=is_enabled,
    )

    articles, total = await article_service.get_articles(
        params, scoped_tenant_id=scope_tid
    )

    return page_response(
        items=articles,
        total=total,
        page_num=pageNum,
        page_size=pageSize,
    )


@router.get("/{article_id}", summary="获取文章详情")
async def get_article(
    article_id: int,
    db: AsyncSession = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin_user),
):
    """获取文章详情"""
    article_service = ArticleService(db)
    article = await article_service.get_article_by_id(
        article_id, scoped_tenant_id=await _admin_scope_tid(db, current_admin)
    )
    return success(data=article)


@router.post("", summary="创建文章")
async def create_article(
    article_data: ArticleCreate,
    db: AsyncSession = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin_user),
):
    """创建新文章"""
    article_service = ArticleService(db)
    article = await article_service.create_article(
        article_data,
        scoped_tenant_id=await _admin_scope_tid(db, current_admin),
    )
    return success(data=article, msg=ResponseMsg.CREATED)


@router.put("/{article_id}", summary="更新文章")
async def update_article(
    article_id: int,
    article_data: ArticleUpdate,
    db: AsyncSession = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin_user),
):
    """更新文章信息"""
    article_service = ArticleService(db)
    article = await article_service.update_article(
        article_id,
        article_data,
        scoped_tenant_id=await _admin_scope_tid(db, current_admin),
    )
    return success(data=article, msg=ResponseMsg.UPDATED)


@router.delete("/{article_id}", summary="删除文章")
async def delete_article(
    article_id: int,
    db: AsyncSession = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin_user),
):
    """删除文章"""
    article_service = ArticleService(db)
    await article_service.delete_article(
        article_id, scoped_tenant_id=await _admin_scope_tid(db, current_admin)
    )
    return success(msg=ResponseMsg.DELETED)


@router.put("/{article_id}/status", summary="更新文章状态")
async def update_article_status(
    article_id: int,
    request: ArticleStatusRequest,
    db: AsyncSession = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin_user),
):
    """更新文章发布状态或启用状态"""
    article_service = ArticleService(db)
    article = await article_service.update_article_status(
        article_id,
        is_published=request.is_published,
        is_enabled=request.is_enabled,
        scoped_tenant_id=await _admin_scope_tid(db, current_admin),
    )
    return success(data=article, msg=ResponseMsg.UPDATED)
