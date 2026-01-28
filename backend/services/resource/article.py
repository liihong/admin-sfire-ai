"""
文章 Service
文章管理服务层
"""
from typing import List, Tuple, Optional
from datetime import datetime
from sqlalchemy import select, func, and_, desc, asc
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from models.article import Article, ArticleCategory
from schemas.article import (
    ArticleCreate,
    ArticleUpdate,
    ArticleQueryParams,
    ArticleResponse,
)
from utils.exceptions import NotFoundException, BadRequestException
from services.base import BaseService


class ArticleService(BaseService):
    """文章管理服务类"""
    
    def __init__(self, db: AsyncSession):
        super().__init__(db, Article, "文章", check_soft_delete=False)
    
    def _format_response(self, article: Article) -> dict:
        """格式化文章响应"""
        # 处理标签：如果是字符串则解析为列表，如果是列表则直接使用
        tags = article.tags
        if isinstance(tags, str):
            import json
            try:
                tags = json.loads(tags)
            except:
                tags = []
        elif tags is None:
            tags = []
        
        return {
            "id": article.id,
            "category": article.category.value,
            "title": article.title,
            "content": article.content,
            "summary": article.summary,
            "cover_image": article.cover_image,
            "tags": tags if isinstance(tags, list) else [],
            "sort_order": article.sort_order,
            "publish_time": article.publish_time.isoformat() if article.publish_time else None,
            "view_count": article.view_count,
            "is_published": article.is_published,
            "is_enabled": article.is_enabled,
            "created_at": article.created_at.isoformat() if article.created_at else None,
            "updated_at": article.updated_at.isoformat() if article.updated_at else None,
        }
    
    async def get_articles(
        self,
        params: ArticleQueryParams,
        only_published: bool = False
    ) -> Tuple[List[dict], int]:
        """
        获取文章列表
        
        Args:
            params: 查询参数
            only_published: 是否只返回已发布的文章（用于小程序端）
        
        Returns:
            (文章列表, 总数量)
        """
        # 构建查询条件
        conditions = []
        
        if params.category:
            try:
                category_enum = ArticleCategory(params.category)
                conditions.append(Article.category == category_enum)
            except ValueError:
                # 无效的文章类型，记录日志但不抛出异常，返回空列表
                logger.warning(f"Invalid article category: {params.category}")
                return [], 0
        
        if params.title:
            conditions.append(Article.title.like(f"%{params.title}%"))
        
        if params.tag:
            # 标签筛选：JSON数组包含指定标签
            conditions.append(
                Article.tags.contains([params.tag])
            )
        
        if params.is_published is not None:
            conditions.append(Article.is_published == params.is_published)
        elif only_published:
            # 小程序端默认只返回已发布的
            conditions.append(Article.is_published == True)
        
        if params.is_enabled is not None:
            conditions.append(Article.is_enabled == params.is_enabled)
        elif only_published:
            # 小程序端默认只返回启用的
            conditions.append(Article.is_enabled == True)
        
        # 查询总数
        count_query = select(func.count(Article.id))
        if conditions:
            count_query = count_query.where(and_(*conditions))
        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0
        
        # 查询数据
        query = select(Article)
        if conditions:
            query = query.where(and_(*conditions))
        
        # 排序：已发布文章按发布时间倒序，未发布按创建时间倒序，相同时间按排序顺序
        query = query.order_by(
            desc(Article.publish_time),
            desc(Article.created_at),
            asc(Article.sort_order)
        )
        
        query = query.offset(params.offset).limit(params.pageSize)
        
        result = await self.db.execute(query)
        articles = result.scalars().all()
        
        # 格式化响应
        article_list = [self._format_response(article) for article in articles]
        
        return article_list, total
    
    async def get_article_by_id(
        self,
        article_id: int,
        increment_view: bool = False
    ) -> dict:
        """
        根据ID获取文章
        
        Args:
            article_id: 文章ID
            increment_view: 是否增加浏览量（小程序端查看详情时使用）
        
        Returns:
            文章信息
        """
        article = await super().get_by_id(article_id, error_msg="文章不存在")
        
        # 增加浏览量
        if increment_view:
            article.view_count += 1
            await self.db.flush()
            await self.db.refresh(article)
        
        return self._format_response(article)
    
    async def create_article(self, article_data: ArticleCreate) -> dict:
        """
        创建文章
        
        Args:
            article_data: 文章创建数据
        
        Returns:
            新文章信息
        """
        def before_create(article: Article, data: ArticleCreate):
            """创建前的钩子函数"""
            # 转换枚举类型
            if hasattr(data, "category") and data.category:
                article.category = ArticleCategory(data.category)
            
            # 处理标签：确保是列表格式
            if hasattr(data, "tags") and data.tags:
                if isinstance(data.tags, list):
                    article.tags = data.tags
                else:
                    article.tags = []
            else:
                article.tags = []
        
        article = await super().create(
            data=article_data,
            before_create=before_create,
        )
        
        await self.db.flush()
        await self.db.refresh(article)
        
        return self._format_response(article)
    
    async def update_article(self, article_id: int, article_data: ArticleUpdate) -> dict:
        """
        更新文章
        
        Args:
            article_id: 文章ID
            article_data: 文章更新数据
        
        Returns:
            更新后的文章信息
        """
        def before_update(article: Article, data: ArticleUpdate):
            """更新前的钩子函数"""
            # 处理枚举类型转换
            update_data = data.model_dump(exclude_unset=True)
            if "category" in update_data and update_data["category"] is not None:
                article.category = ArticleCategory(update_data["category"])
            
            # 处理标签
            if "tags" in update_data:
                tags = update_data["tags"]
                if isinstance(tags, list):
                    article.tags = tags
                elif tags is None:
                    article.tags = []
        
        article = await super().update(
            obj_id=article_id,
            data=article_data,
            before_update=before_update,
        )
        
        await self.db.flush()
        await self.db.refresh(article)
        
        return self._format_response(article)
    
    async def delete_article(self, article_id: int) -> None:
        """
        删除文章
        
        Args:
            article_id: 文章ID
        """
        await super().delete(article_id, hard_delete=True)
        await self.db.flush()
    
    async def update_article_status(
        self,
        article_id: int,
        is_published: Optional[bool] = None,
        is_enabled: Optional[bool] = None
    ) -> dict:
        """
        更新文章状态
        
        Args:
            article_id: 文章ID
            is_published: 是否已发布
            is_enabled: 是否启用
        
        Returns:
            更新后的文章信息
        """
        article = await super().get_by_id(article_id)
        
        if is_published is not None:
            article.is_published = is_published
        if is_enabled is not None:
            article.is_enabled = is_enabled
        
        await self.db.flush()
        await self.db.refresh(article)
        
        return self._format_response(article)

