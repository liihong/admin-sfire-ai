"""
Agent Service
智能体管理服务
"""
from typing import List, Optional
from datetime import datetime

from sqlalchemy import select, func, and_, or_, desc, asc
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from app.models.agent import Agent
from app.schemas.agent import (
    AgentCreate,
    AgentUpdate,
    AgentQueryParams,
    AgentConfig,
)
from app.utils.exceptions import (
    NotFoundException,
    BadRequestException,
)
from app.utils.pagination import paginate, paginate_query, build_order_by, PageResult


class AgentService:
    """智能体管理服务类"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_agent_list(
        self,
        params: AgentQueryParams,
    ) -> PageResult[Agent]:
        """
        获取智能体列表（分页）
        
        Args:
            params: 查询参数
            
        Returns:
            PageResult[Agent]: 分页结果
        """
        query = select(Agent)
        
        # 构建查询条件
        conditions = []
        
        if params.name:
            conditions.append(Agent.name.like(f"%{params.name}%"))
        
        if params.status is not None:
            conditions.append(Agent.status == params.status)
        
        if conditions:
            query = query.where(and_(*conditions))
        
        # 排序：按 sort_order 升序，然后按创建时间降序
        query = query.order_by(asc(Agent.sort_order), desc(Agent.created_at))
        
        # 构建计数查询
        count_query = select(func.count(Agent.id))
        if conditions:
            count_query = count_query.where(and_(*conditions))
        
        # 使用 paginate_query 处理查询对象（因为传递的是 Select 对象，不是模型类）
        result = await paginate_query(
            self.db,
            query,
            count_query,
            page_num=params.pageNum,
            page_size=params.pageSize,
        )
        
        return result
    
    async def get_agent_by_id(self, agent_id: int) -> Agent:
        """
        根据ID获取智能体
        
        Args:
            agent_id: 智能体ID
            
        Returns:
            Agent: 智能体对象
            
        Raises:
            NotFoundException: 智能体不存在
        """
        result = await self.db.execute(
            select(Agent).where(Agent.id == agent_id)
        )
        agent = result.scalar_one_or_none()
        
        if not agent:
            raise NotFoundException(f"智能体 {agent_id} 不存在")
        
        return agent
    
    async def create_agent(self, agent_data: AgentCreate) -> Agent:
        """
        创建智能体
        
        Args:
            agent_data: 智能体数据
            
        Returns:
            Agent: 创建的智能体对象
        """
        # 检查名称是否已存在
        existing = await self.db.execute(
            select(Agent).where(Agent.name == agent_data.name)
        )
        if existing.scalar_one_or_none():
            raise BadRequestException(f"智能体名称 '{agent_data.name}' 已存在")
        
        # 创建新智能体
        agent = Agent(
            name=agent_data.name,
            icon=agent_data.icon,
            description=agent_data.description,
            system_prompt=agent_data.systemPrompt,
            model=agent_data.model,
            config=agent_data.config.model_dump() if agent_data.config else None,
            sort_order=agent_data.sortOrder,
            status=agent_data.status,
        )
        
        self.db.add(agent)
        await self.db.flush()
        await self.db.refresh(agent)
        
        return agent
    
    async def update_agent(self, agent_id: int, agent_data: AgentUpdate) -> Agent:
        """
        更新智能体
        
        Args:
            agent_id: 智能体ID
            agent_data: 更新数据
            
        Returns:
            Agent: 更新后的智能体对象
            
        Raises:
            NotFoundException: 智能体不存在
            BadRequestException: 名称冲突
        """
        agent = await self.get_agent_by_id(agent_id)
        
        # 如果更新名称，检查是否冲突
        if agent_data.name and agent_data.name != agent.name:
            existing = await self.db.execute(
                select(Agent).where(Agent.name == agent_data.name)
            )
            if existing.scalar_one_or_none():
                raise BadRequestException(f"智能体名称 '{agent_data.name}' 已存在")
        
        # 更新字段
        if agent_data.name:
            agent.name = agent_data.name
        if agent_data.icon:
            agent.icon = agent_data.icon
        if agent_data.description is not None:
            agent.description = agent_data.description
        if agent_data.systemPrompt:
            agent.system_prompt = agent_data.systemPrompt
        if agent_data.model:
            agent.model = agent_data.model
        if agent_data.config:
            agent.config = agent_data.config.model_dump()
        if agent_data.sortOrder is not None:
            agent.sort_order = agent_data.sortOrder
        if agent_data.status is not None:
            agent.status = agent_data.status
        
        await self.db.flush()
        await self.db.refresh(agent)
        
        return agent
    
    async def delete_agent(self, agent_id: int) -> None:
        """
        删除智能体
        
        Args:
            agent_id: 智能体ID
            
        Raises:
            NotFoundException: 智能体不存在
        """
        agent = await self.get_agent_by_id(agent_id)
        await self.db.delete(agent)
        await self.db.flush()
    
    async def update_status(self, agent_id: int, status: int) -> Agent:
        """
        更新智能体状态（上架/下架）
        
        Args:
            agent_id: 智能体ID
            status: 状态（0-下架, 1-上架）
            
        Returns:
            Agent: 更新后的智能体对象
            
        Raises:
            NotFoundException: 智能体不存在
        """
        agent = await self.get_agent_by_id(agent_id)
        agent.status = status
        await self.db.flush()
        await self.db.refresh(agent)
        return agent
    
    async def update_sort_order(self, agent_id: int, sort_order: int) -> Agent:
        """
        更新智能体排序
        
        Args:
            agent_id: 智能体ID
            sort_order: 排序顺序
            
        Returns:
            Agent: 更新后的智能体对象
            
        Raises:
            NotFoundException: 智能体不存在
        """
        agent = await self.get_agent_by_id(agent_id)
        agent.sort_order = sort_order
        await self.db.flush()
        await self.db.refresh(agent)
        return agent
    
    async def batch_update_sort(self, items: List[dict]) -> None:
        """
        批量更新智能体排序
        
        Args:
            items: 排序项列表，格式：[{"id": agent_id, "sortOrder": sort_order}, ...]
        """
        for item in items:
            agent_id = item.get("id")
            sort_order = item.get("sortOrder")
            
            if agent_id and sort_order is not None:
                agent = await self.get_agent_by_id(agent_id)
                agent.sort_order = sort_order
        
        await self.db.flush()
