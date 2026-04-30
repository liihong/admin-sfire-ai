"""
文章 Endpoints
文章相关接口（小程序端）
"""
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from db import get_db
from core.client_public_scope import resolve_optional_public_tenant_id
from schemas.article import ArticleCategoryCode, ArticleQueryParams
from services.resource import ArticleService
from utils.response import success, page_response, fail

router = APIRouter()


@router.get("", summary="获取文章列表")
async def get_articles(
    pageNum: int = Query(1, ge=1, description="页码"),
    pageSize: int = Query(10, ge=1, le=100, description="每页数量"),
    category: Optional[ArticleCategoryCode] = Query(
        None,
        description=(
            "按文章类型筛选（sys_dict article_category 的 item_value）。"
            "示例：GET /api/v1/client/articles?category=01&pageNum=1"
        ),
    ),
    scoped_tenant_id: Optional[int] = Depends(resolve_optional_public_tenant_id),
    db: AsyncSession = Depends(get_db),
):
    """
    获取文章列表（小程序端）

    只返回已发布且启用的文章；传 `category` 时只返回该类型。

    说明：`GET /api/v1/client/articles/{id}` 为单篇详情，不支持 category 筛选；
    列表筛选请使用本接口查询参数 `category`（01-商业底牌 02-流量心法 03-实操手册 04-创始人说 05-最近落地）。
    """
    try:
        article_service = ArticleService(db)
        
        params = ArticleQueryParams(
            pageNum=pageNum,
            pageSize=pageSize,
            category=category,
        )
        
        articles, total = await article_service.get_articles(
            params,
            only_published=True,
            scoped_tenant_id=scoped_tenant_id,
        )
        
        return page_response(
            items=articles,
            total=total,
            page_num=pageNum,
            page_size=pageSize,
        )
    except Exception as e:
        logger.error(f"获取文章列表失败: {str(e)}", exc_info=True)
        return fail(msg=f"获取文章列表失败: {str(e)}", code=500)


@router.get("/{article_id}", summary="获取文章详情")
async def get_article_detail(
    article_id: int,
    scoped_tenant_id: Optional[int] = Depends(resolve_optional_public_tenant_id),
    db: AsyncSession = Depends(get_db),
):
    """
    获取文章详情（小程序端）
    
    自动增加浏览量
    """
    article_service = ArticleService(db)
    article = await article_service.get_article_by_id(
        article_id,
        increment_view=True,
        scoped_tenant_id=scoped_tenant_id,
    )
    return success(data=article, msg="获取成功")

