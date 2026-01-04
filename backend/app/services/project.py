"""
Project Service - 项目数据持久化服务

使用 SQLAlchemy 异步操作和 Redis 存储活跃项目
"""
import json
import random
from typing import Optional, List
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from loguru import logger

from app.models.project import Project
from app.models.user import User
from app.schemas.project import (
    ProjectCreate,
    ProjectUpdate,
    PersonaSettings,
)
from app.db.redis import RedisCache
from app.utils.exceptions import (
    NotFoundException,
    BadRequestException,
)


class ProjectService:
    """项目管理服务类"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_projects_by_user(
        self,
        user_id: int,
        include_deleted: bool = False
    ) -> List[Project]:
        """
        获取用户的所有项目，按更新时间倒序
        
        Args:
            user_id: 用户ID
            include_deleted: 是否包含已删除的项目
        
        Returns:
            项目列表
        """
        query = select(Project).where(Project.user_id == user_id)
        
        if not include_deleted:
            query = query.where(Project.is_deleted == False)
        
        query = query.order_by(desc(Project.updated_at))
        
        result = await self.db.execute(query)
        projects = result.scalars().all()
        
        return list(projects)
    
    async def get_project_by_id(
        self,
        project_id: int,
        user_id: Optional[int] = None,
        include_deleted: bool = False
    ) -> Optional[Project]:
        """
        根据 ID 获取项目
        
        Args:
            project_id: 项目ID
            user_id: 可选的用户ID（用于权限验证）
            include_deleted: 是否包含已删除的项目
        
        Returns:
            项目对象，如果不存在则返回 None
        """
        query = select(Project).where(Project.id == project_id)
        
        if user_id is not None:
            query = query.where(Project.user_id == user_id)
        
        if not include_deleted:
            query = query.where(Project.is_deleted == False)
        
        result = await self.db.execute(query)
        project = result.scalar_one_or_none()
        
        return project
    
    async def create_project(
        self,
        user_id: int,
        data: ProjectCreate
    ) -> Project:
        """
        创建新项目
        
        Args:
            user_id: 用户ID
            data: 项目创建数据
        
        Returns:
            创建的项目对象
        """
        # 提取首字母作为头像显示
        avatar_letter = data.name[0].upper() if data.name else 'P'
        
        # 随机选择一个颜色（科技蓝色系）
        colors = ['#3B82F6', '#6366F1', '#8B5CF6', '#0EA5E9', '#14B8A6', '#F97316']
        avatar_color = data.avatar_color or random.choice(colors)
        
        # 处理人设配置
        persona_settings = {}
        if data.persona_settings:
            persona_settings = data.persona_settings.model_dump()
        
        project = Project(
            user_id=user_id,
            name=data.name,
            industry=data.industry or "通用",
            avatar_letter=avatar_letter,
            avatar_color=avatar_color,
            persona_settings=persona_settings,
        )
        
        self.db.add(project)
        await self.db.flush()
        await self.db.refresh(project)
        
        logger.info(f"Created project {project.id} for user {user_id}")
        
        return project
    
    async def update_project(
        self,
        project_id: int,
        user_id: int,
        data: ProjectUpdate
    ) -> Project:
        """
        更新项目
        
        Args:
            project_id: 项目ID
            user_id: 用户ID（用于权限验证）
            data: 项目更新数据
        
        Returns:
            更新后的项目对象
        
        Raises:
            NotFoundException: 项目不存在或无权访问
        """
        project = await self.get_project_by_id(project_id, user_id=user_id)
        if not project:
            raise NotFoundException("项目不存在或无权访问")
        
        # 更新字段
        if data.name is not None:
            project.name = data.name
            project.avatar_letter = data.name[0].upper() if data.name else 'P'
        
        if data.industry is not None:
            project.industry = data.industry
        
        if data.persona_settings is not None:
            project.persona_settings = data.persona_settings.model_dump()
        
        await self.db.flush()
        await self.db.refresh(project)
        
        logger.info(f"Updated project {project_id} for user {user_id}")
        
        return project
    
    async def delete_project(
        self,
        project_id: int,
        user_id: int
    ) -> bool:
        """
        删除项目（软删除）
        
        Args:
            project_id: 项目ID
            user_id: 用户ID（用于权限验证）
        
        Returns:
            是否删除成功
        
        Raises:
            NotFoundException: 项目不存在或无权访问
        """
        project = await self.get_project_by_id(project_id, user_id=user_id)
        if not project:
            raise NotFoundException("项目不存在或无权访问")
        
        project.is_deleted = True
        await self.db.flush()
        
        # 如果删除的是活跃项目，清除活跃项目缓存
        active_id = await self.get_active_project(user_id)
        if active_id == project_id:
            await self.set_active_project(user_id, None)
        
        logger.info(f"Deleted project {project_id} for user {user_id}")
        
        return True
    
    async def get_active_project(self, user_id: int) -> Optional[int]:
        """
        获取用户当前激活的项目ID
        
        Args:
            user_id: 用户ID
        
        Returns:
            项目ID，如果没有激活的项目则返回 None
        """
        key = f"user:{user_id}:active_project"
        project_id_str = await RedisCache.get(key)
        
        if project_id_str:
            try:
                return int(project_id_str)
            except (ValueError, TypeError):
                return None
        
        return None
    
    async def set_active_project(
        self,
        user_id: int,
        project_id: Optional[int]
    ) -> bool:
        """
        设置用户当前激活的项目
        
        Args:
            user_id: 用户ID
            project_id: 项目ID，如果为 None 则清除活跃项目
        
        Returns:
            是否设置成功
        
        Raises:
            NotFoundException: 项目不存在或无权访问（当 project_id 不为 None 时）
        """
        key = f"user:{user_id}:active_project"
        
        if project_id is None:
            # 清除活跃项目
            await RedisCache.delete(key)
            logger.info(f"Cleared active project for user {user_id}")
            return True
        
        # 验证项目是否存在且属于该用户
        project = await self.get_project_by_id(project_id, user_id=user_id)
        if not project:
            raise NotFoundException("项目不存在或无权访问")
        
        # 设置活跃项目（缓存7天）
        await RedisCache.set(key, str(project_id), expire=7 * 24 * 3600)
        
        logger.info(f"Set active project {project_id} for user {user_id}")
        
        return True
    
    async def get_user_by_openid(self, openid: str) -> Optional[User]:
        """
        通过 openid 查找用户
        
        Args:
            openid: 微信 openid
        
        Returns:
            用户对象，如果不存在则返回 None
        """
        query = select(User).where(
            User.openid == openid,
            User.is_deleted == False
        )
        
        result = await self.db.execute(query)
        user = result.scalar_one_or_none()
        
        return user

