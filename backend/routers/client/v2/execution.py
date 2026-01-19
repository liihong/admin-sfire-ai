"""
Agent执行路由（v2版本）
前端用户接口，支持IP基因注入
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from loguru import logger

from core.deps import _get_db
from schemas.v2.agent import (
    AgentExecuteRequest,
    AgentExecuteResponse,
)
from models.agent import Agent
from models.project import Project
from services.agent_service_v2 import AgentServiceV2
from services.prompt_builder import PromptBuilder
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
    执行Agent（支持IP基因注入）

    执行流程：
    1. 获取Agent配置
    2. 如果启用IP基因，注入用户的persona_settings
    3. 如果启用智能路由，根据输入选择技能
    4. 组装完整的Prompt
    5. 调用LLM生成回复

    注意：此接口仅组装Prompt，实际LLM调用需要额外实现
    """
    # 验证输入
    if not request_data.input_text or not request_data.input_text.strip():
        raise BadRequestException(msg="用户输入不能为空")

    # 1. 获取Agent
    result = await db.execute(select(Agent).filter(Agent.id == agent_id))
    agent = result.scalar_one_or_none()
    if not agent:
        raise NotFoundException(msg="Agent不存在")

    if agent.status != 1:
        raise BadRequestException(msg="Agent未上架")
    
    logger.info(f"执行Agent: {agent.name} (ID={agent_id}), 用户ID={request_data.user_id}")

    # 2. 获取用户项目（IP基因）
    project = None
    persona_prompt = ""
    if request_data.enable_persona:
        result = await db.execute(
            select(Project).filter(
                Project.id == request_data.project_id,
                Project.user_id == request_data.user_id,
                Project.is_deleted == False,
            )
        )
        project = result.scalar_one_or_none()

        if project and project.persona_settings:
            # 提取IP人设Prompt
            persona_prompt = PromptBuilder.extract_persona_prompt(
                project.persona_settings
            )

    # 3. 构建Agent Prompt
    agent_prompt = ""
    skills_applied = []

    agent_mode = agent.agent_mode

    if agent_mode == 1:
        # 技能组装模式
        skill_ids = agent.skill_ids or []
        skill_variables = agent.skill_variables or {}
        is_routing_enabled = agent.is_routing_enabled
        routing_description = agent.routing_description or ""

        # 如果启用智能路由，根据输入选择技能
        if is_routing_enabled and routing_description:
            skill_ids = await PromptBuilder.intelligent_routing(
                db,
                request_data.input_text,
                skill_ids,
                routing_description
            )
            logger.info(f"智能路由选择: {len(skill_ids)}个技能")

        # 组装Prompt
        if skill_ids:
            agent_prompt, token_count, skills_used = await PromptBuilder.build_prompt(
                db,
                skill_ids,
                skill_variables,
            )
            skills_applied = skill_ids
            logger.debug(f"Agent Prompt组装完成: {token_count} tokens")
        else:
            agent_prompt = agent.system_prompt
            logger.warning(f"Agent {agent.name} 技能模式但skill_ids为空，使用system_prompt")
    else:
        # 普通模式
        agent_prompt = agent.system_prompt

    # 4. 组装完整Prompt
    prompt_parts = []

    # 添加IP人设（如果有）
    if persona_prompt:
        prompt_parts.append(persona_prompt)

    # 添加Agent能力
    if agent_prompt:
        prompt_parts.append(agent_prompt)

    # 添加用户输入上下文
    prompt_parts.append(f"## 用户输入\n{request_data.input_text}")

    full_prompt = "\n\n".join(prompt_parts)

    # 5. 这里应该调用LLM，暂时返回模拟数据
    # TODO: 实现实际的LLM调用
    mock_response = f"这是模拟的AI回复。Agent: {agent.name}\n用户输入: {request_data.input_text}"

    try:
        # 增加使用次数
        await AgentServiceV2.increment_usage_count(db, agent_id)
    except Exception as e:
        logger.warning(f"更新使用次数失败: {e}")

    data = AgentExecuteResponse(
        response=mock_response,
        prompt_used=full_prompt,
        skills_applied=skills_applied,
    ).model_dump()
    
    logger.info(f"Agent执行完成: {agent.name}, 应用了{len(skills_applied)}个技能")
    return success(data=data, msg="执行成功")


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

    # 获取项目IP
    persona_prompt = ""
    if enable_persona:
        result = await db.execute(
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

    # 构建Agent Prompt
    agent_mode = agent.agent_mode
    agent_prompt = ""

    if agent_mode == 1:
        skill_ids = agent.skill_ids or []
        skill_variables = agent.skill_variables or {}

        if skill_ids:
            agent_prompt, token_count, _ = await PromptBuilder.build_prompt(
                db,
                skill_ids,
                skill_variables,
            )
            logger.debug(f"构建Prompt: {token_count} tokens")
        else:
            agent_prompt = agent.system_prompt
    else:
        agent_prompt = agent.system_prompt

    # 组装完整Prompt
    prompt_parts = []
    if persona_prompt:
        prompt_parts.append(persona_prompt)
    if agent_prompt:
        prompt_parts.append(agent_prompt)
    prompt_parts.append(f"## 用户输入\n{input_text}")

    full_prompt = "\n\n".join(prompt_parts)

    data = {
        "full_prompt": full_prompt,
        "persona_enabled": enable_persona and bool(persona_prompt),
        "agent_mode": agent_mode,
    }
    return success(data=data, msg="构建成功")
