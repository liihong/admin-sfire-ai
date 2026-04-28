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
from core.deps import get_current_miniprogram_user, get_current_miniprogram_user_optional
from core.tenant_constants import DEFAULT_TENANT_ID
from services.resource import ProjectService
from services.shared.llm_service import LLMFactory
from services.resource import LLMModelService
from services.agent import AgentService
from services.agent.admin import AgentAdminService
from services.conversation.business import ConversationBusinessService
from services.content import AIService
from services.coin import CoinServiceFactory
from services.system.permission import PermissionService
from middleware.balance_checker import BalanceCheckerMiddleware
from services.shared.prompt_builder import PromptBuilder
from constants.agent import get_agent_config, get_all_agents, AgentType, AGENT_CONFIGS
from utils.response import success
from utils.exceptions import BadRequestException, ServerErrorException, NotFoundException, RoutingMatchFailedException
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
    from services.conversation.dao import ConversationDAO

    try:
        async with async_session_maker() as db:
            dao = ConversationDAO(db)
            await dao.embed_conversation_async(
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
    后台任务：将保存任务加入Redis队列,由队列Worker处理

    Args:
        conversation_id: 会话ID
        user_message: 用户消息内容
        assistant_message: AI回复内容
        user_tokens: 用户消息token数
        assistant_tokens: AI回复token数
    """
    try:
        # 使用队列化处理,避免数据库锁冲突
        from db.queue import ConversationQueue

        success = await ConversationQueue.enqueue(
            conversation_id=conversation_id,
            user_message=user_message,
            assistant_message=assistant_message,
            user_tokens=user_tokens,
            assistant_tokens=assistant_tokens
        )

        if success:
            logger.info(
                f"✅ [后台任务] 会话保存任务已加入队列: "
                f"会话ID={conversation_id}"
            )
        else:
            # Redis不可用时,降级为直接保存(保持原有逻辑)
            logger.warning(
                f"⚠️ [后台任务] Redis不可用,降级为直接保存: "
                f"会话ID={conversation_id}"
            )
            await save_conversation_fallback(
                conversation_id=conversation_id,
                user_message=user_message,
                assistant_message=assistant_message,
                user_tokens=user_tokens,
                assistant_tokens=assistant_tokens
            )

    except Exception as e:
        logger.error(f"❌ [后台任务] 队列入队失败: 会话{conversation_id}, 错误: {e}")
        # 降级为直接保存
        try:
            await save_conversation_fallback(
                conversation_id=conversation_id,
                user_message=user_message,
                assistant_message=assistant_message,
                user_tokens=user_tokens,
                assistant_tokens=assistant_tokens
            )
        except Exception as fallback_error:
            logger.error(
                f"❌ [后台任务] 降级保存也失败: "
                f"会话{conversation_id}, 错误={fallback_error}"
            )


async def increment_agent_usage_background_task(agent_id: int):
    """
    后台任务：增加智能体使用次数（agents 表 usage_count 字段）
    """
    try:
        logger.info(f"📊 [usage_count] 后台任务开始: Agent ID={agent_id}")
        result = await AgentAdminService.increment_usage_count(None, agent_id)
        logger.info(f"📊 [usage_count] 后台任务完成: Agent ID={agent_id}, success={result}")
    except Exception as e:
        logger.error(f"❌ [usage_count] 增加失败: Agent ID={agent_id}, 错误={e}", exc_info=True)


async def save_conversation_fallback(
    conversation_id: int,
    user_message: str,
    assistant_message: str,
    user_tokens: int = 0,
    assistant_tokens: int = 0
):
    """
    降级方案: 直接保存对话消息(Redis不可用时使用)

    Args:
        conversation_id: 会话ID
        user_message: 用户消息内容
        assistant_message: AI回复内容
        user_tokens: 用户消息token数
        assistant_tokens: AI回复token数
    """
    from db.session import async_session_maker
    from services.conversation.dao import ConversationDAO
    from sqlalchemy import select, desc
    from models.conversation import ConversationMessage

    try:
        # 1. 保存对话消息
        async with async_session_maker() as db:
            dao = ConversationDAO(db)
            await dao.save_conversation_async(
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
        logger.error(f"降级保存失败: 会话{conversation_id}, 错误: {e}")
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
    agent_type: str = Field(default=AgentType.IP_COLLECTOR, description="智能体类型")
    agent_id: Optional[int] = Field(default=None, description="智能体数据库ID（可选，用于 usage_count 统计，当 agent_type 为预设时必传）")
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

def build_final_system_prompt(agent_system_prompt: str, ip_persona_prompt: str) -> str:
    """
    融合补充人设信息 + 智能体能力，构建最终的System Prompt。
    
    拼接顺序（从上到下）：
    1. 补充人设配置（可选，来自 persona_settings）
    2. 智能体系统提示词（agent_system_prompt）
    """
    parts = []

    # 1. 补充人设配置（如语气、禁忌、关键词等）
    if ip_persona_prompt:
        parts.append("【补充人设信息】\n")
        parts.append(ip_persona_prompt.strip())

    # 2. 智能体系统提示词（放在最后，明确当前技能要做什么）
    if agent_system_prompt:
        parts.append("\n\n" + "=" * 40 + "\n")
        parts.append(agent_system_prompt.strip())

    return "".join(parts)


def get_latest_user_message(messages: List[ChatMessage]) -> str:
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


async def create_or_get_conversation(
    conversation_service: ConversationBusinessService,
    request: ChatRequest,
    current_user: User,
    db: AsyncSession,
    agent_model_type: str,
    agent_id: Optional[int] = None,
    db_agent=None
) -> int:
    """
    创建或获取会话ID（复用函数）
    
    Args:
        agent_id: agents 表主键（request.agent_id 或从 agent_type 解析）
        db_agent: Agent 对象，可选
    """
    from schemas.conversation import ConversationCreate
    
    conversation_id = request.conversation_id

    if not conversation_id:
        # 创建新会话
        first_message = ""
        for msg in request.messages:
            if msg.role == "user" and msg.content:
                first_message = msg.content[:30]
                if len(msg.content) > 30:
                    first_message += "..."
                break
        
        title = first_message if first_message else "新对话"
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
        return conversation.id
    else:
        try:
            await conversation_service.get_conversation(
                conversation_id=conversation_id,
                user_id=current_user.id
            )
            return conversation_id
        except NotFoundException:
            logger.warning(f"会话 {conversation_id} 不存在，自动创建新会话（用户ID: {current_user.id}）")
            first_message = ""
            for msg in request.messages:
                if msg.role == "user" and msg.content:
                    first_message = msg.content[:30]
                    if len(msg.content) > 30:
                        first_message += "..."
                    break
            title = first_message if first_message else "新对话"
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
            return conversation.id


async def settle_coin_cost(
    user_id: int,
    request_id: str,
    user_prompt: str,
    assistant_content: str,
    llm_model,
    coin_service,
    db_agent=None,
    agent_type: str = None,
    is_stream: bool = False,
    system_prompt: str = "",
    messages_for_ai: list = None,
    usage_from_api: Optional[dict] = None,
) -> bool:
    """
    算力结算（复用函数）
    
    Args:
        user_id: 用户ID
        request_id: 请求ID
        user_prompt: 用户输入
        assistant_content: AI回复内容
        llm_model: 模型对象
        coin_service: 算力服务（用于估算token）
        db_agent: 数据库智能体对象（可选）
        agent_type: 智能体类型（可选）
        is_stream: 是否为流式响应
        usage_from_api: API 返回的 usage（含 prompt_tokens/completion_tokens），优先使用实际 token 计费
    
    Returns:
        是否结算成功
    """
    try:
        input_tokens = None
        output_tokens = None

        # 优先使用 API 返回的实际 token 数（兼容 OpenAI prompt_tokens/completion_tokens 及部分 API 的 input_tokens/output_tokens）
        if usage_from_api and isinstance(usage_from_api, dict):
            input_tokens = usage_from_api.get("prompt_tokens") or usage_from_api.get("input_tokens")
            output_tokens = usage_from_api.get("completion_tokens") or usage_from_api.get("output_tokens")
            if input_tokens is not None and output_tokens is not None:
                input_tokens = int(input_tokens)
                output_tokens = int(output_tokens)
                logger.info(f"💰 [原子结算] 使用 API 实际 Token: 输入={input_tokens}, 输出={output_tokens}")

        # 回退到估算（API 未返回 usage 或格式不完整时）
        if input_tokens is None or output_tokens is None:
            input_text_parts = []
            if messages_for_ai:
                for m in messages_for_ai:
                    content = m.get("content", "") if isinstance(m, dict) else getattr(m, "content", "")
                    if content:
                        input_text_parts.append(str(content))
            if not input_text_parts:
                input_text_parts = [system_prompt or "", user_prompt or ""]
            input_tokens = coin_service.estimate_tokens_from_text("".join(input_text_parts))
            output_tokens = coin_service.estimate_tokens_from_text(assistant_content)
            logger.info(f"💰 [原子结算] Token 估算完成（回退）: 输入={input_tokens}(含system+历史), 输出={output_tokens}")
        
        # 计算实际消耗金额
        actual_cost = await coin_service.calculate_cost(
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            model_id=llm_model.id
        )
        
        logger.info(f"💰 [原子结算] 成本计算完成: {actual_cost} (模型ID={llm_model.id}, 模型名称={llm_model.name})")
        
        # ✅ 即使成本为0，也需要执行结算（解冻+创建流水记录）
        if actual_cost == 0:
            logger.warning(f"⚠️ [原子结算] 成本为0，但仍需执行结算以解冻预冻结金额并创建流水记录")
        
        # 获取agent信息用于日志记录
        agent_id_for_log = None
        agent_name_for_log = None
        if db_agent:
            agent_id_for_log = db_agent.id
            agent_name_for_log = db_agent.name
        elif agent_type and agent_type.isdigit():
            agent_id_for_log = int(agent_type)
        
        # 使用原子化结算（独立事务，无锁冲突）
        from db.session import async_session_maker
        async with async_session_maker() as settle_db:
            settle_coin_service = CoinServiceFactory(settle_db)
            
            logger.info(f"🔍 [原子结算] 准备调用settle_amount_atomic: user_id={user_id}, request_id={request_id}, actual_cost={actual_cost}")
            
            try:
                extra_data = {
                    "llm_system_prompt": system_prompt or "",
                    "llm_user_prompt": user_prompt or "",
                    "llm_messages": messages_for_ai or [],
                    "is_stream": bool(is_stream),
                }
                settle_result = await settle_coin_service.settle_amount_atomic(
                    user_id=user_id,
                    request_id=request_id,
                    actual_cost=actual_cost,
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    model_name=llm_model.name,
                    agent_id=agent_id_for_log,
                    agent_name=agent_name_for_log,
                    extra_data=extra_data,
                )
            except Exception as settle_error:
                logger.exception(f"❌ [原子结算] settle_amount_atomic调用异常: {str(settle_error)}")
                raise
            
            logger.info(f"🔍 [原子结算] settle_result: {settle_result}")
            
            if settle_result.get('success'):
                stream_type = "流式" if is_stream else "非流式"
                logger.info(
                    f"✅ [原子结算] 算力结算成功（{stream_type}）: "
                    f"用户ID={user_id}, "
                    f"输入Token={input_tokens}, "
                    f"输出Token={output_tokens}, "
                    f"结算金额={actual_cost}"
                )
                return True
            else:
                logger.error(
                    f"❌ [原子结算] 算力结算失败（{'流式' if is_stream else '非流式'}）: "
                    f"用户ID={user_id}, "
                    f"request_id={request_id}, "
                    f"错误={settle_result.get('message', '未知错误')}, "
                    f"结算金额={actual_cost}"
                )
                return False
    
    except (BadRequestException, NotFoundException) as e:
        logger.error(
            f"⚠️ [原子结算] 业务异常（{'流式' if is_stream else '非流式'}）: "
            f"用户ID={user_id}, request_id={request_id}, 错误={str(e)}"
        )
        import traceback
        logger.error(f"业务异常堆栈: {traceback.format_exc()}")
        return False
    except Exception as e:
        logger.exception(
            f"❌ [原子结算] 算力结算异常（{'流式' if is_stream else '非流式'}）: "
            f"用户ID={user_id}, request_id={request_id}, 错误={str(e)}"
        )
        import traceback
        logger.error(f"异常堆栈: {traceback.format_exc()}")
        return False


async def refund_frozen_coin(
    user_id: int,
    request_id: str,
    reason: str = "AI生成失败"
) -> bool:
    """
    退还算力（复用函数）
    
    Args:
        user_id: 用户ID
        request_id: 请求ID
        reason: 退款原因
    
    Returns:
        是否退款成功
    """
    try:
        from db.session import async_session_maker
        async with async_session_maker() as refund_db:
            refund_coin_service = CoinServiceFactory(refund_db)
            refund_result = await refund_coin_service.refund_amount_atomic(
                user_id=user_id,
                request_id=request_id,
                reason=reason
            )
            
            if refund_result['success']:
                logger.info(
                    f"✅ [原子退款] 退款成功: "
                    f"用户ID={user_id}, request_id={request_id}"
                )
                return True
            else:
                logger.error(
                    f"❌ [原子退款] 退款失败: "
                    f"用户ID={user_id}, "
                    f"错误={refund_result.get('message')}"
                )
                return False
    
    except (BadRequestException, NotFoundException) as refund_error:
        logger.warning(f"⚠️ [原子退款] 业务异常: {str(refund_error)}")
        return False
    except Exception as refund_error:
        logger.exception(f"❌ [原子退款] 退款异常: {str(refund_error)}")
        return False


# ============== API Endpoints ==============

@router.get("/agents")
async def list_agents(
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_miniprogram_user_optional),
):
    """获取所有可用的智能体列表（从数据库读取）"""
    # 从未登录或未传 token：仅展示主租户（与线上主小程序行为一致）；已登录：展示该用户租户
    tenant_pid = DEFAULT_TENANT_ID
    if current_user is not None:
        tenant_pid = current_user.tenant_id

    # 从数据库查询启用的智能体
    from sqlalchemy import select, and_
    from models.agent import Agent
    
    result = await db.execute(
        select(Agent).where(
            and_(
                Agent.status == 1,  # 只返回上架的智能体
                Agent.is_system == 0,  # 过滤掉系统自用智能体
                Agent.tenant_id == tenant_pid,
            )
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
            "description": agent.description or "",
            "welcomeMessage": agent.welcome_message or ""  # 欢迎语，空则前端使用默认
        })
    
    return success(data={"agents": agents}, msg="获取成功")


@router.get("/agents/{agent_id}", summary="获取智能体详情（不含提示词）")
async def get_agent_detail(
    agent_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_miniprogram_user_optional),
):
    """获取单个智能体详情，仅返回上架且非系统自用的智能体，不返回提示词"""
    tenant_pid = DEFAULT_TENANT_ID
    if current_user is not None:
        tenant_pid = current_user.tenant_id

    from sqlalchemy import select, and_
    from models.agent import Agent
    from utils.serializers import agent_to_client_detail_response

    result = await db.execute(
        select(Agent).where(
            and_(
                Agent.id == agent_id,
                Agent.status == 1,  # 只返回上架的智能体
                Agent.is_system == 0,  # 过滤掉系统自用智能体
                Agent.tenant_id == tenant_pid,
            )
        )
    )
    agent = result.scalar_one_or_none()
    if not agent:
        raise NotFoundException(msg="智能体不存在或已下架")

    data = agent_to_client_detail_response(agent)
    return success(data=data, msg="获取成功")


@router.post("/chat")
async def generate_chat(
    request: ChatRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_miniprogram_user),
    db: AsyncSession = Depends(get_db)
):
    """对话式创作接口（支持向量检索和异步保存）"""
    try:
        # 0. 会员到期检查：如已到期则直接返回
        permission_service = PermissionService(db)
        permission = await permission_service.get_user_permission(current_user.id)
        if permission.get("is_vip_expired"):
            raise BadRequestException("会员已到期，请联系管理员。")

        # 0.1 初始化会话服务
        conversation_service = ConversationBusinessService(db)

        # 0.1. 解析 agent_id（agents 表主键，唯一标识）
        # agent_id 来源：request.agent_id（前端传入）或 request.agent_type（当为数字时）
        # db_agent：用 agent_id 查出的 Agent 对象，用于配置、会话标题、算力流水、usage_count
        from sqlalchemy import select, or_, and_
        from models.agent import Agent

        agent_id = request.agent_id
        if agent_id is None and request.agent_type and request.agent_type.isdigit():
            agent_id = int(request.agent_type)
        logger.info(f"📊 [Chat] agent_id={agent_id}, request.agent_id={request.agent_id}, request.agent_type={request.agent_type}")

        agent_config = None
        agent_type_source = "preset"
        db_agent = None
        agent_model_type = request.model_type or "doubao"  # 默认值

        # 优先用 agent_id 查数据库（前端传 agent_id 时，agent_type 可能为预设如 ip_collector）
        if agent_id is not None:
            result = await db.execute(
                select(Agent).where(
                    and_(
                        Agent.id == agent_id,
                        Agent.tenant_id == current_user.tenant_id,
                        or_(Agent.is_system == 1, Agent.status == 1),
                    )
                )
            )
            db_agent = result.scalar_one_or_none()
            if db_agent:
                agent_config = {
                    "system_prompt": db_agent.system_prompt,
                    "temperature": db_agent.config.get("temperature", 0.7) if db_agent.config else 0.7,
                    "max_tokens": db_agent.config.get("max_tokens", 2048) if db_agent.config else 2048,
                }
                agent_type_source = "database"
                agent_model_type = db_agent.model
                logger.info(f"📊 [Chat] 使用数据库智能体: id={db_agent.id}, name={db_agent.name}")

        # 若 db_agent 不存在，尝试用 agent_type 解析（预设或旧版传参）
        if not agent_config:
            try:
                agent_config = get_agent_config(request.agent_type)
                if agent_id is None and request.agent_type.isdigit():
                    agent_id = int(request.agent_type)
                    result = await db.execute(
                        select(Agent).where(
                            and_(
                                Agent.id == agent_id,
                                Agent.tenant_id == current_user.tenant_id,
                                or_(Agent.is_system == 1, Agent.status == 1),
                            )
                        )
                    )
                    db_agent = result.scalar_one_or_none()
            except ValueError:
                if agent_id is not None:
                    raise BadRequestException(f"智能体 ID {agent_id} 不存在或已下架")
                available = ", ".join(AGENT_CONFIGS.keys())
                raise BadRequestException(f"未知的智能体类型: '{request.agent_type}'。可用类型: {available}")

        if not agent_config:
            raise BadRequestException(f"无法获取智能体配置: '{request.agent_type}'")

        if agent_type_source == "preset" and not request.model_type:
            agent_model_type = "doubao"

        # 0.2. 不再验证模型类型，所有模型信息从数据库读取
        # 这样可以支持动态添加新模型，无需修改代码
        if settings.DEBUG:
            logger.debug(f"使用模型类型: {agent_model_type} (来源: {agent_type_source})")

        # 0.2. 处理会话ID（如果不存在则创建新会话）
        conversation_id = await create_or_get_conversation(
            conversation_service=conversation_service,
            request=request,
            current_user=current_user,
            db=db,
            agent_model_type=agent_model_type,
            agent_id=agent_id,
            db_agent=db_agent
        )

        # 1. 获取项目补充人设信息（IP人设）
        # 优先使用 request.project_id；若未提供且为续聊（有 conversation_id），则从会话记录中取 project_id
        ip_persona_prompt = ""
        effective_project_id = request.project_id
        if effective_project_id is None and conversation_id:
            try:
                conv = await conversation_service.get_conversation(
                    conversation_id=conversation_id,
                    user_id=current_user.id
                )
                effective_project_id = conv.project_id
                if effective_project_id and settings.DEBUG:
                    logger.debug(f"续聊时从会话恢复 project_id: {effective_project_id}")
            except Exception:
                pass  # 会话不存在或无权访问时，effective_project_id 保持 None
        if effective_project_id:
            project_service = ProjectService(db)
            project = await project_service.get_project_by_id(effective_project_id, user_id=current_user.id)
            if project and project.persona_settings:
                # 始终提取补充人设配置（语气、禁忌、关键词等），排除 master_prompt 仅保留补充信息
                ip_persona_prompt = PromptBuilder.extract_persona_prompt(
                    project.persona_settings or {},
                    master_prompt="",
                    project_name=project.name or "",
                    project_industry=project.industry or "通用",
                )

        # 2. 获取用户最新消息作为prompt
        user_prompt = get_latest_user_message(request.messages)
        
        if not user_prompt:
            raise BadRequestException("消息列表不能为空")
        
        # 3. 技能组装模式：路由 + Prompt 组装（agent_mode=1）
        if db_agent and getattr(db_agent, "agent_mode", 0) == 1:
            from services.routing import MasterRouter, PromptEngine
            master_router = MasterRouter()
            prompt_engine = PromptEngine()
            strict_routing = bool(getattr(db_agent, "is_routing_enabled", 0) == 1)
            try:
                routing_result = await master_router.route(
                    db=db,
                    agent=db_agent,
                    user_input=user_prompt,
                    strict_routing=strict_routing
                )
            except RoutingMatchFailedException as e:
                # 路由失败，返回引导信息，不调用 LLM、不扣费
                routing_failed_msg = e.msg
                if request.stream:
                    async def _stream_routing_failed():
                        import json as _json

                        yield f"data: {_json.dumps({'conversation_id': conversation_id}, ensure_ascii=False)}\n\n"
                        yield f"data: {_json.dumps({'content': routing_failed_msg}, ensure_ascii=False)}\n\n"
                        yield f"data: {_json.dumps({'done': True}, ensure_ascii=False)}\n\n"
                    return StreamingResponse(
                        _stream_routing_failed(),
                        media_type="text/event-stream",
                        headers={"Cache-Control": "no-cache", "Connection": "keep-alive", "X-Accel-Buffering": "no"},
                    )
                return ChatResponse(
                    success=True,
                    content=routing_failed_msg,
                    agent_type=request.agent_type,
                    model_type=agent_model_type,
                )
            prompt_result = await prompt_engine.assemble_prompt(
                db=db,
                agent=db_agent,
                selected_skill_ids=routing_result.selected_skill_ids,
                skill_variables=(db_agent.skill_variables or {}),
                persona_prompt=ip_persona_prompt or None,
                user_input=user_prompt,
            )
            base_system_prompt = prompt_result.system_prompt
            if settings.DEBUG:
                logger.debug(f"技能路由完成: 选中{len(routing_result.selected_skill_ids)}个技能, {prompt_result.token_count} tokens")
        else:
            base_system_prompt = agent_config["system_prompt"]
        
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
        
        # 6. 构建最终System Prompt（system 只放“规则/人设/能力”，对话历史放到 messages，避免重复和额外 token）
        conversation_context = ""
        if db_agent and getattr(db_agent, "agent_mode", 0) == 1:
            # 技能模式：prompt_result 已包含 persona，直接使用
            final_system_prompt = base_system_prompt
        else:
            # 普通模式：需融合 ip_persona_prompt
            final_system_prompt = build_final_system_prompt(
                agent_system_prompt=base_system_prompt,
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
            truncated_prompt = base_system_prompt
            # 2. 普通模式才追加IP人设（技能模式 base_system_prompt 已含 persona）
            is_skill_mode = db_agent and getattr(db_agent, "agent_mode", 0) == 1
            if not is_skill_mode:
                remaining_space = MAX_SYSTEM_PROMPT_LENGTH - len(truncated_prompt) - 100
                if remaining_space > 0 and ip_persona_prompt:
                    ip_persona_truncated = ip_persona_prompt[:remaining_space]
                    truncated_prompt = build_final_system_prompt(
                        agent_system_prompt=truncated_prompt,
                        ip_persona_prompt=ip_persona_truncated
                    )

            # 3. 若仍超长则强制截断
            if len(truncated_prompt) > MAX_SYSTEM_PROMPT_LENGTH:
                truncated_prompt = truncated_prompt[:MAX_SYSTEM_PROMPT_LENGTH - 100]
            # 4. 如果还有空间,添加对话历史(最多2轮)
            if len(truncated_prompt) < MAX_SYSTEM_PROMPT_LENGTH * 0.8 and conversation_context:
                simplified_context = "\n【最近对话】" + "\n".join(conversation_context.split("\n")[-6:])
                final_system_prompt = truncated_prompt + "\n\n" + simplified_context
            else:
                final_system_prompt = truncated_prompt

            logger.warning(f"  - After truncation: {len(final_system_prompt)} chars")
        else:
            if settings.DEBUG:
                logger.debug(f"System prompt length OK: {original_length} chars")

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

        if settings.DEBUG:
            logger.debug(f"Querying model configuration:")
            logger.debug(f"  - Requested model_type: {agent_model_type}")

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

        if settings.DEBUG:
            logger.debug(f"Model found: {llm_model.name} (id={llm_model.id}, provider={llm_model.provider})")

        if not llm_model.api_key:
            raise BadRequestException(f"模型 {llm_model.name} 未配置 API Key，请在管理后台配置")

        # ========== ✅ 第一阶段：算力预冻结（极短事务，~10ms） ==========
        task_id = str(uuid.uuid4())
        request_id = f"chat_{current_user.id}_{task_id}"  # ✅ 幂等性request_id
        coin_service = CoinServiceFactory(db)
        estimated_output_tokens = request.max_tokens or 2048
        
        # ✅ 修复：提前初始化freeze_info，避免作用域问题
        freeze_info = None

        try:
            # 1️⃣ 先计算预估成本（不涉及数据库操作）
            # 构建完整输入文本（system prompt + 对话历史）用于预冻结估算，与结算时一致
            full_input_parts = [final_system_prompt or ""]
            for msg in optimized_messages or []:
                content = msg.content if hasattr(msg, "content") else (msg.get("content", "") if isinstance(msg, dict) else "")
                if content:
                    full_input_parts.append(str(content))
            user_input_text = "".join(full_input_parts)

            estimated_cost = await coin_service.estimate_max_cost(
                model_id=llm_model.id,
                input_text=user_input_text,
                estimated_output_tokens=estimated_output_tokens
            )

            logger.info(
                f"💰 [原子冻结] 预估成本: "
                f"用户ID={current_user.id}, "
                f"预估金额={estimated_cost}, "
                f"request_id={request_id}"
            )

            # 2️⃣ 使用原子化冻结（无锁冲突）
            freeze_result = await coin_service.freeze_amount_atomic(
                user_id=current_user.id,
                amount=estimated_cost,  # ✅ 使用预估成本
                request_id=request_id,
                model_id=llm_model.id,
                conversation_id=conversation_id
            )

            if not freeze_result['success']:
                if freeze_result.get('insufficient_balance'):
                    # 余额不足，直接返回错误
                    logger.warning(f"❌ [原子冻结] 用户余额不足: 用户ID={current_user.id}")
                    raise BadRequestException(
                        f"余额不足，请充值后再试。"
                    )
                else:
                    # 其他错误
                    logger.error(f"❌ [原子冻结] 冻结失败: 用户ID={current_user.id}")
                    raise BadRequestException("算力冻结失败，请稍后重试")

            freeze_info = {
                'task_id': task_id,
                'request_id': request_id,
                'freeze_log_id': freeze_result['freeze_log_id'],
                'frozen_amount': estimated_cost,  # ✅ 保存预估金额
                'estimated_cost': estimated_cost
            }

            logger.info(
                f"✅ [原子冻结] 算力预冻结成功: "
                f"用户ID={current_user.id}, "
                f"request_id={request_id}, "
                f"冻结金额={estimated_cost}, "
                f"冻结记录ID={freeze_result['freeze_log_id']}"
            )

        except BadRequestException:
            # 余额不足，直接返回错误
            raise
        except Exception as e:
            # 预冻结失败，记录警告但不阻止请求（降级处理）
            logger.warning(f"⚠️ [DEBUG] 算力预冻结失败（降级处理）: {str(e)}")
            task_id = None  # 标记为未预冻结，跳过结算
            freeze_info = None  # ✅ 修复：确保freeze_info为None

        # 9. 构建 messages 列表（与 AIService 兼容的格式）
        # 将 final_system_prompt 和 user_prompt 转换为 messages 格式
        messages_for_ai = []

        # 规范化消息，去掉连续重复（避免前端/上游重复发送导致 token 浪费）
        normalized_messages = []
        for msg in optimized_messages or []:
            if normalized_messages and msg.role == normalized_messages[-1].role and msg.content == normalized_messages[-1].content:
                continue
            normalized_messages.append(msg)

        # 🔍 智能处理长system prompt: 将长提示词拆分成多个message,避免网关503错误
        # 策略:
        # 1. 短提示词(<3000 chars): 使用单个 system message
        # 2. 长提示词(>=3000 chars): 拆分成多个 system message,每个<2000 chars
        # 3. 这样既保留完整信息,又避免单个message过长导致网关拒绝

        MAX_SINGLE_MESSAGE_LENGTH = 2000  # 单个message的最大长度
        USE_SPLIT_STRATEGY = len(final_system_prompt) >= MAX_SINGLE_MESSAGE_LENGTH

        if USE_SPLIT_STRATEGY:
            # 长提示词: 拆分成多个 system message
            if settings.DEBUG:
                logger.debug(f"System prompt较长({len(final_system_prompt)} chars),使用拆分策略:")
                logger.debug(f"  - 拆分成多个 system message,每个 < {MAX_SINGLE_MESSAGE_LENGTH} chars")
                logger.debug(f"  - 避免单个 message 过长导致网关 503 错误")

            # 将 system prompt 按段落拆分
            # 优先在分隔符处拆分: "========================================", "\n\n", "\n"
            parts = []
            current_part = ""
            separators = ["========================================", "\n\n", "\n"]

            # 按优先级尝试拆分
            for separator in separators:
                if len(final_system_prompt) < MAX_SINGLE_MESSAGE_LENGTH:
                    break

                # 尝试按此分隔符拆分
                segments = final_system_prompt.split(separator)
                current_part = ""

                for segment in segments:
                    test_part = current_part + separator + segment if current_part else segment

                    if len(test_part) <= MAX_SINGLE_MESSAGE_LENGTH:
                        current_part = test_part
                    else:
                        # 当前部分已满,保存并开始新部分
                        if current_part:
                            parts.append(current_part.strip())
                        current_part = segment.strip()

                # 保存最后的部分
                if current_part:
                    parts.append(current_part.strip())

                # 如果拆分成功,退出循环
                if len(parts) > 1 or all(len(p) < MAX_SINGLE_MESSAGE_LENGTH for p in parts):
                    break
                else:
                    # 拆分失败,清空重试
                    parts = []

            # 如果拆分失败,强制按字符长度拆分
            if not parts:
                logger.warning(f"  - 按分隔符拆分失败,使用强制拆分")
                for i in range(0, len(final_system_prompt), MAX_SINGLE_MESSAGE_LENGTH):
                    parts.append(final_system_prompt[i:i + MAX_SINGLE_MESSAGE_LENGTH])

            logger.info(f"  - 拆分结果: {len(parts)} 个 system message")
            for i, part in enumerate(parts):
                logger.info(f"    Part {i+1}: {len(part)} chars")

            # 构建消息列表: 多个 system message + 对话消息
            messages_for_ai = []
            for part in parts:
                messages_for_ai.append({
                    "role": "system",
                    "content": part
                })

            # 添加对话消息（包含历史与本轮用户输入）
            for msg in normalized_messages:
                messages_for_ai.append({
                    "role": msg.role,
                    "content": msg.content
                })

        else:
            # System prompt长度适中,使用标准格式(带缓存)
            if settings.DEBUG:
                logger.debug(f"System prompt长度适中({len(final_system_prompt)} chars),使用标准格式(带缓存)")

            if final_system_prompt:
                messages_for_ai.append({
                    "role": "system",
                    "content": final_system_prompt
                })
            # 添加对话消息（包含历史与本轮用户输入）
            for msg in normalized_messages:
                messages_for_ai.append({
                    "role": msg.role,
                    "content": msg.content
                })

        # 10. 使用 AIService（与 admin/ai 保持一致，避免差异）
        ai_service = AIService(db)

        # 查找模型 ID（使用实际的模型标识符，而不是数据库主键）
        model_id_for_ai = llm_model.model_id  # 使用 model_id 字段（实际的模型标识符）

        # 🔍 调试日志: 打印关键信息
        # 计算请求体大小(估算)
        request_body_size = len(json.dumps({"model": model_id_for_ai, "messages": messages_for_ai}).encode('utf-8'))

        if settings.DEBUG:
            logger.debug(f"Chat Request Info:")
            logger.debug(f"  - Conversation ID: {conversation_id}")
            logger.debug(f"  - User ID: {current_user.id}")
            logger.debug(f"  - Agent Type: {request.agent_type}")
            logger.debug(f"  - Model Type: {agent_model_type}")
            logger.debug(f"  - Provider: {llm_model.provider}")
            logger.debug(f"  - Model ID for AI: {model_id_for_ai}")
            logger.debug(f"  - DB Model: {llm_model.name} (model_id={llm_model.model_id})")
            logger.debug(f"  - Base URL: {llm_model.base_url}")
            logger.debug(f"  - System Prompt Length: {len(final_system_prompt)} chars")
            logger.debug(f"  - User Prompt Length: {len(user_prompt)} chars")
            logger.debug(f"  - Messages Count: {len(messages_for_ai)}")
            logger.debug(f"  - Estimated Request Body Size: {request_body_size} bytes")
            logger.debug(f"  - Temperature: {temperature}, Max Tokens: {max_tokens}")
            logger.debug(f"  - Stream: {request.stream}")

            # 打印实际发送的消息结构(用于调试503问题)
            logger.debug(f"Messages Structure:")
            for i, msg in enumerate(messages_for_ai):
                role = msg.get('role', 'unknown')
                content = msg.get('content', '')
                content_preview = content[:100] + '...' if len(content) > 100 else content
                # 检查是否有特殊字符
                has_special_chars = any(ord(c) > 127 for c in content)
                logger.debug(f"  - Message {i+1}: role={role}, length={len(content)}, has_special_chars={has_special_chars}")
                logger.debug(f"    Preview: {content_preview}")

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
                nonlocal assistant_content, task_id, freeze_info
                usage_from_api = None
                try:
                    # 首先发送 conversation_id（让前端能够更新会话ID）
                    yield f"data: {json.dumps({'conversation_id': conversation_id}, ensure_ascii=False)}\n\n"
                    if settings.DEBUG:
                        logger.debug(f"Starting stream generation for conversation {conversation_id}")

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
                            if settings.DEBUG:
                                logger.debug(f"Received first chunk from AI service")

                        # AIService.stream_chat 返回的是 JSON 字符串，需要解析
                        try:
                            chunk_data = json.loads(chunk_json)
                            # 检查是否有错误
                            if "error" in chunk_data:
                                # ✅ 修复：AI返回错误时，也需要退款预冻结的算力
                                logger.error(f"Received error from AI service: {chunk_data['error']}")
                                yield f"data: {chunk_json}\n\n"
                                
                                # 退款预冻结的算力
                                if task_id and freeze_info and freeze_info.get('request_id'):
                                    await refund_frozen_coin(
                                        user_id=current_user.id,
                                        request_id=freeze_info['request_id'],
                                        reason="AI服务返回错误"
                                    )
                                
                                return
                            # 捕获 API 返回的 usage，供算力结算使用
                            if "usage" in chunk_data:
                                usage_from_api = chunk_data["usage"]
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

                    if settings.DEBUG:
                        logger.debug(f"Stream generation completed. Total chunks: {chunk_count}, Content length: {len(assistant_content)}")
                    yield f"data: {json.dumps({'done': True}, ensure_ascii=False)}\n\n"

                    # ========== ✅ 第三阶段：算力结算（极短事务，~10ms） ==========
                    # ✅ 修复：增强条件判断，确保freeze_info存在且有效
                    logger.info(f"🔍 [原子结算] 检查结算条件: task_id={task_id}, freeze_info存在={freeze_info is not None}, request_id={freeze_info.get('request_id') if freeze_info else None}")
                    
                    if task_id and freeze_info and freeze_info.get('request_id'):
                        logger.info(f"💰 [原子结算] 开始算力结算流程，request_id={freeze_info['request_id']}")
                        try:
                            settle_success = await settle_coin_cost(
                                user_id=current_user.id,
                                request_id=freeze_info['request_id'],
                                user_prompt=user_prompt,
                                assistant_content=assistant_content,
                                system_prompt=final_system_prompt,
                                messages_for_ai=messages_for_ai,
                                llm_model=llm_model,
                                coin_service=coin_service,
                                db_agent=db_agent,
                                agent_type=request.agent_type,
                                is_stream=True,
                                usage_from_api=usage_from_api
                            )
                            if not settle_success:
                                logger.error(f"❌ [原子结算] settle_coin_cost返回False，结算可能失败，用户ID={current_user.id}, request_id={freeze_info['request_id']}")
                        except Exception as settle_error:
                            logger.exception(f"❌ [原子结算] settle_coin_cost调用异常: 用户ID={current_user.id}, request_id={freeze_info['request_id']}, 错误={str(settle_error)}")
                            # 不重新抛出异常，避免影响流式响应
                    else:
                        if not task_id:
                            logger.warning(f"⚠️ [原子结算] 跳过结算：task_id为空（预冻结失败）")
                        elif not freeze_info:
                            logger.warning(f"⚠️ [原子结算] 跳过结算：freeze_info为空")
                        elif not freeze_info.get('request_id'):
                            logger.warning(f"⚠️ [原子结算] 跳过结算：request_id为空")

                    # 流式完成后，触发后台任务保存
                    background_tasks.add_task(
                        save_conversation_background_task,
                        conversation_id=conversation_id,
                        user_message=user_prompt,
                        assistant_message=assistant_content,
                        user_tokens=len(user_prompt) // 4,  # 粗略估算token数
                        assistant_tokens=len(assistant_content) // 4,
                    )
                    # 增加智能体使用次数（使用 agent_id，即 agents 表主键）
                    if agent_id is not None:
                        logger.info(f"📊 [usage_count] 准备增加 Agent ID={agent_id} 使用次数")
                        background_tasks.add_task(increment_agent_usage_background_task, agent_id)

                except (BadRequestException, NotFoundException) as e:
                    # 业务异常直接传递
                    logger.warning(f"⚠️ [Stream] 业务异常: {str(e)}")
                    error_chunk = {
                        "error": {
                            "message": str(e),
                            "type": type(e).__name__
                        }
                    }
                    yield f"data: {json.dumps(error_chunk, ensure_ascii=False)}\n\n"
                    return
                except Exception as e:
                    # 🔍 详细错误日志
                    import traceback
                    import httpx
                    
                    logger.error(f"Stream generation failed:")
                    logger.error(f"  - Error Type: {type(e).__name__}")
                    logger.error(f"  - Error Message: {str(e)}")
                    
                    # 如果是连接错误，提取更详细的信息
                    if isinstance(e, (httpx.ConnectError, httpx.ConnectTimeout)):
                        # 提取底层异常信息
                        if hasattr(e, '__cause__') and e.__cause__:
                            logger.error(f"  - Underlying Error: {type(e.__cause__).__name__}: {str(e.__cause__)}")
                        
                        # 尝试获取请求信息（如果可用）
                        # ✅ 修复：重命名变量避免覆盖外部的request参数
                        if hasattr(e, 'request'):
                            http_request = e.request
                            logger.error(f"  - Request URL: {http_request.url if hasattr(http_request, 'url') else 'N/A'}")
                            logger.error(f"  - Request Method: {http_request.method if hasattr(http_request, 'method') else 'N/A'}")
                        
                        # 连接错误诊断信息
                        logger.error(f"  - Connection Error Diagnosis:")
                        logger.error(f"    * 可能原因: 网络连接失败、DNS解析失败、防火墙阻止、API服务不可用")
                        logger.error(f"    * 建议检查: 网络连接、API服务状态、代理设置")
                    
                    logger.error(f"  - Conversation ID: {conversation_id}")
                    logger.error(f"  - User ID: {current_user.id}")
                    logger.error(f"  - Model ID: {model_id_for_ai}")
                    logger.error(f"  - Agent Type: {request.agent_type}")
                    logger.error(f"  - System Prompt Length: {len(final_system_prompt)} chars")
                    logger.error(f"  - User Prompt Length: {len(user_prompt)} chars")
                    logger.error(f"  - Temperature: {temperature}, Max Tokens: {max_tokens}")
                    logger.error(f"  - Traceback:\n{traceback.format_exc()}")

                    # ========== ✅ 错误时退款预冻结的算力（原子化退款） ==========
                    # ✅ 修复：增强条件判断，确保freeze_info存在且有效
                    if task_id and freeze_info and freeze_info.get('request_id'):
                        await refund_frozen_coin(
                            user_id=current_user.id,
                            request_id=freeze_info['request_id'],
                            reason="AI生成失败"
                        )

                    # 统一错误格式：包含 message 字段，便于前端展示
                    error_chunk = {
                        "error": {
                            "message": f"生成错误: {str(e)}",
                            "type": type(e).__name__
                        }
                    }
                    # 如果是连接错误，添加更详细的诊断信息
                    if isinstance(e, (httpx.ConnectError, httpx.ConnectTimeout)):
                        error_chunk["error"]["details"] = "请检查网络连接和API服务状态"
                    yield f"data: {json.dumps(error_chunk, ensure_ascii=False)}\n\n"
            
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
            
            # ========== ✅ 非流式响应：算力结算（极短事务，~10ms） ==========
            # ✅ 修复：增强条件判断，确保freeze_info存在且有效
            if task_id and freeze_info and freeze_info.get('request_id'):
                logger.info(f"💰 [原子结算] 开始算力结算流程（非流式），request_id={freeze_info['request_id']}")
                await settle_coin_cost(
                    user_id=current_user.id,
                    request_id=freeze_info['request_id'],
                    user_prompt=user_prompt,
                    assistant_content=assistant_content,
                    system_prompt=final_system_prompt,
                    messages_for_ai=messages_for_ai,
                    llm_model=llm_model,
                    coin_service=coin_service,
                    db_agent=db_agent,
                    agent_type=request.agent_type,
                    is_stream=False,
                    usage_from_api=result.get("usage")
                )
            else:
                if not task_id:
                    logger.warning(f"⚠️ [原子结算] 跳过结算：task_id为空（预冻结失败）")
                elif not freeze_info:
                    logger.warning(f"⚠️ [原子结算] 跳过结算：freeze_info为空")
                elif not freeze_info.get('request_id'):
                    logger.warning(f"⚠️ [原子结算] 跳过结算：request_id为空")
            
            # 立即触发后台任务保存（不阻塞响应）
            background_tasks.add_task(
                save_conversation_background_task,
                conversation_id=conversation_id,
                user_message=user_prompt,
                assistant_message=assistant_content,
                user_tokens=len(user_prompt) // 4,
                assistant_tokens=len(assistant_content) // 4,
            )
            # 增加智能体使用次数（使用 agent_id，即 agents 表主键）
            if agent_id is not None:
                logger.info(f"📊 [usage_count] 准备增加 Agent ID={agent_id} 使用次数（非流式）")
                background_tasks.add_task(increment_agent_usage_background_task, agent_id)
            
            return ChatResponse(
                success=True,
                content=assistant_content,
                agent_type=request.agent_type,
                model_type=agent_model_type
            )
    
    except (BadRequestException, NotFoundException, ServerErrorException):
        # 业务异常直接抛出
        raise
    except Exception as e:
        # 🔍 捕获所有未处理的异常,记录详细日志
        import traceback
        import httpx
        
        # 根据异常类型提供更精确的错误信息
        if isinstance(e, (httpx.ConnectError, httpx.ConnectTimeout, httpx.TimeoutException)):
            logger.error(f"❌ [Chat] 网络连接错误: {str(e)}")
            raise ServerErrorException("AI服务暂时不可用，请稍后重试")
        elif isinstance(e, (ValueError, TypeError, AttributeError)):
            logger.error(f"❌ [Chat] 参数错误: {str(e)}")
            raise BadRequestException(f"请求参数错误: {str(e)}")
        else:
            logger.exception(f"❌ [Chat] 未预期的错误: {str(e)}")
            logger.error(f"  - User ID: {current_user.id if 'current_user' in locals() else 'N/A'}")
            logger.error(f"  - Model Type: {agent_model_type if 'agent_model_type' in locals() else 'N/A'}")
            logger.error(f"  - Agent Type: {request.agent_type if 'request' in locals() else 'N/A'}")
            logger.error(f"  - Project ID: {request.project_id if 'request' in locals() else 'N/A'}")
            raise ServerErrorException("生成失败，请稍后重试")


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
        user_prompt = get_latest_user_message(request.messages)
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
                    ip_persona_prompt = PromptBuilder.get_ip_persona_prompt_from_project(project)
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
    agent_type: str = Query(default=AgentType.IP_COLLECTOR, description="智能体类型"),
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

