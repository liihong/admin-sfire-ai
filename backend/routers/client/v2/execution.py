"""
Agent执行路由（v2版本）
前端用户接口，支持IP基因注入
"""
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from loguru import logger
import json

from core.deps import _get_db
from schemas.v2.agent import (
    AgentExecuteRequest,
    AgentExecuteResponse,
)
from models.agent import Agent
from models.project import Project
from services.agent.business import AgentBusinessService
from services.routing import MasterRouter, PromptEngine
from services.shared.prompt_builder import PromptBuilder
from utils.response import success
from utils.exceptions import NotFoundException, BadRequestException

router = APIRouter(prefix="/execution", tags=["Agent执行（v2）"])


@router.post("/agents/{agent_id}/execute")
async def execute_agent(
    agent_id: int,
    request_data: AgentExecuteRequest,
    db: AsyncSession = Depends(_get_db),
):
    """
    执行Agent（支持IP基因注入和智能路由）
    
    执行流程：
    1. 参数校验
    2. 调用AgentBusinessService执行完整流程
    3. 返回流式响应（SSE格式）
    
    注意：此接口返回流式响应，前端需要处理SSE格式
    """
    # 参数校验
    if not request_data.input_text or not request_data.input_text.strip():
        raise BadRequestException(msg="用户输入不能为空")
    
    # 创建Agent业务服务
    execution_service = AgentBusinessService(db)
    
    # 流式响应生成器
    async def generate_response():
        try:
            async for chunk in execution_service.execute_agent(
                agent_id=agent_id,
                user_id=request_data.user_id,
                project_id=request_data.project_id,
                input_text=request_data.input_text,
                enable_persona=request_data.enable_persona
            ):
                # SSE格式：data: {chunk}\n\n
                yield f"data: {json.dumps({'content': chunk}, ensure_ascii=False)}\n\n"
            # 结束标记
            yield "data: [DONE]\n\n"
        except Exception as e:
            logger.error(f"Agent执行失败: {e}")
            error_msg = json.dumps({"error": str(e)}, ensure_ascii=False)
            yield f"data: {error_msg}\n\n"
    
    return StreamingResponse(
        generate_response(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )


@router.get("/projects/{project_id}/persona")
async def get_project_persona(
    project_id: int,
    user_id: int,
    db: AsyncSession = Depends(_get_db),
):
    """
    获取项目的IP人设配置

    用于前端展示当前用户的IP设置
    """
    result = await db.execute(
        select(Project).filter(
            Project.id == project_id,
            Project.user_id == user_id,
            Project.is_deleted == False,
        )
    )
    project = result.scalar_one_or_none()

    if not project:
        raise NotFoundException(msg="项目不存在")

    data = {
        "project_id": project.id,
        "project_name": project.name,
        "persona_settings": project.persona_settings,
    }
    return success(data=data, msg="获取成功")


@router.post("/build-prompt")
async def build_execution_prompt(
    agent_id: int,
    user_id: int,
    project_id: int,
    input_text: str,
    enable_persona: bool = True,
    db: AsyncSession = Depends(_get_db),
):
    """
    仅构建Prompt，不执行LLM调用
    
    用于调试和预览
    """
    # 验证输入
    if not input_text or not input_text.strip():
        raise BadRequestException(msg="用户输入不能为空")
    
    # 获取Agent
    result = await db.execute(select(Agent).filter(Agent.id == agent_id))
    agent = result.scalar_one_or_none()
    if not agent:
        raise NotFoundException(msg="Agent不存在")
    
    # 获取IP基因
    persona_prompt = None
    if enable_persona:
        result = await db.execute(
            select(Project).filter(
                Project.id == project_id,
                Project.user_id == user_id,
                Project.is_deleted == False,
            )
        )
        project = result.scalar_one_or_none()
        
        if project and (project.persona_settings or project.master_prompt):
            persona_prompt = PromptBuilder.extract_persona_prompt(
                project.persona_settings or {},
                master_prompt=project.master_prompt
            )
    
    # 调用路由模块
    master_router = MasterRouter()
    routing_result = await master_router.route(
        db=db,
        agent=agent,
        user_input=input_text
    )
    
    # 调用Prompt Engine组装Prompt
    prompt_engine = PromptEngine()
    prompt_result = await prompt_engine.assemble_prompt(
        db=db,
        agent=agent,
        selected_skill_ids=routing_result.selected_skill_ids,
        skill_variables=agent.skill_variables or {},
        persona_prompt=persona_prompt,
        user_input=input_text
    )
    
    data = {
        "full_prompt": prompt_result.system_prompt,
        "user_message": prompt_result.user_message,
        "persona_enabled": enable_persona and bool(persona_prompt),
        "agent_mode": agent.agent_mode,
        "skills_applied": prompt_result.skills_applied,
        "token_count": prompt_result.token_count,
        "routing_method": routing_result.routing_method,
    }
    return success(data=data, msg="构建成功")
