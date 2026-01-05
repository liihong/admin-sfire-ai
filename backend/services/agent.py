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
        unique_fields = {
            "name": {"error_msg": f"智能体名称 '{agent_data.name}' 已存在"},
        }
        
        def before_create(agent: Agent, data: AgentCreate):
            """创建前的钩子函数"""
            # 处理特殊字段映射
            if hasattr(data, "systemPrompt"):
                agent.system_prompt = data.systemPrompt
            if hasattr(data, "sortOrder"):
                agent.sort_order = data.sortOrder
            if hasattr(data, "config") and data.config:
                agent.config = data.config.model_dump()
        
        agent = await super().create(
            data=agent_data,
            unique_fields=unique_fields,
            before_create=before_create,
        )
        
        await self.db.flush()
        await self.db.refresh(agent)
        return agent
    
    async def update_agent(self, agent_id: int, agent_data: AgentUpdate) -> Agent:
        """更新智能体"""
        # 检查名称唯一性（如果名称有变化）
        if agent_data.name:
            agent = await self.get_agent_by_id(agent_id)
            if agent_data.name != agent.name:
                unique_fields = {
                    "name": {"error_msg": f"智能体名称 '{agent_data.name}' 已存在"},
                }
            else:
                unique_fields = None
        else:
            unique_fields = None
        
        def before_update(agent: Agent, data: AgentUpdate):
            """更新前的钩子函数"""
            # 处理特殊字段映射
            update_data = data.model_dump(exclude_unset=True)
            if "systemPrompt" in update_data:
                agent.system_prompt = update_data["systemPrompt"]
            if "sortOrder" in update_data:
                agent.sort_order = update_data["sortOrder"]
            if "config" in update_data and update_data["config"]:
                agent.config = update_data["config"]
        
        agent = await super().update(
            obj_id=agent_id,
            data=agent_data,
            unique_fields=unique_fields,
            before_update=before_update,
        )
        
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
