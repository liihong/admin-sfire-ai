"""
Agent Service
智能体管理服务
"""
from typing import List
from sqlalchemy import select, func, and_, desc, asc
from sqlalchemy.ext.asyncio import AsyncSession

from models.agent import Agent
from schemas.agent import (
    AgentCreate,
    AgentUpdate,
    AgentQueryParams,
)
from utils.exceptions import (
    NotFoundException,
    BadRequestException,
)
from utils.pagination import paginate_query, PageResult
from services.base import BaseService


class AgentService(BaseService):
    """智能体管理服务类"""
    
    def __init__(self, db: AsyncSession):
        super().__init__(db, Agent, "智能体", check_soft_delete=False)
    
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
        conditions = []
        
        if params.name:
            conditions.append(Agent.name.like(f"%{params.name}%"))
        if params.status is not None:
            conditions.append(Agent.status == params.status)
        
        if conditions:
            query = query.where(and_(*conditions))
        
        query = query.order_by(asc(Agent.sort_order), desc(Agent.created_at))
        
        count_query = select(func.count(Agent.id))
        if conditions:
            count_query = count_query.where(and_(*conditions))
        
        return await paginate_query(
            self.db,
            query,
            count_query,
            page_num=params.pageNum,
            page_size=params.pageSize,
        )
    
    async def get_agent_by_id(self, agent_id: int) -> Agent:
        """根据ID获取智能体"""
        return await super().get_by_id(agent_id, error_msg=f"智能体 {agent_id} 不存在")
    
    async def create_agent(self, agent_data: AgentCreate) -> Agent:
        """创建智能体"""
        # 检查名称唯一性
        from utils.query import check_unique
        await check_unique(
            db=self.db,
            model=Agent,
            field_name="name",
            value=agent_data.name,
            error_msg=f"智能体名称 '{agent_data.name}' 已存在",
        )
        
        # 手动创建 Agent 对象，处理字段名映射（驼峰 -> 下划线）
        agent = Agent(
            name=agent_data.name,
            icon=agent_data.icon,
            description=agent_data.description,
            system_prompt=agent_data.systemPrompt,  # 驼峰 -> 下划线
            model=agent_data.model,
            config=agent_data.config.model_dump() if agent_data.config else None,
            sort_order=agent_data.sortOrder,  # 驼峰 -> 下划线
            status=agent_data.status,
        )
        
        self.db.add(agent)
        await self.db.flush()
        await self.db.refresh(agent)
        return agent
    
    async def update_agent(self, agent_id: int, agent_data: AgentUpdate) -> Agent:
        """更新智能体"""
        from utils.query import check_unique
        
        # 获取现有智能体
        agent = await self.get_agent_by_id(agent_id)
        
        # 检查名称唯一性（如果名称有变化）
        if agent_data.name and agent_data.name != agent.name:
            await check_unique(
                db=self.db,
                model=Agent,
                field_name="name",
                value=agent_data.name,
                exclude_id=agent_id,
                error_msg=f"智能体名称 '{agent_data.name}' 已存在",
            )
        
        # 获取需要更新的字段
        update_data = agent_data.model_dump(exclude_unset=True)
        
        # 更新字段（处理驼峰 -> 下划线字段名映射）
        if "name" in update_data:
            agent.name = update_data["name"]
        if "icon" in update_data:
            agent.icon = update_data["icon"]
        if "description" in update_data:
            agent.description = update_data["description"]
        if "systemPrompt" in update_data:
            agent.system_prompt = update_data["systemPrompt"]
        if "model" in update_data:
            agent.model = update_data["model"]
        if "config" in update_data and update_data["config"]:
            agent.config = update_data["config"]
        if "sortOrder" in update_data:
            agent.sort_order = update_data["sortOrder"]
        if "status" in update_data:
            agent.status = update_data["status"]
        
        await self.db.flush()
        await self.db.refresh(agent)
        return agent
    
    async def delete_agent(self, agent_id: int) -> None:
        """删除智能体"""
        await super().delete(agent_id, hard_delete=True)
        await self.db.flush()
    
    async def update_status(self, agent_id: int, status: int) -> Agent:
        """更新智能体状态（上架/下架）"""
        agent = await super().get_by_id(agent_id)
        agent.status = status
        await self.db.flush()
        await self.db.refresh(agent)
        return agent
    
    async def update_sort_order(self, agent_id: int, sort_order: int) -> Agent:
        """更新智能体排序"""
        agent = await super().get_by_id(agent_id)
        agent.sort_order = sort_order
        await self.db.flush()
        await self.db.refresh(agent)
        return agent
    
    async def batch_update_sort(self, items: List[dict]) -> None:
        """批量更新智能体排序"""
        for item in items:
            agent_id = item.get("id")
            sort_order = item.get("sortOrder")
            if agent_id and sort_order is not None:
                try:
                    agent = await super().get_by_id(agent_id)
                    agent.sort_order = sort_order
                except NotFoundException:
                    continue
        await self.db.flush()
