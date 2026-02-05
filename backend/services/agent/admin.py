"""
Agent管理服务（CRUD操作）
负责Agent的创建、更新、查询、删除等管理功能
支持技能组装模式
"""
from typing import Optional, List, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from loguru import logger

from models.agent import Agent
from services.shared.prompt_builder import PromptBuilder
from services.skill import SkillService


class AgentAdminService:
    """
    Agent管理服务类
    
    职责说明：
    - CRUD操作：创建、更新、查询、删除Agent
    - 技能管理：处理技能组装模式的配置
    - Prompt组装：自动组装技能模式的Prompt
    - 统计更新：更新Agent使用次数
    
    使用示例：
        service = AgentAdminService()
        agent = await service.create_with_skills(db, agent_data)
    """
    
    @staticmethod
    async def create_with_skills(
        db: AsyncSession,
        agent_data: dict,
    ) -> Agent:
        """
        创建Agent（支持技能模式）
        
        业务逻辑：
        1. 提取技能相关字段
        2. 创建Agent基础信息
        3. 如果是技能模式，自动组装system_prompt
        4. 保存到数据库
        
        Args:
            db: 异步数据库会话
            agent_data: Agent数据（包含skill_ids等字段）
        
        Returns:
            创建的Agent实例
        
        Raises:
            ValueError: 技能模式下必须提供skill_ids
        """
        # 提取技能相关字段
        skill_ids = agent_data.pop("skill_ids", None)
        skill_variables = agent_data.pop("skill_variables", None)
        routing_description = agent_data.pop("routing_description", None)
        is_routing_enabled = agent_data.pop("is_routing_enabled", 0)
        agent_mode = agent_data.get("agent_mode", 0)
        
        logger.info(f"创建Agent: {agent_data.get('name')}, mode={agent_mode}")
        
        # 创建Agent基础信息
        agent = Agent(**agent_data)
        db.add(agent)
        await db.flush()  # 获取agent.id
        
        # 如果是技能模式，处理技能配置
        if agent_mode == 1 and skill_ids:
            agent.skill_ids = skill_ids
            agent.skill_variables = skill_variables or {}
            agent.routing_description = routing_description
            agent.is_routing_enabled = is_routing_enabled
            
            # 自动组装system_prompt
            try:
                full_prompt, token_count, _ = await PromptBuilder.build_prompt(
                    db,
                    skill_ids,
                    skill_variables or {}
                )
                agent.system_prompt = full_prompt
                logger.info(f"Agent {agent.name} Prompt组装成功: {token_count} tokens")
            except Exception as e:
                logger.error(f"Agent {agent.name} 组装Prompt失败: {e}")
                # 如果组装失败，使用默认Prompt
                agent.system_prompt = agent_data.get("system_prompt", "")
        
        # 普通模式：直接使用system_prompt
        elif agent_mode == 0:
            agent.system_prompt = agent_data.get("system_prompt", "")
        
        await db.commit()
        await db.refresh(agent)
        return agent
    
    @staticmethod
    async def update_with_skills(
        db: AsyncSession,
        agent_id: int,
        update_data: dict
    ) -> Optional[Agent]:
        """
        更新Agent（支持技能模式）
        
        业务逻辑：
        1. 获取Agent
        2. 更新基础字段
        3. 更新技能配置
        4. 如果是技能模式，重新组装system_prompt
        
        Args:
            db: 异步数据库会话
            agent_id: Agent ID
            update_data: 更新数据
        
        Returns:
            更新后的Agent实例，如果不存在则返回None
        """
        result = await db.execute(select(Agent).filter(Agent.id == agent_id))
        agent = result.scalar_one_or_none()
        if not agent:
            logger.warning(f"更新Agent失败: ID={agent_id} 不存在")
            return None
        
        logger.info(f"更新Agent: {agent.name} (ID={agent_id})")
        
        # 分离技能相关字段
        skill_ids = update_data.pop("skill_ids", None)
        skill_variables = update_data.pop("skill_variables", None)
        routing_description = update_data.pop("routing_description", None)
        is_routing_enabled = update_data.pop("is_routing_enabled", None)
        agent_mode = update_data.get("agent_mode", agent.agent_mode)
        
        # 更新基础字段
        for key, value in update_data.items():
            if hasattr(agent, key) and value is not None:
                setattr(agent, key, value)
        
        # 更新技能配置
        if skill_ids is not None:
            agent.skill_ids = skill_ids
        
        if skill_variables is not None:
            agent.skill_variables = skill_variables
        
        if routing_description is not None:
            agent.routing_description = routing_description
        
        if is_routing_enabled is not None:
            agent.is_routing_enabled = is_routing_enabled
        
        # 如果是技能模式且有技能，重新组装system_prompt
        if agent_mode == 1 and agent.skill_ids:
            try:
                full_prompt, token_count, _ = await PromptBuilder.build_prompt(
                    db,
                    agent.skill_ids,
                    agent.skill_variables or {}
                )
                agent.system_prompt = full_prompt
                logger.info(f"Agent {agent.name} Prompt重新组装成功: {token_count} tokens")
            except Exception as e:
                logger.error(f"Agent {agent.name} 重新组装Prompt失败: {e}")
        
        await db.commit()
        await db.refresh(agent)
        return agent
    
    @staticmethod
    async def get_detail_with_skills(db: AsyncSession, agent_id: int) -> Optional[dict]:
        """
        获取Agent详情（包含技能详情）
        
        Args:
            db: 异步数据库会话
            agent_id: Agent ID
        
        Returns:
            Agent详情字典，如果不存在则返回None
        """
        result = await db.execute(select(Agent).filter(Agent.id == agent_id))
        agent = result.scalar_one_or_none()
        if not agent:
            logger.debug(f"获取Agent详情失败: ID={agent_id} 不存在")
            return None
        
        # 如果是技能模式，加载技能详情
        skills_detail = []
        if agent.agent_mode == 1 and agent.skill_ids:
            skills = await SkillService.get_by_ids(db, agent.skill_ids)
            
            # 按skill_ids顺序排序
            skills_map = {s.id: s for s in skills}
            for skill_id in agent.skill_ids:
                if skill_id in skills_map:
                    skills_detail.append(skills_map[skill_id])
            
            logger.debug(f"Agent {agent.name} 加载了 {len(skills_detail)} 个技能详情")
        
        return {
            "id": agent.id,
            "name": agent.name,
            "icon": agent.icon,
            "description": agent.description or "",
            "agent_mode": agent.agent_mode,
            "system_prompt": agent.system_prompt,
            "model": agent.model,
            "config": agent.config,
            "sort_order": agent.sort_order,
            "status": agent.status,
            "usage_count": agent.usage_count,
            "skill_ids": agent.skill_ids,
            "skill_variables": agent.skill_variables,
            "routing_description": agent.routing_description,
            "is_routing_enabled": agent.is_routing_enabled,
            "is_system": agent.is_system,
            "skills_detail": [
                {
                    "id": s.id,
                    "name": s.name,
                    "category": s.category,
                    "meta_description": s.meta_description,
                    "content": s.content,
                    "status": s.status,
                    "created_at": s.created_at,
                }
                for s in skills_detail
            ],
            "created_at": agent.created_at,
            "updated_at": agent.updated_at,
        }
    
    @staticmethod
    async def get_list(
        db: AsyncSession,
        page: int = 1,
        size: int = 20,
        name: Optional[str] = None,
        agent_mode: Optional[int] = None,
        status: Optional[int] = None,
    ) -> Tuple[List[Agent], int]:
        """
        获取Agent列表（分页）
        
        Args:
            db: 异步数据库会话
            page: 页码
            size: 每页数量
            name: 名称筛选（模糊查询）
            agent_mode: 运行模式筛选
            status: 状态筛选
        
        Returns:
            (Agent列表, 总数)
        """
        # 构建查询
        query = select(Agent)
        count_query = select(func.count()).select_from(Agent)
        
        # 筛选条件
        conditions = []
        if name:
            conditions.append(Agent.name.like(f"%{name}%"))
        if agent_mode is not None:
            conditions.append(Agent.agent_mode == agent_mode)
        if status is not None:
            conditions.append(Agent.status == status)
        
        if conditions:
            query = query.filter(*conditions)
            count_query = count_query.filter(*conditions)
        
        # 获取总数
        total_result = await db.execute(count_query)
        total = total_result.scalar()
        
        # 分页查询
        query = query.order_by(Agent.sort_order.asc(), Agent.id.desc()).offset((page - 1) * size).limit(size)
        result = await db.execute(query)
        agents = result.scalars().all()
        
        logger.debug(f"获取Agent列表: page={page}, size={size}, total={total}, 返回{len(agents)}条")
        
        return agents, total
    
    @staticmethod
    async def delete(db: AsyncSession, agent_id: int) -> bool:
        """
        删除Agent
        
        Args:
            db: 异步数据库会话
            agent_id: Agent ID
        
        Returns:
            是否删除成功
        """
        result = await db.execute(select(Agent).filter(Agent.id == agent_id))
        agent = result.scalar_one_or_none()
        if not agent:
            logger.warning(f"删除Agent失败: ID={agent_id} 不存在")
            return False
        
        logger.info(f"删除Agent: {agent.name} (ID={agent_id})")
        await db.delete(agent)
        await db.flush()
        await db.commit()
        return True
    
    @staticmethod
    async def increment_usage_count(db: AsyncSession, agent_id: int) -> bool:
        """
        增加Agent使用次数
        
        使用原子更新操作，避免并发问题
        使用独立的数据库会话确保统计更新被正确提交，不影响主事务
        
        Args:
            db: 异步数据库会话（用于兼容性，实际使用独立会话）
            agent_id: Agent ID
        
        Returns:
            是否成功
        """
        from sqlalchemy import update
        from db import async_session_maker
        
        # 使用独立的数据库会话，确保统计更新被正确提交
        # 这对于流式响应场景特别重要，因为外层事务可能在流式响应完成前就提交了
        async with async_session_maker() as stat_db:
            try:
                # 使用原子更新操作，直接更新数据库，避免加载整个对象
                result = await stat_db.execute(
                    update(Agent)
                    .where(Agent.id == agent_id)
                    .values(usage_count=Agent.usage_count + 1)
                )
                
                # 检查是否有行被更新
                if result.rowcount == 0:
                    logger.warning(f"⚠️ 增加使用次数失败: Agent ID={agent_id} 不存在或未找到")
                    return False
                
                logger.info(f"📊 Agent ID={agent_id} 执行原子更新操作，影响行数: {result.rowcount}")
                
                # 提交事务，确保统计更新被持久化
                await stat_db.commit()
                
                logger.info(f"✅ Agent ID={agent_id} 使用次数已增加并提交 (影响 {result.rowcount} 行)")
                return True
                
            except Exception as e:
                logger.error(f"增加Agent使用次数异常: Agent ID={agent_id}, 错误={e}")
                # 如果提交失败，尝试回滚
                try:
                    await stat_db.rollback()
                except Exception as rollback_error:
                    logger.error(f"回滚事务失败: {rollback_error}")
                return False


# 向后兼容：AgentServiceV2 作为 AgentAdminService 的别名
AgentServiceV2 = AgentAdminService

