"""
Client Content Generation Endpoints
C端内容生成接口（小程序 & PC官网）
支持智能体列表查询、对话式内容生成、快速生成等功能
"""
import json
import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from db import get_db
from models.user import User
from core.deps import get_current_miniprogram_user
from services.project import ProjectService
from services.llm_service import LLMFactory
from services.llm_model import LLMModelService
from services.agent import AgentService
from services.conversation import ConversationService
from services.ai import AIService
from services.coin_account import CoinAccountService
from services.coin_calculator import CoinCalculatorService
from middleware.balance_checker import BalanceCheckerMiddleware
from constants.agent import get_agent_config, get_all_agents, AgentType, AGENT_CONFIGS
from utils.response import success
from utils.exceptions import BadRequestException, ServerErrorException, NotFoundException
from loguru import logger
from core.config import settings

router = APIRouter()


# ============== 后台任务函数 ==============

async def embed_conversation_background_task(
    conversation_id: int,
    user_message_id: int,
    assistant_message_id: int
):
    """
    后台任务：向量化对话片段

    Args:
        conversation_id: 会话ID
        user_message_id: 用户消息ID
        assistant_message_id: AI回复消息ID
    """
    from db.session import async_session_maker
    from services.conversation import ConversationService

    try:
        async with async_session_maker() as db:
            service = ConversationService(db)
            await service.embed_conversation_async(
                conversation_id=conversation_id,
                user_message_id=user_message_id,
                assistant_message_id=assistant_message_id
            )
            logger.info(f"向量化完成: 会话{conversation_id}, 消息{user_message_id}-{assistant_message_id}")
    except Exception as e:
        logger.error(f"向量化失败: 会话{conversation_id}, 错误: {e}")
        # 不抛出异常，避免影响主流程


async def save_conversation_background_task(
    conversation_id: int,
    user_message: str,
    assistant_message: str,
    user_tokens: int = 0,
    assistant_tokens: int = 0
):
    """
    后台任务：保存对话消息到数据库并触发向量化

    Args:
        conversation_id: 会话ID
        user_message: 用户消息内容
        assistant_message: AI回复内容
        user_tokens: 用户消息token数
        assistant_tokens: AI回复token数
    """
    from db.session import async_session_maker
    from services.conversation import ConversationService
    from sqlalchemy import select, desc
    from models.conversation import ConversationMessage

    try:
        # 1. 保存对话消息
        async with async_session_maker() as db:
            service = ConversationService(db)
            await service.save_conversation_async(
                conversation_id=conversation_id,
                user_message=user_message,
                assistant_message=assistant_message,
                user_tokens=user_tokens,
                assistant_tokens=assistant_tokens
            )

        # 2. 获取刚保存的消息ID并触发向量化
        async with async_session_maker() as db:
            # 查询最新的两条消息（user + assistant）
            query = select(ConversationMessage).where(
                ConversationMessage.conversation_id == conversation_id
            ).order_by(desc(ConversationMessage.sequence)).limit(2)

            result = await db.execute(query)
            messages = list(result.scalars().all())

            if len(messages) == 2:
                # messages[0]是assistant, messages[1]是user（降序）
                assistant_msg = messages[0]
                user_msg = messages[1]

                # 触发向量化任务
                await embed_conversation_background_task(
                    conversation_id=conversation_id,
                    user_message_id=user_msg.id,
                    assistant_message_id=assistant_msg.id
                )
            else:
                logger.warning(f"无法找到消息进行向量化: 会话{conversation_id}")

    except Exception as e:
        logger.error(f"后台任务失败: 会话{conversation_id}, 错误: {e}")
        # 不抛出异常，避免影响主流程


# ============== Request/Response Models ==============

class ChatMessage(BaseModel):
    """对话消息模型"""
    role: str = Field(..., description="消息角色: 'user' 或 'assistant'")
    content: str = Field(..., description="消息内容")


class ChatRequest(BaseModel):
    """对话式创作请求模型"""
    conversation_id: Optional[int] = Field(default=None, description="会话ID（可选，如果不存在则创建新会话）")
    project_id: Optional[int] = Field(default=None, description="项目ID，用于获取IP人设信息")
    agent_type: str = Field(default=AgentType.EFFICIENT_ORAL, description="智能体类型")
    messages: List[ChatMessage] = Field(..., description="对话历史消息列表")
    model_type: Optional[str] = Field(default=None, description="LLM模型类型（可选，不传则使用智能体配置的模型）")
    temperature: Optional[float] = Field(default=None, ge=0.0, le=2.0, description="生成温度")
    max_tokens: int = Field(default=2048, ge=1, le=8192, description="最大生成tokens")
    stream: bool = Field(default=True, description="是否启用流式输出")


class ChatResponse(BaseModel):
    """对话响应模型（非流式）"""
    success: bool = True
    content: str = Field(..., description="生成的内容")
    agent_type: str = Field(..., description="使用的智能体类型")
    model_type: str = Field(..., description="使用的模型类型")


class AgentInfo(BaseModel):
    """智能体信息模型"""
    type: str  # 智能体类型标识，用于映射到后端的 agent_type
    id: str  # 智能体ID（字符串格式）
    name: str
    icon: str
    description: str


class AgentListResponse(BaseModel):
    """智能体列表响应"""
    success: bool = True
    agents: List[AgentInfo]


# ============== Helper Functions ==============

def build_ip_persona_prompt(project) -> str:
    """从项目信息构建IP人设提示词"""
    if not project:
        return ""
    
    persona = project.get_persona_settings_dict()
    parts = []
    
    parts.append(f"【IP信息】")
    parts.append(f"- IP名称：{project.name}")
    parts.append(f"- 所属赛道：{project.industry}")
    
    if persona.get("introduction"):
        parts.append(f"- IP简介：{persona['introduction']}")
    
    if persona.get("tone"):
        parts.append(f"- 语气风格：{persona['tone']}")
    
    if persona.get("target_audience"):
        parts.append(f"- 目标受众：{persona['target_audience']}")
    
    if persona.get("content_style"):
        parts.append(f"- 内容风格：{persona['content_style']}")
    
    if persona.get("catchphrase"):
        parts.append(f"- 常用口头禅：{persona['catchphrase']}")
    
    if persona.get("keywords"):
        parts.append(f"- 常用关键词：{', '.join(persona['keywords'])}")
    
    if persona.get("taboos"):
        parts.append(f"- 内容禁忌：{', '.join(persona['taboos'])}")
    
    if persona.get("benchmark_accounts"):
        parts.append(f"- 对标账号：{', '.join(persona['benchmark_accounts'])}")
    
    return "\n".join(parts)


def build_final_system_prompt(agent_system_prompt: str, ip_persona_prompt: str) -> str:
    """融合智能体人设和IP画像，构建最终的System Prompt"""
    parts = [agent_system_prompt]
    
    if ip_persona_prompt:
        parts.append("\n\n" + "=" * 40)
        parts.append("\n在创作时，请严格遵循以下IP人设设定，确保内容符合该IP的风格特点：\n")
        parts.append(ip_persona_prompt)
        parts.append("\n" + "=" * 40)
        parts.append("\n请在保持智能体专业能力的同时，融入以上IP的人设特点进行创作。")
    
    return "".join(parts)


def format_messages_for_llm(messages: List[ChatMessage]) -> str:
    """将消息列表格式化为用于LLM的prompt"""
    for msg in reversed(messages):
        if msg.role == "user":
            return msg.content
    
    return messages[-1].content if messages else ""


def build_conversation_context(messages: List[ChatMessage]) -> str:
    """构建对话上下文，用于多轮对话"""
    if len(messages) <= 1:
        return ""
    
    history = messages[:-1]
    if not history:
        return ""
    
    context_parts = ["\n【对话历史】"]
    for msg in history[-6:]:
        role_name = "用户" if msg.role == "user" else "助手"
        context_parts.append(f"{role_name}：{msg.content}")
    
    context_parts.append("\n请基于以上对话历史，继续回复用户的最新请求。")
    
    return "\n".join(context_parts)


# ============== API Endpoints ==============

@router.get("/agents")
async def list_agents(
    db: AsyncSession = Depends(get_db)
):
    """获取所有可用的智能体列表（从数据库读取）"""
    # 从数据库查询启用的智能体
    from sqlalchemy import select, and_
    from models.agent import Agent
    
    result = await db.execute(
        select(Agent).where(
            Agent.status == 1  # 只返回上架的智能体
        ).order_by(Agent.sort_order, Agent.created_at)
    )
    db_agents = result.scalars().all()
    
    # 转换为前端需要的格式，确保 id 为 number 类型
    agents = []
    for agent in db_agents:
        # 如果数据库中有 type 字段，使用 agent.type；否则使用 agent.id
        agent_type = str(agent.id)  # 暂时使用 ID 作为 type
        
        # 尝试从 config 中获取 type（如果之前有存储）
        if agent.config and isinstance(agent.config, dict) and "type" in agent.config:
            agent_type = agent.config["type"]
        
        agents.append({
            "type": agent_type,
            "id": agent.id,  # 统一为 number 类型
            "name": agent.name,
            "icon": agent.icon,
            "description": agent.description or ""
        })
    
    return success(data={"agents": agents}, msg="获取成功")


@router.post("/chat")
async def generate_chat(
    request: ChatRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_miniprogram_user),
    db: AsyncSession = Depends(get_db)
):
    """对话式创作接口（支持向量检索和异步保存）"""
    try:
        # 0. 初始化会话服务
        conversation_service = ConversationService(db)

        # 0.1. 获取智能体配置和模型类型（提前获取，避免重复查询）
        agent_config = None
        agent_type_source = "preset"
        db_agent = None
        agent_model_type = request.model_type or "doubao"  # 默认值

        try:
            agent_config = get_agent_config(request.agent_type)
        except ValueError:
            # 如果预设配置中找不到，尝试从数据库查询（可能是数据库ID）
            try:
                agent_id = int(request.agent_type)
                from sqlalchemy import select
                from models.agent import Agent

                result = await db.execute(
                    select(Agent).where(
                        Agent.id == agent_id,
                        Agent.status == 1  # 只查询上架的智能体
                    )
                )
                db_agent = result.scalar_one_or_none()

                if db_agent:
                    # 从数据库智能体构建配置
                    agent_config = {
                        "system_prompt": db_agent.system_prompt,
                        "temperature": db_agent.config.get("temperature", 0.7) if db_agent.config else 0.7,
                        "max_tokens": db_agent.config.get("max_tokens", 2048) if db_agent.config else 2048,
                    }
                    agent_type_source = "database"
                    # 使用数据库智能体配置的模型
                    agent_model_type = db_agent.model
                    logger.info(f"📊 [DEBUG] 使用数据库智能体配置的模型: {agent_model_type}")
                else:
                    available = ", ".join(AGENT_CONFIGS.keys())
                    raise BadRequestException(f"智能体 ID '{agent_id}' 不存在或已下架。可用类型: {available}")
            except ValueError:
                # agent_type 不是数字，也不是预设枚举值
                available = ", ".join(AGENT_CONFIGS.keys())
                raise BadRequestException(f"未知的智能体类型: '{request.agent_type}'。可用类型: {available}")

        if not agent_config:
            available = ", ".join(AGENT_CONFIGS.keys())
            raise BadRequestException(f"无法获取智能体配置: '{request.agent_type}'。可用类型: {available}")

        # 如果是预设智能体且没有提供model_type，使用默认值
        if agent_type_source == "preset" and not request.model_type:
            agent_model_type = "doubao"
            logger.info(f"📊 [DEBUG] 使用默认模型: {agent_model_type}")

        # 0.2. 不再验证模型类型，所有模型信息从数据库读取
        # 这样可以支持动态添加新模型，无需修改代码
        logger.info(f"📊 [DEBUG] 使用模型类型: {agent_model_type} (来源: {agent_type_source})")

        # 0.1. 处理会话ID（如果不存在则创建新会话）
        conversation_id = request.conversation_id
        if not conversation_id:
            from schemas.conversation import ConversationCreate
            from sqlalchemy import select
            from models.agent import Agent
            
            # 获取智能体名称用于生成会话标题
            agent_name = "新对话"
            agent_id = None
            if request.agent_type.isdigit():
                agent_id = int(request.agent_type)
                result = await db.execute(
                    select(Agent).where(Agent.id == agent_id)
                )
                db_agent = result.scalar_one_or_none()
                if db_agent:
                    agent_name = db_agent.name
            
            # 获取用户的第一句话（截取前30个字符）
            first_message = ""
            for msg in request.messages:
                if msg.role == "user" and msg.content:
                    first_message = msg.content[:30]
                    if len(msg.content) > 30:
                        first_message += "..."
                    break
            
            # 生成会话标题：智能体名称 + 用户第一句话
            title = f"{agent_name}: {first_message}" if first_message else agent_name
            
            conversation_data = ConversationCreate(
                agent_id=agent_id,
                project_id=request.project_id,
                model_type=agent_model_type,
                title=title,
            )
            conversation = await conversation_service.create_conversation(
                user_id=current_user.id,
                conversation_data=conversation_data
            )
            conversation_id = conversation.id
        else:
            # 验证会话是否属于当前用户
            try:
                await conversation_service.get_conversation_by_id(
                    conversation_id=conversation_id,
                    user_id=current_user.id
                )
            except NotFoundException:
                # 如果会话不存在，创建新会话（可能是前端存储了已删除的会话ID）
                from schemas.conversation import ConversationCreate
                from sqlalchemy import select
                from models.agent import Agent

                logger.warning(f"会话 {conversation_id} 不存在，自动创建新会话（用户ID: {current_user.id}）")
                
                # 获取智能体名称用于生成会话标题
                agent_name = "新对话"
                agent_id = None
                if request.agent_type.isdigit():
                    agent_id = int(request.agent_type)
                    result = await db.execute(
                        select(Agent).where(Agent.id == agent_id)
                    )
                    db_agent = result.scalar_one_or_none()
                    if db_agent:
                        agent_name = db_agent.name
                
                # 获取用户的第一句话（截取前30个字符）
                first_message = ""
                for msg in request.messages:
                    if msg.role == "user" and msg.content:
                        first_message = msg.content[:30]
                        if len(msg.content) > 30:
                            first_message += "..."
                        break
                
                # 生成会话标题：智能体名称 + 用户第一句话
                title = f"{agent_name}: {first_message}" if first_message else agent_name

                conversation_data = ConversationCreate(
                    agent_id=agent_id,
                    project_id=request.project_id,
                    model_type=agent_model_type,
                    title=title,
                )
                conversation = await conversation_service.create_conversation(
                    user_id=current_user.id,
                    conversation_data=conversation_data
                )
                conversation_id = conversation.id
            except Exception as e:
                # 其他错误正常抛出
                raise

        # 1. 获取项目IP画像（如果提供了project_id）
        ip_persona_prompt = ""
        if request.project_id:
            project_service = ProjectService(db)
            project = await project_service.get_project_by_id(request.project_id, user_id=current_user.id)
            if project:
                ip_persona_prompt = build_ip_persona_prompt(project)

        # 2. 获取用户最新消息作为prompt
        user_prompt = format_messages_for_llm(request.messages)
        
        if not user_prompt:
            raise BadRequestException("消息列表不能为空")
        
        # 5. 向量检索：搜索相关历史片段
        # ⚠️ 临时禁用向量检索以提升性能（待后端向量化功能修复后重新启用）
        # TODO: 修复向量化后台任务后重新启用此功能
        relevant_chunks = []
        optimized_messages = request.messages  # 默认使用原始消息

        # 禁用向量检索代码 - 节省200-500ms响应时间
        # try:
        #     # 对用户新消息进行向量化并搜索相关片段
        #     relevant_chunks = await conversation_service.search_relevant_chunks(
        #         conversation_id=conversation_id,
        #         query_text=user_prompt,
        #         top_k=5,
        #         threshold=0.7
        #     )
        #
        #     # 如果找到了相关片段，使用优化的消息上下文
        #     if relevant_chunks:
        #         optimized_messages = await conversation_service.build_context_from_search(
        #             conversation_id=conversation_id,
        #             query_text=user_prompt,
        #             relevant_chunks=relevant_chunks,
        #             include_recent=2  # 包含最近2轮对话
        #         )
        # except Exception as e:
        #     # 向量检索失败，回退到原始消息
        #     from loguru import logger
        #     logger.warning(f"向量检索失败，使用原始消息: {e}")
        
        # 6. 构建最终System Prompt（使用优化后的消息或原始消息构建上下文）
        base_system_prompt = agent_config["system_prompt"]
        
        # 如果有优化的消息，构建上下文
        if relevant_chunks:
            # 使用优化后的消息构建上下文（只包含相关片段和最近消息）
            conversation_context = ""
        else:
            # 回退到原始逻辑：使用全部消息构建上下文
            conversation_context = build_conversation_context(optimized_messages)
        
        final_system_prompt = build_final_system_prompt(
            agent_system_prompt=base_system_prompt + conversation_context,
            ip_persona_prompt=ip_persona_prompt,
        )

        # 🔍 检查并限制 system prompt 长度
        MAX_SYSTEM_PROMPT_LENGTH = 8000  # 根据模型限制调整
        original_length = len(final_system_prompt)
        if original_length > MAX_SYSTEM_PROMPT_LENGTH:
            logger.warning(f"⚠️ [DEBUG] System prompt too long ({original_length} chars), truncating to {MAX_SYSTEM_PROMPT_LENGTH} chars")
            logger.warning(f"  - Base agent prompt length: {len(base_system_prompt)} chars")
            logger.warning(f"  - Conversation context length: {len(conversation_context)} chars")
            logger.warning(f"  - IP persona prompt length: {len(ip_persona_prompt)} chars")

            # 智能截断策略: 保留智能体核心prompt,精简历史和IP信息
            # 1. 先保留完整的智能体prompt
            truncated_prompt = base_system_prompt

            # 2. 如果还有空间,添加IP人设的关键部分
            remaining_space = MAX_SYSTEM_PROMPT_LENGTH - len(truncated_prompt) - 100  # 留100字符buffer
            if remaining_space > 0 and ip_persona_prompt:
                # 只保留IP人设的前N个字符
                ip_persona_truncated = ip_persona_prompt[:remaining_space]
                truncated_prompt = build_final_system_prompt(
                    agent_system_prompt=truncated_prompt,
                    ip_persona_prompt=ip_persona_truncated
                )

            # 3. 如果还没到限制,添加对话历史(最多2轮)
            if len(truncated_prompt) < MAX_SYSTEM_PROMPT_LENGTH * 0.8 and conversation_context:
                # 简化对话历史:只保留最近2轮
                simplified_context = "\n【最近对话】" + "\n".join(conversation_context.split("\n")[-6:])
                final_system_prompt = truncated_prompt + "\n\n" + simplified_context
            else:
                final_system_prompt = truncated_prompt

            logger.warning(f"  - After truncation: {len(final_system_prompt)} chars")
        else:
            logger.info(f"✅ [DEBUG] System prompt length OK: {original_length} chars")

        # 如果使用优化后的消息，需要重新格式化user_prompt
        if relevant_chunks:
            # 从优化的消息中提取用户消息（最后一条user消息）
            user_prompt = user_prompt  # 保持原样，因为已经在optimized_messages的最后
        
        # 7. 确定生成参数
        temperature = request.temperature if request.temperature is not None else agent_config.get("temperature", 0.7)
        max_tokens = request.max_tokens or agent_config.get("max_tokens", 2048)
        
        # 8. 从��据库获取模型配置
        # 直接通过 model_type (或 model_id) 查询数据库中的模型配置
        # 支持两种查询方式:
        # 1. 通过 provider 字段查询 (兼容旧的 model_type 如 "deepseek", "doubao")
        # 2. 通过 model_id 字段查询 (支持数据库中存储的模型ID)
        from sqlalchemy import select, and_, or_
        from models.llm_model import LLMModel

        logger.info(f"🔍 [DEBUG] Querying model configuration:")
        logger.info(f"  - Requested model_type: {agent_model_type}")

        # 尝试通过 provider 或 model_id 查询
        result = await db.execute(
            select(LLMModel).where(
                and_(
                    or_(
                        LLMModel.provider == agent_model_type.lower(),
                        LLMModel.model_id == agent_model_type,
                        LLMModel.id == int(agent_model_type) if agent_model_type.isdigit() else False
                    ),
                    LLMModel.is_enabled == True
                )
            ).order_by(LLMModel.sort_order).limit(1)
        )
        llm_model = result.scalar_one_or_none()

        if not llm_model:
            # 🔍 详细错误日志: 查询失败的原因
            logger.error(f"❌ [DEBUG] Model not found in database:")
            logger.error(f"  - Requested model_type: {agent_model_type}")

            # 查询所有启用的模型,帮助调试
            all_enabled = await db.execute(
                select(LLMModel).where(LLMModel.is_enabled == True)
            )
            enabled_models = all_enabled.scalars().all()
            logger.error(f"  - All enabled models in database:")
            for m in enabled_models:
                logger.error(f"    * {m.name} (id={m.id}, provider={m.provider}, model_id={m.model_id}, enabled={m.is_enabled})")

            raise BadRequestException(
                f"未找到启用的模型 '{agent_model_type}'，请在管理后台配置模型"
            )

        logger.info(f"✅ [DEBUG] Model found: {llm_model.name} (id={llm_model.id}, provider={llm_model.provider})")

        if not llm_model.api_key:
            raise BadRequestException(f"模型 {llm_model.name} 未配置 API Key，请在管理后台配置")

        # 8.5 算力预冻结（在AI调用前）
        task_id = str(uuid.uuid4())
        balance_checker = BalanceCheckerMiddleware(db)
        estimated_output_tokens = request.max_tokens or 2048

        try:
            # 获取用户输入文本用于估算
            user_input_text = user_prompt  # 使用用户提示词

            freeze_info = await balance_checker.check_and_freeze(
                user_id=current_user.id,
                model_id=llm_model.id,
                input_text=user_input_text,
                task_id=task_id,
                estimated_output_tokens=estimated_output_tokens
            )
            logger.info(f"💰 [DEBUG] 算力预冻结成功: 用户ID={current_user.id}, 金额={freeze_info['frozen_amount']}, 任务ID={task_id}")
        except BadRequestException as e:
            # 余额不足，直接返回错误
            logger.warning(f"❌ [DEBUG] 用户余额不足: {str(e)}")
            raise
        except Exception as e:
            # 预冻结失败，记录警告但不阻止请求（降级处理）
            logger.warning(f"⚠️ [DEBUG] 算力预冻结失败（降级处理）: {str(e)}")
            task_id = None  # 标记为未预冻结，跳过结算

        # 9. 构建 messages 列表（与 AIService 兼容的格式）
        # 将 final_system_prompt 和 user_prompt 转换为 messages 格式
        messages_for_ai = []

        # 🔍 智能处理长system prompt: 确保完整prompt始终发送,避免网关503错误
        # 策略: 将完整system prompt融入user消息,避免system字段过长导致网关503

        if len(final_system_prompt) > 1500:
            # System prompt较长,使用user消息策略(避免system字段过长)
            logger.info(f"📊 [DEBUG] System prompt较长({len(final_system_prompt)} chars),使用user消息策略:")
            logger.info(f"  - 将system prompt融入user消息中")
            logger.info(f"  - 保持user-assistant交替的格式规范")

            # 判断是否首次对话
            is_first_message = len(request.messages) <= 2

            if is_first_message:
                # 首次对话: 将完整system prompt + 用户问题作为user消息
                logger.info(f"  - 首次对话: 完整prompt({len(final_system_prompt)} chars) + 用户问题")
                combined_message = f"{final_system_prompt}\n\n【用户问题】\n{user_prompt}"

                messages_for_ai = [
                    {
                        "role": "user",
                        "content": combined_message
                    }
                ]
            else:
                # 后续对话: 将system prompt融入当前user消息,保持user-assistant交替格式
                logger.info(f"  - 后续对话: 融合prompt({len(final_system_prompt)} chars) + 当前问题")
                logger.info(f"  - 保持user-assistant交替的格式规范,避免网关503错误")

                # 按照user-assistant交替的规则构建消息列表
                for i, msg in enumerate(request.messages):
                    if msg.role == "user":
                        # 判断是否是最后一条user消息(当前问题)
                        is_last_user = True
                        for j in range(i + 1, len(request.messages)):
                            if request.messages[j].role == "user":
                                is_last_user = False
                                break

                        if is_last_user:
                            # 最后一条user消息: 融合system prompt
                            enhanced_content = f"{final_system_prompt}\n\n【用户问题】\n{msg.content}"
                            messages_for_ai.append({
                                "role": "user",
                                "content": enhanced_content
                            })
                        else:
                            # 历史user消息: 保持原样
                            messages_for_ai.append({
                                "role": msg.role,
                                "content": msg.content
                            })
                    else:
                        # assistant消息: 保持原样
                        messages_for_ai.append({
                            "role": msg.role,
                            "content": msg.content
                        })
        else:
            # System prompt长度适中,使用标准格式(带缓存)
            logger.info(f"✅ [DEBUG] System prompt长度适中({len(final_system_prompt)} chars),使用标准格式(带缓存)")

            if final_system_prompt:
                messages_for_ai.append({
                    "role": "system",
                    "content": final_system_prompt
                })
            messages_for_ai.append({
                "role": "user",
                "content": user_prompt
            })
        
        # 10. 使用 AIService（与 admin/ai 保持一致，避免差异）
        ai_service = AIService(db)

        # 查找模型 ID（使用数据库中的模型 ID）
        model_id_for_ai = str(llm_model.id)  # 使用数据库 ID 作为模型标识

        # 🔍 调试日志: 打印关键信息
        # 计算请求体大小(估算)
        import json
        request_body_size = len(json.dumps({"model": model_id_for_ai, "messages": messages_for_ai}).encode('utf-8'))

        logger.info(f"📊 [DEBUG] Chat Request Info:")
        logger.info(f"  - Conversation ID: {conversation_id}")
        logger.info(f"  - User ID: {current_user.id}")
        logger.info(f"  - Agent Type: {request.agent_type}")
        logger.info(f"  - Model Type: {agent_model_type}")
        logger.info(f"  - Provider: {llm_model.provider}")
        logger.info(f"  - Model ID for AI: {model_id_for_ai}")
        logger.info(f"  - DB Model: {llm_model.name} (model_id={llm_model.model_id})")
        logger.info(f"  - Base URL: {llm_model.base_url}")
        logger.info(f"  - System Prompt Length: {len(final_system_prompt)} chars")
        logger.info(f"  - User Prompt Length: {len(user_prompt)} chars")
        logger.info(f"  - Messages Count: {len(messages_for_ai)}")
        logger.info(f"  - Estimated Request Body Size: {request_body_size} bytes")
        logger.info(f"  - Temperature: {temperature}, Max Tokens: {max_tokens}")
        logger.info(f"  - Stream: {request.stream}")

        # 打印实际发送的消息结构(用于调试503问题)
        logger.info(f"📋 [DEBUG] Messages Structure:")
        for i, msg in enumerate(messages_for_ai):
            role = msg.get('role', 'unknown')
            content = msg.get('content', '')
            content_preview = content[:100] + '...' if len(content) > 100 else content
            # 检查是否有特殊字符
            has_special_chars = any(ord(c) > 127 for c in content)
            logger.info(f"  - Message {i+1}: role={role}, length={len(content)}, has_special_chars={has_special_chars}")
            logger.info(f"    Preview: {content_preview}")

            # 如果有特殊字符,打印一些示例
            if has_special_chars:
                special_chars = [c for c in content if ord(c) > 127][:10]
                logger.warning(f"    ⚠️ Special chars found: {special_chars}")

        # 检查请求体大小是否超过安全阈值
        MAX_REQUEST_SIZE = 100000  # 100KB (大多数API网关的限制是1-10MB)
        if request_body_size > MAX_REQUEST_SIZE:
            logger.warning(f"⚠️ [WARNING] Request body size ({request_body_size} bytes) exceeds safe threshold ({MAX_REQUEST_SIZE} bytes)")
            logger.warning(f"  This may cause API gateway 503 errors or timeouts")
            logger.warning(f"  Consider: 1) Reducing system prompt length, 2) Limiting conversation history")
        
        # 11. 生成响应
        assistant_content = ""  # 用于后台任务保存

        if request.stream:
            # 流式响应
            async def generate_stream():
                nonlocal assistant_content
                try:
                    # 首先发送 conversation_id（让前端能够更新会话ID）
                    yield f"data: {json.dumps({'conversation_id': conversation_id}, ensure_ascii=False)}\n\n"
                    logger.info(f"📤 [DEBUG] Starting stream generation for conversation {conversation_id}")

                    # 使用 AIService.stream_chat（与 admin/ai 保持一致）
                    chunk_count = 0
                    async for chunk_json in ai_service.stream_chat(
                        messages=messages_for_ai,
                        model=model_id_for_ai,
                        temperature=temperature,
                        max_tokens=max_tokens,
                        top_p=1.0,
                        frequency_penalty=0.0,
                        presence_penalty=0.0
                    ):
                        chunk_count += 1
                        if chunk_count == 1:
                            logger.info(f"✅ [DEBUG] Received first chunk from AI service")

                        # AIService.stream_chat 返回的是 JSON 字符串，需要解析
                        try:
                            chunk_data = json.loads(chunk_json)
                            # 检查是否有错误
                            if "error" in chunk_data:
                                # 如果是错误，直接传递
                                logger.error(f"❌ [DEBUG] Received error from AI service: {chunk_data['error']}")
                                yield f"data: {chunk_json}\n\n"
                                return
                            # 提取 content（AIService 返回的格式）
                            delta = chunk_data.get("delta", {})
                            content = delta.get("content", "")
                            if content:
                                assistant_content += content
                                yield f"data: {json.dumps({'content': content}, ensure_ascii=False)}\n\n"
                        except json.JSONDecodeError:
                            # 如果不是 JSON（不应该发生，但为了安全），直接作为内容处理
                            assistant_content += chunk_json
                            yield f"data: {json.dumps({'content': chunk_json}, ensure_ascii=False)}\n\n"

                    logger.info(f"✅ [DEBUG] Stream generation completed. Total chunks: {chunk_count}, Content length: {len(assistant_content)}")
                    yield f"data: {json.dumps({'done': True}, ensure_ascii=False)}\n\n"

                    # 8.6 算力结算（在AI调用后）
                    if task_id:
                        logger.info(f"💰 [DEBUG] 开始算力结算流程，task_id={task_id}")
                        try:
                            # 估算实际token使用
                            calculator = CoinCalculatorService(db)
                            input_tokens = calculator.estimate_tokens_from_text(user_prompt)
                            output_tokens = calculator.estimate_tokens_from_text(assistant_content)

                            logger.info(f"💰 [DEBUG] Token估算完成: 输入={input_tokens}, 输出={output_tokens}")

                            # 计算实际消耗金额（注意参数顺序：input_tokens, output_tokens, model_id）
                            actual_cost = await calculator.calculate_cost(
                                input_tokens=input_tokens,
                                output_tokens=output_tokens,
                                model_id=llm_model.id
                            )

                            logger.info(f"💰 [DEBUG] 成本计算完成: {actual_cost} (类型: {type(actual_cost)})")

                            # 执行结算
                            await balance_checker.settle(
                                user_id=current_user.id,
                                task_id=task_id,
                                actual_cost=actual_cost,
                                input_tokens=input_tokens,
                                output_tokens=output_tokens,
                                model_id=llm_model.id,
                                is_error=False,
                                error_code=None
                            )
                            logger.info(f"💰 [DEBUG] 算力结算成功: 用户ID={current_user.id}, 输入Token={input_tokens}, 输出Token={output_tokens}, 结算金额={actual_cost}")
                        except Exception as e:
                            logger.error(f"❌ [DEBUG] 算力结算失败: {str(e)}")
                            import traceback
                            logger.error(f"❌ [DEBUG] 结算错误详情: {traceback.format_exc()}")
                            # 结算失败不影响对话，只记录错误

                    # 流式完成后，触发后台任务保存
                    background_tasks.add_task(
                        save_conversation_background_task,
                        conversation_id=conversation_id,
                        user_message=user_prompt,
                        assistant_message=assistant_content,
                        user_tokens=len(user_prompt) // 4,  # 粗略估算token数
                        assistant_tokens=len(assistant_content) // 4,
                    )

                except Exception as e:
                    # 🔍 详细错误日志
                    import traceback
                    logger.error(f"❌ [DEBUG] Stream generation failed:")
                    logger.error(f"  - Error Type: {type(e).__name__}")
                    logger.error(f"  - Error Message: {str(e)}")
                    logger.error(f"  - Conversation ID: {conversation_id}")
                    logger.error(f"  - User ID: {current_user.id}")
                    logger.error(f"  - Model ID: {model_id_for_ai}")
                    logger.error(f"  - Agent Type: {request.agent_type}")
                    logger.error(f"  - System Prompt Length: {len(final_system_prompt)} chars")
                    logger.error(f"  - User Prompt Length: {len(user_prompt)} chars")
                    logger.error(f"  - Temperature: {temperature}, Max Tokens: {max_tokens}")
                    logger.error(f"  - Traceback:\n{traceback.format_exc()}")

                    # 8.7 错误时退款预冻结的算力
                    if task_id:
                        try:
                            await balance_checker.settle(
                                user_id=current_user.id,
                                task_id=task_id,
                                actual_cost=0,  # 错误时实际消耗为0
                                input_tokens=0,
                                output_tokens=0,
                                model_id=llm_model.id,
                                is_error=True,
                                error_code="generation_error"
                            )
                            logger.info(f"💰 [DEBUG] 错误退款成功: 用户ID={current_user.id}, 任务ID={task_id}")
                        except Exception as refund_error:
                            logger.error(f"❌ [DEBUG] 错误退款失败: {str(refund_error)}")

                    error_msg = f"生成错误: {str(e)}"
                    yield f"data: {json.dumps({'error': error_msg}, ensure_ascii=False)}\n\n"
            
            return StreamingResponse(
                generate_stream(),
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "X-Accel-Buffering": "no",
                }
            )
        else:
            # 非流式响应
            result = await ai_service.chat(
                messages=messages_for_ai,
                model=model_id_for_ai,
                temperature=temperature,
                max_tokens=max_tokens,
                top_p=1.0,
                frequency_penalty=0.0,
                presence_penalty=0.0
            )
            assistant_content = result.get("message", {}).get("content", "")
            
            # 立即触发后台任务保存（不阻塞响应）
            background_tasks.add_task(
                save_conversation_background_task,
                conversation_id=conversation_id,
                user_message=user_prompt,
                assistant_message=assistant_content,
                user_tokens=len(user_prompt) // 4,
                assistant_tokens=len(assistant_content) // 4,
            )
            
            return ChatResponse(
                success=True,
                content=assistant_content,
                agent_type=request.agent_type,
                model_type=agent_model_type
            )
    
    except (BadRequestException, ServerErrorException):
        raise
    except Exception as e:
        # 🔍 捕获所有未处理的异常,记录详细日志
        import traceback
        logger.error(f"❌ [DEBUG] Chat endpoint unexpected error:")
        logger.error(f"  - Error Type: {type(e).__name__}")
        logger.error(f"  - Error Message: {str(e)}")
        logger.error(f"  - User ID: {current_user.id if 'current_user' in locals() else 'N/A'}")
        logger.error(f"  - Model Type: {agent_model_type if 'agent_model_type' in locals() else 'N/A'}")
        logger.error(f"  - Agent Type: {request.agent_type if 'request' in locals() else 'N/A'}")
        logger.error(f"  - Project ID: {request.project_id if 'request' in locals() else 'N/A'}")
        logger.error(f"  - Traceback:\n{traceback.format_exc()}")
        raise ServerErrorException(f"生成失败: {str(e)}")


@router.post("/chat/debug")
async def debug_chat(
    request: ChatRequest,
    current_user: User = Depends(get_current_miniprogram_user),
    db: AsyncSession = Depends(get_db)
):
    """
    调试版chat接口 - 返回详细信息但不调用AI

    用于排查503错误,展示:
    1. 模型配置查询结果
    2. 提示词构建过程和长度
    3. 消息格式
    4. 不会实际调用AI API
    """
    try:
        debug_info = {
            "request_params": {
                "model_type": request.model_type,
                "agent_type": request.agent_type,
                "project_id": request.project_id,
                "stream": request.stream,
                "temperature": request.temperature,
                "max_tokens": request.max_tokens,
                "messages_count": len(request.messages),
            },
            "step_results": {}
        }

        # 1. 验证模型类型
        supported_models = LLMFactory.get_supported_models()
        debug_info["step_results"]["model_type_check"] = {
            "is_supported": request.model_type.lower() in supported_models,
            "supported_models": supported_models
        }

        # 2. 获取智能体配置
        try:
            agent_config = get_agent_config(request.agent_type)
            debug_info["step_results"]["agent_config"] = {
                "found": True,
                "system_prompt_length": len(agent_config.get("system_prompt", "")),
                "temperature": agent_config.get("temperature"),
                "max_tokens": agent_config.get("max_tokens"),
            }
        except Exception as e:
            debug_info["step_results"]["agent_config"] = {
                "found": False,
                "error": str(e)
            }
            # 尝试从数据库查询
            try:
                agent_id = int(request.agent_type)
                from sqlalchemy import select
                from models.agent import Agent
                result = await db.execute(
                    select(Agent).where(Agent.id == agent_id)
                )
                db_agent = result.scalar_one_or_none()
                if db_agent:
                    debug_info["step_results"]["agent_config"] = {
                        "found": True,
                        "source": "database",
                        "agent_name": db_agent.name,
                        "system_prompt_length": len(db_agent.system_prompt),
                    }
            except:
                pass

        # 3. 查询模型配置
        model_type_to_provider = {
            "deepseek": "deepseek",
            "doubao": "doubao",
            "claude": "anthropic"
        }
        provider = model_type_to_provider.get(request.model_type.lower(), request.model_type.lower())
        debug_info["step_results"]["model_query"] = {
            "provider": provider,
            "provider_mapping": model_type_to_provider
        }

        from sqlalchemy import select, and_
        from models.llm_model import LLMModel
        result = await db.execute(
            select(LLMModel).where(
                and_(
                    LLMModel.provider == provider,
                    LLMModel.is_enabled == True
                )
            ).order_by(LLMModel.sort_order).limit(1)
        )
        llm_model = result.scalar_one_or_none()

        if llm_model:
            debug_info["step_results"]["model_query"]["found_model"] = {
                "id": llm_model.id,
                "name": llm_model.name,
                "model_id": llm_model.model_id,
                "provider": llm_model.provider,
                "base_url": llm_model.base_url,
                "has_api_key": bool(llm_model.api_key),
                "api_key_prefix": llm_model.api_key[:10] + "..." if llm_model.api_key else None,
                "is_enabled": llm_model.is_enabled,
            }
        else:
            debug_info["step_results"]["model_query"]["found_model"] = None
            # 查询所有启用的模型
            all_enabled = await db.execute(
                select(LLMModel).where(LLMModel.is_enabled == True)
            )
            enabled_models = all_enabled.scalars().all()
            debug_info["step_results"]["model_query"]["all_enabled_models"] = [
                {
                    "id": m.id,
                    "name": m.name,
                    "provider": m.provider,
                    "model_id": m.model_id,
                }
                for m in enabled_models
            ]

        # 4. 构建提示词(模拟真实流程但不调用AI)
        user_prompt = format_messages_for_llm(request.messages)
        debug_info["step_results"]["prompt_building"] = {
            "user_prompt_length": len(user_prompt),
            "user_prompt_preview": user_prompt[:200] + "..." if len(user_prompt) > 200 else user_prompt,
        }

        # 如果有项目ID,构建IP人设
        if request.project_id:
            try:
                project_service = ProjectService(db)
                project = await project_service.get_project_by_id(request.project_id, user_id=current_user.id)
                if project:
                    ip_persona_prompt = build_ip_persona_prompt(project)
                    debug_info["step_results"]["prompt_building"]["ip_persona_length"] = len(ip_persona_prompt)
                    debug_info["step_results"]["prompt_building"]["ip_persona_preview"] = ip_persona_prompt[:200] + "..." if len(ip_persona_prompt) > 200 else ip_persona_prompt
            except Exception as e:
                debug_info["step_results"]["prompt_building"]["ip_persona_error"] = str(e)

        # 构建对话上下文
        conversation_context = build_conversation_context(request.messages)
        debug_info["step_results"]["prompt_building"]["conversation_context_length"] = len(conversation_context)

        # 构建最终system prompt
        if "agent_config" in debug_info["step_results"] and debug_info["step_results"]["agent_config"].get("found"):
            base_system_prompt = debug_info["step_results"]["agent_config"].get("system_prompt", "")
            # 这里简化处理,只计算长度
            debug_info["step_results"]["prompt_building"]["estimated_system_prompt_length"] = (
                                len(base_system_prompt) +
                                len(conversation_context) +
                                debug_info["step_results"]["prompt_building"].get("ip_persona_length", 0)
            )

        return success(data=debug_info, msg="调试信息获取成功")

    except Exception as e:
        import traceback
        return success(
            data={
                "error": str(e),
                "traceback": traceback.format_exc(),
                "debug_info": debug_info if 'debug_info' in locals() else None
            },
            msg="调试接口发生错误"
        )


@router.post("/chat/quick")
async def quick_generate(
    content: str = Query(..., description="创作内容/主题"),
    agent_type: str = Query(default=AgentType.EFFICIENT_ORAL, description="智能体类型"),
    project_id: Optional[int] = Query(default=None, description="项目ID"),
    model_type: str = Query(default="deepseek", description="模型类型"),
    current_user: User = Depends(get_current_miniprogram_user),
    db: AsyncSession = Depends(get_db)
):
    """快速创作接口（简化版）"""
    request = ChatRequest(
        project_id=project_id,
        agent_type=agent_type,
        messages=[ChatMessage(role="user", content=content)],
        model_type=model_type,
        stream=False
    )
    
    return await generate_chat(request, current_user=current_user, db=db)

