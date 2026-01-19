"""
Agent管理路由（v2版本）
后台管理接口，支持技能组装模式
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from core.deps import _get_db
from schemas.v2.agent import (
    AgentCreateV2,
    AgentUpdateV2,
    AgentResponseV2,
    PromptPreviewRequest,
    PromptPreviewResponse,
)
from services.agent_service_v2 import AgentServiceV2
from services.prompt_builder import PromptBuilder
from utils.response import success, page_response
from utils.exceptions import NotFoundException, BadRequestException

router = APIRouter(prefix="/agents", tags=["Agent管理（v2）"])


@router.get("/list")
async def get_agent_list(
    page: int = 1,
    size: int = 20,
    name: str = None,
    agent_mode: int = None,
    status: int = None,
    db: AsyncSession = Depends(_get_db),
):
    """
    获取Agent列表

    支持按名称、运行模式、状态筛选
    """
    try:
        agents, total = await AgentServiceV2.get_list(
            db,
            page=page,
            size=size,
            name=name,
            agent_mode=agent_mode,
            status=status,
        )

        # 转换为响应格式
        items = []
        for agent in agents:
            agent_dict = {
                "id": agent.id,
                "name": agent.name,
                "icon": agent.icon,
                "description": agent.description or "",
                "agent_mode": agent.agent_mode,
                "system_prompt": agent.system_prompt,
                "model": agent.model,
                "config": agent.config,
                "sort_order": agent.sort_order,
                "status": agent.status,
                "usage_count": agent.usage_count,
                "skill_ids": agent.skill_ids,
                "skill_variables": agent.skill_variables,
                "routing_description": agent.routing_description,
                "is_routing_enabled": agent.is_routing_enabled,
                "skills_detail": None,  # 列表接口不返回技能详情
                "created_at": agent.created_at,
                "updated_at": agent.updated_at,
            }
            items.append(AgentResponseV2(**agent_dict).model_dump())

        return page_response(
            items=items,
            total=total,
            page_num=page,
            page_size=size,
            msg="获取成功"
        )
    except Exception as e:
        logger.error(f"获取Agent列表失败: {e}")
        raise BadRequestException(msg="获取Agent列表失败")


@router.get("/{agent_id}")
async def get_agent_detail(
    agent_id: int,
    db: AsyncSession = Depends(_get_db),
):
    """
    获取Agent详情（包含技能详情）
    """
    agent_dict = await AgentServiceV2.get_detail_with_skills(db, agent_id)
    if not agent_dict:
        raise NotFoundException(msg="Agent不存在")
    return success(data=AgentResponseV2(**agent_dict).model_dump(), msg="获取成功")


@router.post("/")
async def create_agent(
    agent_data: AgentCreateV2,
    db: AsyncSession = Depends(_get_db),
):
    """
    创建Agent（支持技能模式）

    - agent_mode=0: 普通模式，直接使用system_prompt
    - agent_mode=1: 技能组装模式，使用skill_ids组装Prompt
    """
    try:
        # 验证技能模式下的必填字段
        if agent_data.agent_mode == 1:
            if not agent_data.skill_ids:
                raise BadRequestException(msg="技能模式下必须提供skill_ids")
        
        agent = await AgentServiceV2.create_with_skills(db, agent_data.model_dump())
        agent_dict = await AgentServiceV2.get_detail_with_skills(db, agent.id)
        logger.info(f"创建Agent成功: {agent.name} (ID={agent.id})")
        return success(data=AgentResponseV2(**agent_dict).model_dump(), msg="创建成功")
    except BadRequestException:
        raise
    except Exception as e:
        logger.error(f"创建Agent失败: {e}")
        raise BadRequestException(msg=f"创建Agent失败: {str(e)}")


@router.put("/{agent_id}")
async def update_agent(
    agent_id: int,
    update_data: AgentUpdateV2,
    db: AsyncSession = Depends(_get_db),
):
    """
    更新Agent（支持技能模式）
    """
    try:
        agent = await AgentServiceV2.update_with_skills(
            db,
            agent_id,
            update_data.model_dump(exclude_unset=True),
        )
        if not agent:
            raise NotFoundException(msg="Agent不存在")

        agent_dict = await AgentServiceV2.get_detail_with_skills(db, agent.id)
        logger.info(f"更新Agent成功: {agent.name} (ID={agent_id})")
        return success(data=AgentResponseV2(**agent_dict).model_dump(), msg="更新成功")
    except NotFoundException:
        raise
    except Exception as e:
        logger.error(f"更新Agent失败: {e}")
        raise BadRequestException(msg=f"更新Agent失败: {str(e)}")


@router.delete("/{agent_id}")
async def delete_agent(
    agent_id: int,
    db: AsyncSession = Depends(_get_db),
):
    """
    删除Agent
    """
    result = await AgentServiceV2.delete(db, agent_id)
    if not result:
        raise NotFoundException(msg="Agent不存在")
    return success(msg="删除成功")


@router.post("/{agent_id}/preview")
async def preview_agent_prompt(
    agent_id: int,
    request_data: PromptPreviewRequest,
    db: AsyncSession = Depends(_get_db),
):
    """
    预览Agent的完整Prompt

    根据skill_ids和skill_variables组装Prompt，并计算token数量
    """
    try:
        # 验证输入
        if not request_data.skill_ids:
            raise BadRequestException(msg="skill_ids不能为空")
        
        full_prompt, token_count, skills_used = await PromptBuilder.build_prompt(
            db,
            request_data.skill_ids,
            request_data.skill_variables,
        )

        data = PromptPreviewResponse(
            full_prompt=full_prompt,
            token_count=token_count,
            skills_used=skills_used,
        ).model_dump()
        
        logger.info(f"预览Prompt成功: Agent ID={agent_id}, {token_count} tokens, {len(skills_used)}个技能")
        return success(data=data, msg="预览成功")
    except BadRequestException:
        raise
    except Exception as e:
        logger.error(f"预览Prompt失败: {e}")
        raise BadRequestException(msg=f"预览失败: {str(e)}")


@router.post("/{agent_id}/mode")
async def switch_agent_mode(
    agent_id: int,
    agent_mode: int,
    db: AsyncSession = Depends(_get_db),
):
    """
    切换Agent运行模式

    - agent_mode=0: 普通模式
    - agent_mode=1: 技能组装模式
    """
    if agent_mode not in [0, 1]:
        raise BadRequestException(msg="agent_mode必须是0或1")
    
    agent = await AgentServiceV2.update_with_skills(
        db,
        agent_id,
        {"agent_mode": agent_mode}
    )
    if not agent:
        raise NotFoundException(msg="Agent不存在")

    agent_dict = await AgentServiceV2.get_detail_with_skills(db, agent.id)
    logger.info(f"切换Agent模式成功: {agent.name} (ID={agent_id}), mode={agent_mode}")
    return success(data=AgentResponseV2(**agent_dict).model_dump(), msg="切换成功")
