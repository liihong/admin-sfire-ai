"""
MiniProgram Generation Endpoints
小程序内容生成接口
"""
import json
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
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
from constants.agent import get_agent_config, get_all_agents, AgentType
from utils.response import success
from utils.exceptions import BadRequestException, ServerErrorException

router = APIRouter()


# ============== Request/Response Models ==============

class ChatMessage(BaseModel):
    """对话消息模型"""
    role: str = Field(..., description="消息角色: 'user' 或 'assistant'")
    content: str = Field(..., description="消息内容")


class ChatRequest(BaseModel):
    """对话式创作请求模型"""
    project_id: Optional[int] = Field(default=None, description="项目ID，用于获取IP人设信息")
    agent_type: str = Field(default=AgentType.EFFICIENT_ORAL, description="智能体类型")
    messages: List[ChatMessage] = Field(..., description="对话历史消息列表")
    model_type: str = Field(default="deepseek", description="LLM模型类型: 'deepseek', 'claude', 'doubao'")
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

@router.get("/agents", response_model=AgentListResponse)
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
    
    # 转换为前端需要的格式
    agents = []
    for agent in db_agents:
        # 如果数据库中有 type 字段，使用 agent.type；否则使用 agent.id
        # 这里我们使用 agent.id 作为 type，前端可以通过这个 id 来识别智能体
        # 注意：前端需要调整映射逻辑，或者数据库需要添加 type 字段
        agent_type = str(agent.id)  # 暂时使用 ID 作为 type
        
        # 尝试从 config 中获取 type（如果之前有存储）
        if agent.config and isinstance(agent.config, dict) and "type" in agent.config:
            agent_type = agent.config["type"]
        
        agents.append(AgentInfo(
            type=agent_type,
            id=str(agent.id),
            name=agent.name,
            icon=agent.icon,
            description=agent.description or ""
        ))
    
    return AgentListResponse(
        success=True,
        agents=agents
    )


@router.post("/chat")
async def generate_chat(
    request: ChatRequest,
    current_user: User = Depends(get_current_miniprogram_user),
    db: AsyncSession = Depends(get_db)
):
    """对话式创作接口"""
    try:
        # 1. 验证模型类型
        supported_models = LLMFactory.get_supported_models()
        if request.model_type.lower() not in supported_models:
            raise BadRequestException(f"不支持的模型类型: '{request.model_type}'。支持的类型: {supported_models}")
        
        # 2. 获取智能体配置
        try:
            agent_config = get_agent_config(request.agent_type)
        except ValueError as e:
            raise BadRequestException(str(e))
        
        # 3. 获取项目IP画像（如果提供了project_id）
        ip_persona_prompt = ""
        if request.project_id:
            project_service = ProjectService(db)
            project = await project_service.get_project_by_id(request.project_id, user_id=current_user.id)
            if project:
                ip_persona_prompt = build_ip_persona_prompt(project)
        
        # 4. 构建最终System Prompt
        base_system_prompt = agent_config["system_prompt"]
        conversation_context = build_conversation_context(request.messages)
        
        final_system_prompt = build_final_system_prompt(
            agent_system_prompt=base_system_prompt + conversation_context,
            ip_persona_prompt=ip_persona_prompt,
        )
        
        # 5. 获取用户最新消息作为prompt
        user_prompt = format_messages_for_llm(request.messages)
        
        if not user_prompt:
            raise BadRequestException("消息列表不能为空")
        
        # 6. 确定生成参数
        temperature = request.temperature if request.temperature is not None else agent_config.get("temperature", 0.7)
        max_tokens = request.max_tokens or agent_config.get("max_tokens", 2048)
        
        # 7. 从数据库获取模型配置
        # model_type 到 provider 的映射
        model_type_to_provider = {
            "deepseek": "deepseek",
            "doubao": "doubao",
            "claude": "anthropic"
        }
        provider = model_type_to_provider.get(request.model_type.lower(), request.model_type.lower())
        
        # 查询数据库中的模型配置
        llm_model_service = LLMModelService(db)
        # 根据 provider 查询启用的模型（取第一个）
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
        
        if not llm_model:
            raise BadRequestException(f"未找到启用的 {request.model_type} 模型配置，请在管理后台配置模型")
        
        if not llm_model.api_key:
            raise BadRequestException(f"模型 {llm_model.name} 未配置 API Key，请在管理后台配置")
        
        # 8. 创建LLM实例（使用数据库配置）
        llm = LLMFactory.create(
            request.model_type,
            api_key=llm_model.api_key,
            base_url=llm_model.base_url,
            model=llm_model.model_id
        )
        
        # 9. 生成响应
        if request.stream:
            # 流式响应
            async def generate_stream():
                try:
                    async for chunk in llm.generate_stream(
                        prompt=user_prompt,
                        system_prompt=final_system_prompt,
                        temperature=temperature,
                        max_tokens=max_tokens
                    ):
                        yield f"data: {json.dumps({'content': chunk}, ensure_ascii=False)}\n\n"
                    
                    yield f"data: {json.dumps({'done': True}, ensure_ascii=False)}\n\n"
                    
                except Exception as e:
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
            content = await llm.generate_text(
                prompt=user_prompt,
                system_prompt=final_system_prompt,
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            return ChatResponse(
                success=True,
                content=content,
                agent_type=request.agent_type,
                model_type=request.model_type
            )
    
    except (BadRequestException, ServerErrorException):
        raise
    except Exception as e:
        raise ServerErrorException(f"生成失败: {str(e)}")


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

