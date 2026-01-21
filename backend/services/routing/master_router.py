"""
Master Router：策略分发层
根据Agent配置决定路由策略
"""
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from core.config import settings
from models.agent import Agent
from .skill_router import SkillRouter
from .types import RoutingResult


class MasterRouter:
    """主路由器：负责策略分发和路由决策"""
    
    @staticmethod
    async def route(
        db: AsyncSession,
        agent: Agent,
        user_input: str
    ) -> RoutingResult:
        """
        路由决策：根据Agent配置决定路由策略
        
        Args:
            db: 异步数据库会话
            agent: Agent对象
            user_input: 用户输入
        
        Returns:
            RoutingResult: 路由结果
        """
        # 如果Agent未启用路由或不是技能模式，返回全部技能ID（静态加载）
        if agent.agent_mode != 1 or agent.is_routing_enabled != 1:
            skill_ids = agent.skill_ids or []
            logger.debug(
                f"Agent {agent.name} 未启用路由或非技能模式，"
                f"使用全部{len(skill_ids)}个技能"
            )
            return RoutingResult(
                selected_skill_ids=skill_ids,
                static_skill_ids=skill_ids,
                dynamic_skill_ids=[],
                routing_method="static"
            )
        
        # 技能模式且启用路由：调用SkillRouter进行路由
        agent_skill_ids = agent.skill_ids or []
        routing_description = agent.routing_description or ""
        
        if not agent_skill_ids:
            logger.warning(f"Agent {agent.name} 技能模式但skill_ids为空")
            return RoutingResult(
                selected_skill_ids=[],
                static_skill_ids=[],
                dynamic_skill_ids=[],
                routing_method="static"
            )
        
        # 从配置读取路由Agent ID（LLM模型从Agent表读取）
        router_agent_id = None
        if settings.ROUTER_AGENT_ID:
            try:
                router_agent_id = int(settings.ROUTER_AGENT_ID)
            except (ValueError, TypeError):
                logger.warning(f"ROUTER_AGENT_ID配置无效: {settings.ROUTER_AGENT_ID}")
        
        # 调用SkillRouter进行路由（LLM模型从router_agent.model字段读取）
        routing_result = await SkillRouter.route_skills(
            db=db,
            agent_skill_ids=agent_skill_ids,
            user_input=user_input,
            routing_description=routing_description,
            use_vector=True,  # 默认使用向量检索
            top_k=3,
            threshold=0.7,
            router_agent_id=router_agent_id
        )
        
        logger.info(
            f"Master Router完成: Agent={agent.name}, "
            f"选中{len(routing_result.selected_skill_ids)}个技能, "
            f"方法={routing_result.routing_method}"
        )
        
        return routing_result

