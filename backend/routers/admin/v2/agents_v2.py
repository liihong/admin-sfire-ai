"""
Agent管理路由（v2版本）
后台管理接口，支持技能组装模式
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from loguru import logger

from core.deps import _get_db
from schemas.v2.agent import (
    AgentCreateV2,
    AgentUpdateV2,
    AgentResponseV2,
    PromptPreviewRequest,
    PromptPreviewResponse,
    RoutingPreviewRequest,
    RoutingPreviewResponse,
)
from services.agent.admin import AgentServiceV2
from services.shared.prompt_builder import PromptBuilder
from services.routing import MasterRouter, SkillRouter, PromptEngine
from core.config import settings
from utils.response import success, page_response
from utils.exceptions import NotFoundException, BadRequestException
from models.agent import Agent
from models.skill_library import SkillLibrary

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
                "is_system": agent.is_system,
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


@router.post("/{agent_id}/routing-preview")
async def preview_intelligent_routing(
    agent_id: int,
    request_data: RoutingPreviewRequest,
    db: AsyncSession = Depends(_get_db),
):
    """
    预览智能路由结果

    功能：
    1. 根据用户输入测试智能路由
    2. 展示选中和未选中的技能
    3. 对比Token使用量
    4. 返回最终组装的Prompt

    注意：此接口不注入IP基因（仅用于后台调试）
    """
    try:
        # 1. 获取Agent
        result = await db.execute(select(Agent).filter(Agent.id == agent_id))
        agent = result.scalar_one_or_none()
        if not agent:
            raise NotFoundException(msg="Agent不存在")

        # 2. 验证Agent配置
        if agent.agent_mode != 1:
            raise BadRequestException(msg="该Agent未启用技能组装模式")

        if not agent.skill_ids or len(agent.skill_ids) == 0:
            raise BadRequestException(msg="该Agent未配置技能")

        agent_skill_ids = agent.skill_ids
        skill_variables = agent.skill_variables or {}
        routing_description = agent.routing_description or ""

        # 3. 使用新的路由模块执行智能路由
        # 从配置读取路由Agent ID和LLM模型ID
        router_agent_id = None
        if settings.ROUTER_AGENT_ID:
            try:
                router_agent_id = int(settings.ROUTER_AGENT_ID)
            except (ValueError, TypeError):
                logger.warning(f"ROUTER_AGENT_ID配置无效: {settings.ROUTER_AGENT_ID}")
        
        skill_router = SkillRouter()
        
        # 如果Agent启用了路由，使用SkillRouter进行路由（支持用户指定的参数）
        if agent.is_routing_enabled == 1:
            routing_result = await skill_router.route_skills(
                db=db,
                agent_skill_ids=agent_skill_ids,
                user_input=request_data.user_input,
                routing_description=routing_description,
                use_vector=request_data.use_vector,
                top_k=request_data.top_k,
                threshold=request_data.threshold,
                router_agent_id=router_agent_id
            )
        else:
            # Agent未启用路由，使用MasterRouter（会返回全部技能）
            master_router = MasterRouter()
            routing_result = await master_router.route(
                db=db,
                agent=agent,
                user_input=request_data.user_input
            )
        
        selected_skill_ids = routing_result.selected_skill_ids
        routing_method = routing_result.routing_method
        static_skill_ids = routing_result.static_skill_ids
        dynamic_skill_ids = routing_result.dynamic_skill_ids
        
        logger.info(
            f"路由结果: 选中{len(selected_skill_ids)}个技能, "
            f"静态={len(static_skill_ids)}个, "
            f"动态规则={len(dynamic_skill_ids)}个, "
            f"路由方法={routing_method}"
        )

        # 4. 获取所有技能详情
        all_skill_ids = agent_skill_ids
        result = await db.execute(
            select(SkillLibrary).filter(SkillLibrary.id.in_(all_skill_ids))
        )
        all_skills = result.scalars().all()
        skills_map = {s.id: s for s in all_skills}

        # 6. 构建选中和未选中的技能列表
        selected_skills = []
        rejected_skills = []

        # 计算相似度（用于展示）
        if routing_method == "vector":
            # 使用向量相似度
            from services.skill import get_skill_embedding_service
            skill_embedding_service = get_skill_embedding_service()
            query = f"{request_data.user_input}\n{routing_description}"

            similar_skills = await skill_embedding_service.search_similar_skills(
                query_text=query,
                top_k=len(all_skill_ids),
                threshold=0.0  # 获取所有结果的相似度
            )
            similarity_map = {skill_id: sim for skill_id, sim, _ in similar_skills}
        elif routing_method == "keywords":
            # 使用关键词相似度
            input_keywords = PromptBuilder._extract_keywords(request_data.user_input)
            routing_keywords = PromptBuilder._extract_keywords(routing_description)
            similarity_map = {}

            for skill in all_skills:
                skill_keywords = PromptBuilder._extract_keywords(
                    skill.meta_description or skill.name
                )
                score = PromptBuilder._calculate_relevance(
                    input_keywords, skill_keywords, routing_keywords
                )
                similarity_map[skill.id] = score
        else:
            # static模式，没有相似度
            similarity_map = {}

        # 分类技能并标记静态/动态
        for skill_id in all_skill_ids:
            skill = skills_map.get(skill_id)
            if not skill:
                continue

            similarity = similarity_map.get(skill_id, 0.0)
            skill_info = {
                "id": skill.id,
                "name": skill.name,
                "category": skill.category,
                "similarity": round(similarity, 3),
                "meta_description": skill.meta_description,
                "is_static": skill_id in static_skill_ids,
                "is_dynamic": skill_id in dynamic_skill_ids
            }

            if skill_id in selected_skill_ids:
                selected_skills.append(skill_info)
            else:
                rejected_skills.append(skill_info)

        # 按相似度排序
        selected_skills.sort(key=lambda x: x["similarity"], reverse=True)
        rejected_skills.sort(key=lambda x: x["similarity"], reverse=True)

        # 7. 使用PromptEngine组装Prompt（使用选中的技能）
        prompt_engine = PromptEngine()
        prompt_result = await prompt_engine.assemble_prompt(
            db=db,
            agent=agent,
            selected_skill_ids=selected_skill_ids,
            skill_variables=skill_variables,
            persona_prompt=None,  # 预览接口不注入IP基因
            user_input=request_data.user_input
        )
        final_prompt = prompt_result.system_prompt
        token_routed = prompt_result.token_count

        # 8. 计算全量加载的Token（用于对比）
        full_prompt_result = await prompt_engine.assemble_prompt(
            db=db,
            agent=agent,
            selected_skill_ids=agent_skill_ids,
            skill_variables=skill_variables,
            persona_prompt=None,
            user_input=request_data.user_input
        )
        token_full = full_prompt_result.token_count

        # 8. 计算节省比例
        saved_percent = 0.0
        if token_full > 0:
            saved_percent = round((1 - token_routed / token_full) * 100, 1)

        token_comparison = {
            "full": token_full,
            "routed": token_routed,
            "saved_percent": saved_percent
        }

        data = RoutingPreviewResponse(
            selected_skills=selected_skills,
            rejected_skills=rejected_skills,
            token_comparison=token_comparison,
            final_prompt=final_prompt,
            routing_method=routing_method
        ).model_dump()

        logger.info(
            f"路由预览成功: Agent={agent.name}, "
            f"选中{len(selected_skills)}个, "
            f"Token节省{saved_percent}%, "
            f"方法={routing_method}"
        )
        return success(data=data, msg="预览成功")

    except (NotFoundException, BadRequestException):
        raise
    except Exception as e:
        logger.error(f"路由预览失败: {e}")
        raise BadRequestException(msg=f"预览失败: {str(e)}")
