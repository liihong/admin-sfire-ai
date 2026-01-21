"""
Agent执行服务
整合路由模块和业务逻辑（会话、算力、LLM调用）
"""
from typing import Optional, AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from loguru import logger

from models.agent import Agent
from models.project import Project
from models.llm_model import LLMModel
from services.routing import MasterRouter, PromptEngine
from services.prompt_builder import PromptBuilder
from services.enhanced_conversation import EnhancedConversationService
from services.llm_service import LLMFactory
from services.agent_service_v2 import AgentServiceV2
from utils.exceptions import NotFoundException, BadRequestException


class AgentExecutionService:
    """Agent执行服务：整合路由模块和业务逻辑"""
    
    def __init__(self, db: AsyncSession):
        """
        初始化Agent执行服务
        
        Args:
            db: 异步数据库会话
        """
        self.db = db
        self.master_router = MasterRouter()
        self.prompt_engine = PromptEngine()
    
    async def execute(
        self,
        agent_id: int,
        user_id: int,
        project_id: int,
        input_text: str,
        enable_persona: bool = True,
        conversation_id: Optional[int] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> AsyncGenerator[str, None]:
        """
        执行Agent（流式响应）
        
        完整流程：
        1. 获取Agent配置
        2. 获取IP基因（如果enable_persona=True）
        3. 调用MasterRouter进行路由决策
        4. 调用PromptEngine组装Prompt
        5. 从数据库读取Agent配置的模型
        6. 创建LLM客户端
        7. 创建EnhancedConversationService
        8. 调用EnhancedConversationService.chat（处理算力扣除、内容审查、流式响应）
        
        Args:
            agent_id: Agent ID
            user_id: 用户ID
            project_id: 项目ID
            input_text: 用户输入
            enable_persona: 是否启用IP基因注入
            conversation_id: 会话ID（可选）
            temperature: 温度参数（可选，使用Agent配置的默认值）
            max_tokens: 最大Token数（可选，使用Agent配置的默认值）
        
        Yields:
            流式输出的文本块
        
        Raises:
            NotFoundException: Agent不存在或未上架
            BadRequestException: 用户输入为空或其他业务错误
        """
        # 1. 获取Agent配置
        result = await self.db.execute(
            select(Agent).filter(Agent.id == agent_id)
        )
        agent = result.scalar_one_or_none()
        if not agent:
            raise NotFoundException(msg="Agent不存在")
        
        if agent.status != 1:
            raise BadRequestException(msg="Agent未上架")
        
        logger.info(f"执行Agent: {agent.name} (ID={agent_id}), 用户ID={user_id}")
        
        # 2. 获取IP基因（如果启用）
        persona_prompt = None
        if enable_persona:
            result = await self.db.execute(
                select(Project).filter(
                    Project.id == project_id,
                    Project.user_id == user_id,
                    Project.is_deleted == False,
                )
            )
            project = result.scalar_one_or_none()
            
            if project and project.persona_settings:
                persona_prompt = PromptBuilder.extract_persona_prompt(
                    project.persona_settings
                )
                logger.debug(f"已注入IP基因: 项目={project.name}")
        
        # 3. 调用MasterRouter进行路由决策（LLM模型从router_agent.model字段读取）
        routing_result = await self.master_router.route(
            db=self.db,
            agent=agent,
            user_input=input_text
        )
        
        logger.info(
            f"路由完成: 选中{len(routing_result.selected_skill_ids)}个技能, "
            f"方法={routing_result.routing_method}"
        )
        
        # 4. 调用PromptEngine组装Prompt
        prompt_result = await self.prompt_engine.assemble_prompt(
            db=self.db,
            agent=agent,
            selected_skill_ids=routing_result.selected_skill_ids,
            skill_variables=agent.skill_variables or {},
            persona_prompt=persona_prompt,
            user_input=input_text
        )
        
        logger.debug(
            f"Prompt组装完成: {prompt_result.token_count} tokens, "
            f"使用了{len(prompt_result.skills_applied)}个技能"
        )
        
        # 5. 从数据库读取Agent配置的模型
        # agent.model字段可能是model_id（数据库ID）、model_id（模型标识）或provider
        llm_model = await self._resolve_llm_model(agent.model)
        if not llm_model:
            raise BadRequestException(
                msg=f"Agent配置的模型 '{agent.model}' 不存在或未启用"
            )
        
        logger.info(f"使用模型: {llm_model.name} (ID={llm_model.id}, provider={llm_model.provider})")
        
        # 6. 创建LLM客户端（从数据库读取配置）
        try:
            llm_client = await LLMFactory.create_from_db(self.db, llm_model.id)
        except Exception as e:
            logger.error(f"创建LLM客户端失败: {e}")
            raise BadRequestException(msg=f"创建LLM客户端失败: {str(e)}")
        
        # 7. 创建EnhancedConversationService
        enhanced_conversation = EnhancedConversationService(
            db=self.db,
            llm_client=llm_client
        )
        
        # 8. 获取Agent配置的温度和最大Token数
        agent_config = agent.config or {}
        final_temperature = temperature if temperature is not None else agent_config.get("temperature", 0.7)
        final_max_tokens = max_tokens if max_tokens is not None else agent_config.get("maxTokens", 2048)
        
        # 9. 调用EnhancedConversationService.chat（处理算力扣除、内容审查、流式响应）
        # system_prompt包含IP人设和Agent能力（不包含用户输入）
        # message是用户输入
        async for chunk in enhanced_conversation.chat(
            user_id=user_id,
            message=prompt_result.user_message,  # 用户输入
            model_id=llm_model.id,
            system_prompt=prompt_result.system_prompt,  # IP人设 + Agent能力
            conversation_id=conversation_id,
            temperature=final_temperature,
            max_tokens=final_max_tokens
        ):
            yield chunk
        
        # 10. 增加Agent使用次数
        try:
            await AgentServiceV2.increment_usage_count(self.db, agent_id)
        except Exception as e:
            logger.warning(f"更新Agent使用次数失败: {e}")
    
    async def execute_non_stream(
        self,
        agent_id: int,
        user_id: int,
        project_id: int,
        input_text: str,
        enable_persona: bool = True,
        conversation_id: Optional[int] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> dict:
        """
        执行Agent（非流式响应）
        
        Args:
            参数同execute方法（已移除routing_llm_model_id，LLM模型从router_agent.model字段读取）
        
        Returns:
            {
                "response": str,  # AI回复
                "prompt_used": str,  # 使用的Prompt
                "skills_applied": List[int],  # 使用的技能ID列表
                "token_count": int  # Token数量
            }
        """
        # 1-4步与execute方法相同
        result = await self.db.execute(
            select(Agent).filter(Agent.id == agent_id)
        )
        agent = result.scalar_one_or_none()
        if not agent:
            raise NotFoundException(msg="Agent不存在")
        
        if agent.status != 1:
            raise BadRequestException(msg="Agent未上架")
        
        # 获取IP基因
        persona_prompt = None
        if enable_persona:
            result = await self.db.execute(
                select(Project).filter(
                    Project.id == project_id,
                    Project.user_id == user_id,
                    Project.is_deleted == False,
                )
            )
            project = result.scalar_one_or_none()
            
            if project and project.persona_settings:
                persona_prompt = PromptBuilder.extract_persona_prompt(
                    project.persona_settings
                )
        
        # 路由决策（LLM模型从router_agent.model字段读取）
        routing_result = await self.master_router.route(
            db=self.db,
            agent=agent,
            user_input=input_text
        )
        
        # 组装Prompt
        prompt_result = await self.prompt_engine.assemble_prompt(
            db=self.db,
            agent=agent,
            selected_skill_ids=routing_result.selected_skill_ids,
            skill_variables=agent.skill_variables or {},
            persona_prompt=persona_prompt,
            user_input=input_text
        )
        
        # 解析模型
        llm_model = await self._resolve_llm_model(agent.model)
        if not llm_model:
            raise BadRequestException(
                msg=f"Agent配置的模型 '{agent.model}' 不存在或未启用"
            )
        
        # 创建LLM客户端
        llm_client = await LLMFactory.create_from_db(self.db, llm_model.id)
        
        # 创建EnhancedConversationService
        enhanced_conversation = EnhancedConversationService(
            db=self.db,
            llm_client=llm_client
        )
        
        # 获取配置
        agent_config = agent.config or {}
        final_temperature = temperature if temperature is not None else agent_config.get("temperature", 0.7)
        final_max_tokens = max_tokens if max_tokens is not None else agent_config.get("maxTokens", 2048)
        
        # 调用非流式方法
        result = await enhanced_conversation.chat_non_stream(
            user_id=user_id,
            message=input_text,
            model_id=llm_model.id,
            system_prompt=prompt_result.system_prompt,
            conversation_id=conversation_id,
            temperature=final_temperature,
            max_tokens=final_max_tokens
        )
        
        # 增加使用次数
        try:
            await AgentServiceV2.increment_usage_count(self.db, agent_id)
        except Exception as e:
            logger.warning(f"更新Agent使用次数失败: {e}")
        
        return {
            "response": result["response"],
            "prompt_used": prompt_result.system_prompt,
            "skills_applied": prompt_result.skills_applied,
            "token_count": prompt_result.token_count
        }
    
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

