"""
技能库业务逻辑服务
"""
from typing import List, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from loguru import logger

from models.skill_library import SkillLibrary


class SkillService:
    """技能库业务逻辑"""

    @staticmethod
    async def get_list(
        db: AsyncSession,
        page: int = 1,
        size: int = 20,
        category: Optional[str] = None,
        status: Optional[int] = None,
    ) -> Tuple[List[SkillLibrary], int]:
        """
        获取技能列表

        Args:
            db: 数据库会话
            page: 页码（从1开始）
            size: 每页数量
            category: 分类筛选
            status: 状态筛选（1-启用, 0-禁用）

        Returns:
            (技能列表, 总数)
        """
        query = select(SkillLibrary)

        # 筛选条件
        conditions = []
        if category:
            conditions.append(SkillLibrary.category == category)
        if status is not None:
            conditions.append(SkillLibrary.status == status)

        if conditions:
            query = query.filter(*conditions)

        # 获取总数
        count_query = select(func.count()).select_from(SkillLibrary)
        if conditions:
            count_query = count_query.filter(*conditions)
        result = await db.execute(count_query)
        total = result.scalar()

        # 分页查询
        query = query.order_by(SkillLibrary.id.desc()).offset((page - 1) * size).limit(size)
        result = await db.execute(query)
        skills = result.scalars().all()

        return skills, total

    @staticmethod
    async def get_by_id(db: AsyncSession, skill_id: int) -> Optional[SkillLibrary]:
        """根据ID获取技能"""
        result = await db.execute(
            select(SkillLibrary).filter(SkillLibrary.id == skill_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def create(db: AsyncSession, skill_data: dict) -> SkillLibrary:
        """创建技能"""
        skill = SkillLibrary(**skill_data)
        db.add(skill)
        await db.commit()
        await db.refresh(skill)
        return skill

    @staticmethod
    async def update(db: AsyncSession, skill_id: int, skill_data: dict) -> Optional[SkillLibrary]:
        """更新技能"""
        skill = await SkillService.get_by_id(db, skill_id)
        if not skill:
            return None

        # 更新字段
        for key, value in skill_data.items():
            if hasattr(skill, key) and value is not None:
                setattr(skill, key, value)

        await db.commit()
        await db.refresh(skill)
        return skill

    @staticmethod
    async def delete(db: AsyncSession, skill_id: int) -> bool:
        """
        删除技能（物理删除）

        说明：
            - 此方法会直接从数据库中删除记录
            - 禁用/启用请使用单独的状态更新接口，不要与删除混用
        """
        skill = await SkillService.get_by_id(db, skill_id)
        if not skill:
            return False

        # 物理删除记录
        await db.delete(skill)
        await db.commit()
        return True

    @staticmethod
    async def update_status(
        db: AsyncSession,
        skill_id: int,
        status: int,
    ) -> Optional[SkillLibrary]:
        """
        更新技能状态（启用/禁用）

        Args:
            db: 异步数据库会话
            skill_id: 技能ID
            status: 状态（1-启用, 0-禁用）

        Returns:
            更新后的技能对象；不存在时返回 None
        """
        skill = await SkillService.get_by_id(db, skill_id)
        if not skill:
            return None

        # 仅允许 0/1 两种状态，避免非法值
        skill.status = 1 if status == 1 else 0
        await db.commit()
        await db.refresh(skill)
        return skill

    @staticmethod
    async def get_by_ids(db: AsyncSession, skill_ids: List[int]) -> List[SkillLibrary]:
        """
        根据ID列表获取技能（异步版本）
        
        Args:
            db: 异步数据库会话
            skill_ids: 技能ID列表
            
        Returns:
            技能列表
        """
        if not skill_ids:
            logger.debug("技能ID列表为空，返回空列表")
            return []
        result = await db.execute(
            select(SkillLibrary).filter(SkillLibrary.id.in_(skill_ids))
        )
        skills = result.scalars().all()
        logger.debug(f"获取到 {len(skills)} 个技能 (IDs: {skill_ids})")
        return skills

    @staticmethod
    async def get_categories(db: AsyncSession) -> List[str]:
        """获取所有分类"""
        result = await db.execute(
            select(SkillLibrary.category).distinct()
        )
        return [r[0] for r in result.all()]

    @staticmethod
    async def get_categories_with_count(db: AsyncSession) -> List[dict]:
        """获取所有分类及其数量"""
        result = await db.execute(
            select(SkillLibrary.category, func.count(SkillLibrary.id))
            .filter(SkillLibrary.status == 1)
            .group_by(SkillLibrary.category)
        )
        return [{"category": r[0], "count": r[1]} for r in result.all()]
