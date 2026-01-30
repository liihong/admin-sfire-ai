"""
Inspiration Service - 灵感数据持久化服务

提供灵感的CRUD操作、搜索、标签筛选等功能
"""
import json
import hashlib
from datetime import datetime
from typing import Optional, List, Tuple, Dict, Any
from sqlalchemy import select, func, and_, desc, asc, text, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from loguru import logger

from models.inspiration import Inspiration, InspirationStatus
from schemas.inspiration import (
    InspirationCreate,
    InspirationUpdate,
    InspirationQueryParams,
    InspirationResponse,
)
from utils.exceptions import NotFoundException, BadRequestException
from utils.pagination import PageResult
from services.base import BaseService
from db.redis import RedisCache


class InspirationService(BaseService):
    """灵感管理服务类"""
    
    def __init__(self, db: AsyncSession):
        super().__init__(db, Inspiration, "灵感", check_soft_delete=False)
    
    async def create_inspiration(
        self,
        user_id: int,
        data: InspirationCreate
    ) -> Inspiration:
        """
        创建灵感
        
        Args:
            user_id: 用户ID
            data: 创建数据
        
        Returns:
            创建的灵感对象
        """
        # 验证内容长度
        if len(data.content) > 500:
            raise BadRequestException("灵感内容不能超过500字符")
        
        # 创建灵感对象
        inspiration_data = {
            "user_id": user_id,
            "content": data.content.strip(),
            "tags": data.tags or [],
            "project_id": data.project_id,
            "status": InspirationStatus.ACTIVE.value,
        }
        
        inspiration = Inspiration(**inspiration_data)
        self.db.add(inspiration)
        await self.db.flush()
        
        # 刷新以获取生成的ID和时间戳
        await self.db.refresh(inspiration)
        
        # 清除相关缓存
        await RedisCache.delete_pattern(f"inspiration:list:*")
        
        logger.info(f"灵感创建成功: ID={inspiration.id}, user_id={user_id}")
        return inspiration
    
    async def get_inspiration_by_id(
        self,
        inspiration_id: int,
        user_id: Optional[int] = None
    ) -> Inspiration:
        """
        根据ID获取灵感
        
        Args:
            inspiration_id: 灵感ID
            user_id: 可选的用户ID（用于权限验证）
        
        Returns:
            灵感对象
        
        Raises:
            NotFoundException: 灵感不存在时抛出
        """
        query = select(Inspiration).where(Inspiration.id == inspiration_id)
        
        # 排除已删除的灵感
        query = query.where(Inspiration.status != InspirationStatus.DELETED.value)
        
        # 如果提供了user_id，验证权限
        if user_id:
            query = query.where(Inspiration.user_id == user_id)
        
        # 预加载关联对象
        query = query.options(selectinload(Inspiration.project))
        
        result = await self.db.execute(query)
        inspiration = result.scalar_one_or_none()
        
        if not inspiration:
            raise NotFoundException("灵感不存在")
        
        return inspiration
    
    async def update_inspiration(
        self,
        inspiration_id: int,
        user_id: int,
        data: InspirationUpdate
    ) -> Inspiration:
        """
        更新灵感
        
        Args:
            inspiration_id: 灵感ID
            user_id: 用户ID（用于权限验证）
            data: 更新数据
        
        Returns:
            更新后的灵感对象
        """
        # 获取灵感并验证权限
        inspiration = await self.get_inspiration_by_id(inspiration_id, user_id)
        
        # 验证内容长度
        if data.content and len(data.content) > 500:
            raise BadRequestException("灵感内容不能超过500字符")
        
        # 更新字段
        if data.content is not None:
            inspiration.content = data.content.strip()
        if data.tags is not None:
            inspiration.set_tags_list(data.tags)
        if data.project_id is not None:
            inspiration.project_id = data.project_id
        if data.status is not None:
            if data.status not in [s.value for s in InspirationStatus]:
                raise BadRequestException(f"无效的状态值: {data.status}")
            inspiration.status = data.status
        
        await self.db.flush()
        await self.db.refresh(inspiration)
        
        # 清除相关缓存
        await RedisCache.delete_pattern(f"inspiration:list:*")
        
        logger.info(f"灵感更新成功: ID={inspiration_id}")
        return inspiration
    
    async def delete_inspiration(
        self,
        inspiration_id: int,
        user_id: int
    ) -> None:
        """
        删除灵感（软删除）
        
        Args:
            inspiration_id: 灵感ID
            user_id: 用户ID（用于权限验证）
        """
        inspiration = await self.get_inspiration_by_id(inspiration_id, user_id)
        inspiration.status = InspirationStatus.DELETED.value
        await self.db.flush()
        
        # 清除相关缓存
        await RedisCache.delete_pattern(f"inspiration:list:*")
        
        logger.info(f"灵感删除成功: ID={inspiration_id}")
    
    async def pin_inspiration(
        self,
        inspiration_id: int,
        user_id: int,
        is_pinned: bool
    ) -> Inspiration:
        """
        置顶/取消置顶灵感
        
        Args:
            inspiration_id: 灵感ID
            user_id: 用户ID（用于权限验证）
            is_pinned: 是否置顶
        
        Returns:
            更新后的灵感对象
        """
        inspiration = await self.get_inspiration_by_id(inspiration_id, user_id)
        inspiration.is_pinned = is_pinned
        await self.db.flush()
        await self.db.refresh(inspiration)
        
        logger.info(f"灵感置顶状态更新: ID={inspiration_id}, is_pinned={is_pinned}")
        return inspiration
    
    async def archive_inspiration(
        self,
        inspiration_id: int,
        user_id: int,
        status: str
    ) -> Inspiration:
        """
        归档/取消归档灵感
        
        Args:
            inspiration_id: 灵感ID
            user_id: 用户ID（用于权限验证）
            status: 状态（active/archived）
        
        Returns:
            更新后的灵感对象
        """
        if status not in [InspirationStatus.ACTIVE.value, InspirationStatus.ARCHIVED.value]:
            raise BadRequestException(f"无效的状态值: {status}")
        
        inspiration = await self.get_inspiration_by_id(inspiration_id, user_id)
        inspiration.status = status
        await self.db.flush()
        await self.db.refresh(inspiration)
        
        logger.info(f"灵感归档状态更新: ID={inspiration_id}, status={status}")
        return inspiration
    
    async def get_inspiration_list(
        self,
        user_id: int,
        params: InspirationQueryParams
    ) -> PageResult[Inspiration]:
        """
        获取灵感列表（支持分页、筛选、搜索、排序）
        
        Args:
            user_id: 用户ID
            params: 查询参数
        
        Returns:
            分页结果
        """
        # 构建基础查询条件
        conditions = [
            Inspiration.user_id == user_id,
            Inspiration.status != InspirationStatus.DELETED.value,  # 排除已删除的
        ]
        
        # 状态筛选
        if params.status:
            if params.status == "active":
                conditions.append(Inspiration.status == InspirationStatus.ACTIVE.value)
            elif params.status == "archived":
                conditions.append(Inspiration.status == InspirationStatus.ARCHIVED.value)
            # deleted状态不返回，已在基础条件中排除
        
        # 项目筛选
        if params.project_id:
            conditions.append(Inspiration.project_id == params.project_id)
        
        # 标签筛选（JSON字段查询）
        if params.tag:
            tag_json = json.dumps([params.tag])
            conditions.append(
                text("JSON_CONTAINS(inspirations.tags, :tag)")
            )
        
        # 关键词搜索（全文索引或LIKE查询）
        if params.keyword:
            keyword = params.keyword.strip()
            if keyword:
                # 优先使用全文索引（如果可用）
                # 注意：MySQL全文索引需要至少4个字符，否则使用LIKE查询
                if len(keyword) >= 4:
                    conditions.append(
                        text("MATCH(inspirations.content) AGAINST(:keyword IN NATURAL LANGUAGE MODE)")
                    )
                else:
                    conditions.append(Inspiration.content.like(f"%{keyword}%"))
        
        # 置顶筛选
        if params.is_pinned is not None:
            conditions.append(Inspiration.is_pinned == params.is_pinned)
        
        # 构建查询
        query = select(Inspiration).where(and_(*conditions))
        
        # 预加载关联对象
        query = query.options(selectinload(Inspiration.project))
        
        # 排序
        if params.sort_by == "pinned":
            # 置顶优先排序
            query = query.order_by(
                desc(Inspiration.is_pinned),
                desc(Inspiration.created_at)
            )
        else:
            # 默认按创建时间排序
            order_func = desc if params.sort_order == "desc" else asc
            query = query.order_by(order_func(Inspiration.created_at))
        
        # 生成缓存键（基于查询参数）
        cache_key = self._generate_cache_key(user_id, params)
        
        # 尝试从缓存获取
        cached_result = await RedisCache.get_json(cache_key)
        if cached_result:
            logger.debug(f"灵感列表缓存命中: user_id={user_id}")
            return PageResult(
                list=[Inspiration(**item) for item in cached_result.get("items", [])],
                total=cached_result.get("total", 0),
                pageNum=params.pageNum,
                pageSize=params.pageSize
            )
        
        # 查询总数（添加超时设置）
        count_query = select(func.count(Inspiration.id)).where(and_(*conditions))
        
        # 绑定参数（如果使用了text()）
        count_params = {}
        if params.tag:
            count_params['tag'] = tag_json
        if params.keyword and len(params.keyword.strip()) >= 4:
            count_params['keyword'] = params.keyword.strip()
        
        if count_params:
            count_query = count_query.params(**count_params)
        
        # 添加查询超时（5秒）
        count_query = count_query.execution_options(timeout=5)
        
        try:
            total_result = await self.db.execute(count_query)
            total = total_result.scalar() or 0
        except Exception as e:
            logger.error(f"查询总数超时或失败: {e}")
            total = 0
        
        # 分页查询（添加超时设置）
        query = query.offset(params.offset).limit(params.pageSize)
        
        # 绑定参数（如果使用了text()）
        query_params = {}
        if params.tag:
            query_params['tag'] = tag_json
        if params.keyword and len(params.keyword.strip()) >= 4:
            query_params['keyword'] = params.keyword.strip()
        
        if query_params:
            query = query.params(**query_params)
        
        # 添加查询超时（5秒）
        query = query.execution_options(timeout=5)
        
        try:
            result = await self.db.execute(query)
            items = result.scalars().all()
        except Exception as e:
            logger.error(f"查询列表超时或失败: {e}")
            items = []
        
        # 构建返回结果
        page_result = PageResult(
            list=items,
            total=total,
            pageNum=params.pageNum,
            pageSize=params.pageSize
        )
        
        # 缓存结果（5分钟）
        if items:
            cache_data = {
                "items": [self._inspiration_to_dict(item) for item in items],
                "total": total
            }
            await RedisCache.set_json(cache_key, cache_data, expire=300)
        
        return page_result
    
    def _generate_cache_key(self, user_id: int, params: InspirationQueryParams) -> str:
        """生成缓存键"""
        # 构建参数字符串
        params_str = f"{user_id}_{params.pageNum}_{params.pageSize}_{params.status or ''}_{params.project_id or ''}_{params.tag or ''}_{params.keyword or ''}_{params.is_pinned or ''}_{params.sort_by or ''}_{params.sort_order or ''}"
        # 使用MD5生成短键名
        key_hash = hashlib.md5(params_str.encode()).hexdigest()
        return f"inspiration:list:{key_hash}"
    
    def _inspiration_to_dict(self, inspiration: Inspiration) -> Dict[str, Any]:
        """将Inspiration对象转换为字典（用于缓存）"""
        return {
            "id": inspiration.id,
            "user_id": inspiration.user_id,
            "project_id": inspiration.project_id,
            "content": inspiration.content,
            "tags": inspiration.tags,
            "status": inspiration.status,
            "is_pinned": inspiration.is_pinned,
            "generated_content": inspiration.generated_content,
            "created_at": inspiration.created_at.isoformat() if inspiration.created_at else None,
            "updated_at": inspiration.updated_at.isoformat() if inspiration.updated_at else None,
        }
    
    async def update_generated_content(
        self,
        inspiration_id: int,
        user_id: int,
        generated_content: str,
        generated_at: Optional[datetime] = None
    ) -> Inspiration:
        """
        更新生成的内容
        
        Args:
            inspiration_id: 灵感ID
            user_id: 用户ID（用于权限验证）
            generated_content: 生成的内容
            generated_at: 生成时间（可选，默认当前时间）
        
        Returns:
            更新后的灵感对象
        """
        inspiration = await self.get_inspiration_by_id(inspiration_id, user_id)
        inspiration.generated_content = generated_content
        inspiration.generated_at = generated_at or datetime.now()
        await self.db.flush()
        await self.db.refresh(inspiration)
        
        logger.info(f"灵感生成内容更新: ID={inspiration_id}")
        return inspiration
    
    def _format_response(self, obj: Inspiration) -> Dict[str, Any]:
        """
        格式化响应数据
        
        Args:
            obj: 灵感对象
        
        Returns:
            格式化后的字典
        """
        return {
            "id": obj.id,
            "user_id": obj.user_id,
            "project_id": obj.project_id,
            "content": obj.content,
            "tags": obj.get_tags_list(),
            "status": obj.status,
            "is_pinned": obj.is_pinned,
            "generated_content": obj.generated_content,
            "generated_at": obj.generated_at.isoformat() if obj.generated_at else None,
            "created_at": obj.created_at.isoformat() if obj.created_at else None,
            "updated_at": obj.updated_at.isoformat() if obj.updated_at else None,
            "project_name": obj.project.name if obj.project else None,
        }

