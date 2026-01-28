"""
文章 Endpoints
文章相关接口（小程序端）
"""
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from db import get_db
from schemas.article import ArticleQueryParams
from services.resource import ArticleService
from utils.response import success, page_response, fail

router = APIRouter()


@router.get("", summary="获取文章列表")
async def get_articles(
    pageNum: int = Query(1, ge=1, description="页码"),
    pageSize: int = Query(10, ge=1, le=100, description="每页数量"),
    category: Optional[str] = Query(None, description="文章类型筛选: founder_story, operation_article, customer_case"),
    db: AsyncSession = Depends(get_db),
):
    """
    获取文章列表（小程序端）
    
    只返回已发布且启用的文章
    支持按类型筛选
    """
    try:
        article_service = ArticleService(db)
        
        params = ArticleQueryParams(
            pageNum=pageNum,
            pageSize=pageSize,
            category=category,
        )
        
        articles, total = await article_service.get_articles(params, only_published=True)
        
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
    db: AsyncSession = Depends(get_db),
):
    """
    获取文章详情（小程序端）
    
    自动增加浏览量
    """
    article_service = ArticleService(db)
    article = await article_service.get_article_by_id(article_id, increment_view=True)
    return success(data=article, msg="获取成功")

