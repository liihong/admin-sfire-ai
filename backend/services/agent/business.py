"""
Agent业务服务（业务逻辑层）
负责权限验证、余额检查、会话管理等业务逻辑
调用Agent核心执行器完成技术实现
"""
from typing import Optional, AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from loguru import logger

from models.agent import Agent
from models.project import Project
from services.agent.core import AgentExecutor
from services.agent.admin import AgentAdminService
from services.conversation.business import ConversationBusinessService
from services.conversation.enhanced import EnhancedConversationService
from services.shared.prompt_builder import PromptBuilder
from services.shared.llm_service import LLMFactory
from utils.exceptions import NotFoundException, BadRequestException, ForbiddenException
from utils.redis_lock import RedisLock
from models.conversation import MessageStatus


class AgentBusinessService:
    """
    Agent业务服务类
    
    职责说明：
    - 权限验证：验证用户是否有权限使用Agent、验证项目权限
    - 余额检查：通过EnhancedConversationService处理（内部包含余额检查）
    - 会话管理：创建和管理对话会话
    - 业务编排：调用Agent核心执行器完成技术实现
    - 统计更新：更新Agent使用次数
    
    依赖关系：
    - 依赖AgentExecutor（核心执行）
    - 依赖ConversationBusinessService（会话管理）
    - 依赖EnhancedConversationService（算力扣除、内容审查）
    - 依赖AgentAdminService（统计更新）
    
    使用示例：
        service = AgentBusinessService(db)
        async for chunk in service.execute_agent(
            agent_id=1,
            user_id=1,
            project_id=1,
            input_text="你好"
        ):
            print(chunk)
    """
    
    def __init__(self, db: AsyncSession):
        """
        初始化Agent业务服务
        
        Args:
            db: 异步数据库会话
        """
        self.db = db
        self.executor = AgentExecutor(db)
        self.conversation_service = ConversationBusinessService(db)
    
    async def execute_agent(
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
        执行Agent（完整业务流程，流式响应）
        
        业务逻辑流程：
        1. 验证Agent存在和状态
        2. 获取会话锁（如果conversation_id存在，防止并发请求）
        3. 验证项目权限（如果启用IP基因）
        4. 获取IP基因（如果启用）
        5. 创建/获取会话
        6. 调用Agent核心执行（通过EnhancedConversationService，处理算力扣除、内容审查）
        7. 更新Agent使用次数
        
        Args:
            agent_id: Agent ID
            user_id: 用户ID
            project_id: 项目ID
            input_text: 用户输入文本
            enable_persona: 是否启用IP基因注入，默认True
            conversation_id: 会话ID，如果为None则创建新会话
            temperature: 温度参数（可选，使用Agent配置的默认值）
            max_tokens: 最大Token数（可选，使用Agent配置的默认值）
        
        Yields:
            流式输出的文本块（str）
        
        Raises:
            NotFoundException: Agent不存在或未上架
            ForbiddenException: 用户无权限使用项目
            BadRequestException: 余额不足或输入无效
        """
        # 1. 验证Agent存在和状态
        agent = await self._get_and_verify_agent(agent_id)
        
        logger.info(f"执行Agent: {agent.name} (ID={agent_id}), 用户ID={user_id}")
        
        # 2. 获取会话锁（如果conversation_id存在，防止并发请求）
        lock_value = None
        if conversation_id:
            lock_value = await RedisLock.acquire_conversation_lock(conversation_id)
            if not lock_value:
                raise BadRequestException("该会话正在处理中，请稍后重试")
        
        try:
            # 3. 获取IP基因（如果启用，同时验证项目权限）
            persona_prompt = None
            if enable_persona:
                persona_prompt = await self._get_persona_prompt(user_id, project_id)
            
            # 4. 调用Agent核心执行器进行路由和Prompt组装
            # 注意：这里先调用executor获取prompt结果，然后通过EnhancedConversationService执行
            # 因为EnhancedConversationService处理算力扣除和内容审查
            
            # 4.1 路由决策和Prompt组装（纯技术，不涉及业务逻辑）
            from services.routing import MasterRouter, PromptEngine
            master_router = MasterRouter()
            prompt_engine = PromptEngine()
            
            routing_result = await master_router.route(
                db=self.db,
                agent=agent,
                user_input=input_text
            )
            
            prompt_result = await prompt_engine.assemble_prompt(
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
            
            # 4.2 解析LLM模型
            llm_model = await self.executor._resolve_llm_model(agent.model)
            if not llm_model:
                raise BadRequestException(
                    msg=f"Agent配置的模型 '{agent.model}' 不存在或未启用"
                )
            
            # 4.3 创建LLM客户端
            try:
                llm_client = await LLMFactory.create_from_db(self.db, llm_model.id)
            except Exception as e:
                logger.error(f"创建LLM客户端失败: {e}")
                raise BadRequestException(msg=f"创建LLM客户端失败: {str(e)}")
            
            # 4.4 创建EnhancedConversationService（处理算力扣除、内容审查）
            enhanced_conversation = EnhancedConversationService(
                db=self.db,
                llm_client=llm_client
            )
            
            # 4.5 获取配置参数
            agent_config = agent.config or {}
            final_temperature = temperature if temperature is not None else agent_config.get("temperature", 0.7)
            final_max_tokens = max_tokens if max_tokens is not None else agent_config.get("maxTokens", 2048)
            
            # 5. 调用EnhancedConversationService.chat（处理算力扣除、内容审查、流式响应）
            # system_prompt包含IP人设和Agent能力（不包含用户输入）
            # message是用户输入
            execution_successful = False
            try:
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
                # 流式响应正常完成
                execution_successful = True
            except Exception as e:
                # 流式响应过程中出现异常，记录日志但继续执行统计更新
                logger.error(f"Agent流式响应异常: Agent ID={agent_id}, 错误={e}")
                execution_successful = False
                raise  # 重新抛出异常，让外层处理
        
        finally:
            # 6. 更新Agent使用次数（在finally中执行，确保无论成功失败都会更新）
            # 注意：即使流式响应失败，也统计调用次数（因为已经消耗了资源）
            try:
                logger.info(f"开始更新Agent使用次数: Agent ID={agent_id}")
                result = await AgentAdminService.increment_usage_count(self.db, agent_id)
                if result:
                    logger.info(f"✅ Agent使用次数更新成功: Agent ID={agent_id}")
                else:
                    logger.warning(f"⚠️ Agent使用次数更新失败: Agent ID={agent_id} (返回False)")
            except Exception as e:
                logger.error(f"❌ 更新Agent使用次数异常: Agent ID={agent_id}, 错误={e}", exc_info=True)
            
            # 释放会话锁
            if conversation_id and lock_value:
                await RedisLock.release_conversation_lock(conversation_id, lock_value)
    
    async def execute_agent_non_stream(
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
        执行Agent（完整业务流程，非流式响应）
        
        Args:
            参数同execute_agent方法
        
        Returns:
            {
                "response": str,  # AI回复
                "prompt_used": str,  # 使用的Prompt
                "skills_applied": List[int],  # 使用的技能ID列表
                "token_count": int  # Token数量
            }
        """
        # 1. 验证Agent存在和状态
        agent = await self._get_and_verify_agent(agent_id)
        
        # 2. 获取IP基因（如果启用）
        persona_prompt = None
        if enable_persona:
            persona_prompt = await self._get_persona_prompt(user_id, project_id)
        
        # 3. 路由决策和Prompt组装
        from services.routing import MasterRouter, PromptEngine
        master_router = MasterRouter()
        prompt_engine = PromptEngine()
        
        routing_result = await master_router.route(
            db=self.db,
            agent=agent,
            user_input=input_text
        )
        
        prompt_result = await prompt_engine.assemble_prompt(
            db=self.db,
            agent=agent,
            selected_skill_ids=routing_result.selected_skill_ids,
            skill_variables=agent.skill_variables or {},
            persona_prompt=persona_prompt,
            user_input=input_text
        )
        
        # 4. 解析LLM模型
        llm_model = await self.executor._resolve_llm_model(agent.model)
        if not llm_model:
            raise BadRequestException(
                msg=f"Agent配置的模型 '{agent.model}' 不存在或未启用"
            )
        
        # 5. 创建LLM客户端
        llm_client = await LLMFactory.create_from_db(self.db, llm_model.id)
        
        # 6. 创建EnhancedConversationService
        enhanced_conversation = EnhancedConversationService(
            db=self.db,
            llm_client=llm_client
        )
        
        # 7. 获取配置参数
        agent_config = agent.config or {}
        final_temperature = temperature if temperature is not None else agent_config.get("temperature", 0.7)
        final_max_tokens = max_tokens if max_tokens is not None else agent_config.get("maxTokens", 2048)
        
        # 8. 调用非流式方法
        try:
            result = await enhanced_conversation.chat_non_stream(
                user_id=user_id,
                message=input_text,
                model_id=llm_model.id,
                system_prompt=prompt_result.system_prompt,
                conversation_id=conversation_id,
                temperature=final_temperature,
                max_tokens=final_max_tokens
            )
        except Exception as e:
            # 即使执行失败，也更新统计（因为已经消耗了资源）
            logger.error(f"Agent非流式执行异常: Agent ID={agent_id}, 错误={e}")
            raise
        
        # 9. 更新Agent使用次数
        try:
            logger.info(f"开始更新Agent使用次数: Agent ID={agent_id} (非流式)")
            increment_result = await AgentAdminService.increment_usage_count(self.db, agent_id)
            if increment_result:
                logger.info(f"✅ Agent使用次数更新成功: Agent ID={agent_id} (非流式)")
            else:
                logger.warning(f"⚠️ Agent使用次数更新失败: Agent ID={agent_id} (非流式, 返回False)")
        except Exception as e:
            logger.error(f"❌ 更新Agent使用次数异常: Agent ID={agent_id} (非流式), 错误={e}", exc_info=True)
        
        return {
            "response": result["response"],
            "prompt_used": prompt_result.system_prompt,
            "skills_applied": prompt_result.skills_applied,
            "token_count": prompt_result.token_count
        }
    
    async def _get_and_verify_agent(self, agent_id: int) -> Agent:
        """
        获取并验证Agent
        
        Args:
            agent_id: Agent ID
        
        Returns:
            Agent对象
        
        Raises:
            NotFoundException: Agent不存在
            BadRequestException: Agent未上架（系统自用智能体除外）
        
        注意：
            - 系统自用智能体（is_system=1）可以绕过上架检查，直接使用
            - 普通智能体（is_system=0）必须上架（status=1）才能使用
        """
        result = await self.db.execute(
            select(Agent).filter(Agent.id == agent_id)
        )
        agent = result.scalar_one_or_none()
        
        if not agent:
            raise NotFoundException(msg="Agent不存在")
        
        # 系统自用智能体可以绕过上架检查，普通智能体必须上架
        if agent.is_system == 0 and agent.status != 1:
            raise BadRequestException(msg="Agent未上架")
        
        return agent
    
    async def _get_persona_prompt(self, user_id: int, project_id: int) -> Optional[str]:
        """
        获取IP人设Prompt（同时验证项目权限）
        
        Args:
            user_id: 用户ID
            project_id: 项目ID
        
        Returns:
            IP人设Prompt，如果项目不存在或未配置则返回None
        
        Raises:
            ForbiddenException: 用户无权限访问该项目
        """
        result = await self.db.execute(
            select(Project).filter(
                Project.id == project_id,
                Project.user_id == user_id,
                Project.is_deleted == False,
            )
        )
        project = result.scalar_one_or_none()
        
        if not project:
            raise ForbiddenException(msg="项目不存在或无权访问")
        
        if project.persona_settings or project.master_prompt:
            persona_prompt = PromptBuilder.extract_persona_prompt(
                project.persona_settings or {},
                master_prompt=project.master_prompt
            )
            logger.debug(f"已注入IP基因: 项目={project.name}")
            return persona_prompt
        
        return None

