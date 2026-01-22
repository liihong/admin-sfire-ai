"""
Agent核心执行器（纯技术实现）
负责路由决策、Prompt组装、LLM调用等纯技术操作
不涉及业务逻辑（权限验证、余额检查、会话管理等）
"""
from typing import Optional, AsyncGenerator, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from loguru import logger

from models.agent import Agent
from models.llm_model import LLMModel
from services.routing import MasterRouter, PromptEngine
from services.shared.prompt_builder import PromptBuilder
from services.shared.llm_service import LLMFactory, BaseLLM
from utils.exceptions import BadRequestException


class AgentExecutor:
    """
    Agent核心执行器
    
    职责：
    - 路由决策：根据用户输入选择技能
    - Prompt组装：组装系统Prompt和用户消息
    - LLM调用：调用LLM生成响应
    
    不涉及：
    - 用户权限验证
    - 余额检查
    - 会话管理
    - 算力扣除
    - 内容审查
    
    使用示例：
        executor = AgentExecutor(db)
        async for chunk in executor.execute_stream(
            agent=agent,
            user_input="你好",
            persona_prompt="你是AI助手",
            temperature=0.7,
            max_tokens=2048
        ):
            print(chunk)
    """
    
    def __init__(self, db: AsyncSession):
        """
        初始化Agent执行器
        
        Args:
            db: 异步数据库会话
        """
        self.db = db
        self.master_router = MasterRouter()
        self.prompt_engine = PromptEngine()
    
    async def execute_stream(
        self,
        agent: Agent,
        user_input: str,
        persona_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        llm_client: Optional[BaseLLM] = None
    ) -> AsyncGenerator[str, None]:
        """
        执行Agent（流式响应，纯技术实现）
        
        技术流程：
        1. 路由决策：根据用户输入选择技能
        2. Prompt组装：组装系统Prompt和用户消息
        3. 解析LLM模型：从Agent配置解析模型
        4. 创建LLM客户端（如果未提供）
        5. 调用LLM生成响应（流式）
        
        Args:
            agent: Agent对象（必须已加载）
            user_input: 用户输入文本
            persona_prompt: IP人设Prompt（可选）
            temperature: 温度参数（可选，使用Agent配置的默认值）
            max_tokens: 最大Token数（可选，使用Agent配置的默认值）
            llm_client: LLM客户端（可选，如果提供则直接使用）
        
        Yields:
            流式输出的文本块
        
        Raises:
            BadRequestException: 模型不存在或LLM调用失败
        """
        # 1. 路由决策
        routing_result = await self.master_router.route(
            db=self.db,
            agent=agent,
            user_input=user_input
        )
        
        logger.debug(
            f"路由完成: 选中{len(routing_result.selected_skill_ids)}个技能, "
            f"方法={routing_result.routing_method}"
        )
        
        # 2. Prompt组装
        prompt_result = await self.prompt_engine.assemble_prompt(
            db=self.db,
            agent=agent,
            selected_skill_ids=routing_result.selected_skill_ids,
            skill_variables=agent.skill_variables or {},
            persona_prompt=persona_prompt,
            user_input=user_input
        )
        
        logger.debug(
            f"Prompt组装完成: {prompt_result.token_count} tokens, "
            f"使用了{len(prompt_result.skills_applied)}个技能"
        )
        
        # 3. 解析LLM模型（如果未提供llm_client）
        if not llm_client:
            llm_model = await self._resolve_llm_model(agent.model)
            if not llm_model:
                raise BadRequestException(
                    msg=f"Agent配置的模型 '{agent.model}' 不存在或未启用"
                )
            
            logger.debug(f"使用模型: {llm_model.name} (ID={llm_model.id}, provider={llm_model.provider})")
            
            # 4. 创建LLM客户端
            try:
                llm_client = await LLMFactory.create_from_db(self.db, llm_model.id)
            except Exception as e:
                logger.error(f"创建LLM客户端失败: {e}")
                raise BadRequestException(msg=f"创建LLM客户端失败: {str(e)}")
        
        # 5. 获取配置参数
        agent_config = agent.config or {}
        final_temperature = temperature if temperature is not None else agent_config.get("temperature", 0.7)
        final_max_tokens = max_tokens if max_tokens is not None else agent_config.get("maxTokens", 2048)
        
        # 6. 调用LLM生成响应（流式）
        async for chunk in llm_client.generate_stream(
            prompt=prompt_result.user_message,
            system_prompt=prompt_result.system_prompt,
            temperature=final_temperature,
            max_tokens=final_max_tokens
        ):
            yield chunk
    
    async def execute_non_stream(
        self,
        agent: Agent,
        user_input: str,
        persona_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        llm_client: Optional[BaseLLM] = None
    ) -> Tuple[str, str, list, int]:
        """
        执行Agent（非流式响应，纯技术实现）
        
        Args:
            参数同execute_stream方法
        
        Returns:
            (response, system_prompt, skills_applied, token_count)
            - response: AI回复文本
            - system_prompt: 使用的系统Prompt
            - skills_applied: 使用的技能ID列表
            - token_count: Token数量
        """
        # 1-4步与execute_stream相同
        routing_result = await self.master_router.route(
            db=self.db,
            agent=agent,
            user_input=user_input
        )
        
        prompt_result = await self.prompt_engine.assemble_prompt(
            db=self.db,
            agent=agent,
            selected_skill_ids=routing_result.selected_skill_ids,
            skill_variables=agent.skill_variables or {},
            persona_prompt=persona_prompt,
            user_input=user_input
        )
        
        if not llm_client:
            llm_model = await self._resolve_llm_model(agent.model)
            if not llm_model:
                raise BadRequestException(
                    msg=f"Agent配置的模型 '{agent.model}' 不存在或未启用"
                )
            
            llm_client = await LLMFactory.create_from_db(self.db, llm_model.id)
        
        agent_config = agent.config or {}
        final_temperature = temperature if temperature is not None else agent_config.get("temperature", 0.7)
        final_max_tokens = max_tokens if max_tokens is not None else agent_config.get("maxTokens", 2048)
        
        # 调用LLM生成响应（非流式）
        response = await llm_client.generate_text(
            prompt=prompt_result.user_message,
            system_prompt=prompt_result.system_prompt,
            temperature=final_temperature,
            max_tokens=final_max_tokens
        )
        
        return (
            response,
            prompt_result.system_prompt,
            prompt_result.skills_applied,
            prompt_result.token_count
        )
    
    async def _resolve_llm_model(self, model_identifier: str) -> Optional[LLMModel]:
        """
        解析模型标识符，从数据库获取LLMModel对象
        
        Args:
            model_identifier: 模型标识符（可能是数据库ID、model_id字段或provider）
        
        Returns:
            LLMModel对象，如果不存在则返回None
        """
        # 尝试作为数据库ID查询
        if model_identifier.isdigit():
            try:
                result = await self.db.execute(
                    select(LLMModel).filter(
                        LLMModel.id == int(model_identifier),
                        LLMModel.is_enabled == True
                    )
                )
                llm_model = result.scalar_one_or_none()
                if llm_model:
                    return llm_model
            except (ValueError, Exception):
                pass
        
        # 尝试通过model_id字段查询
        result = await self.db.execute(
            select(LLMModel).filter(
                LLMModel.model_id == model_identifier,
                LLMModel.is_enabled == True
            ).order_by(LLMModel.sort_order).limit(1)
        )
        llm_model = result.scalar_one_or_none()
        if llm_model:
            return llm_model
        
        # 尝试通过provider查询
        result = await self.db.execute(
            select(LLMModel).filter(
                LLMModel.provider == model_identifier.lower(),
                LLMModel.is_enabled == True
            ).order_by(LLMModel.sort_order).limit(1)
        )
        llm_model = result.scalar_one_or_none()
        return llm_model

