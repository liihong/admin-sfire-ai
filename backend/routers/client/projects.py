"""
Client Project Endpoints
C端项目管理接口（小程序 & PC官网）
支持项目的创建、查询、更新、删除、切换等功能
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from db import get_db
from models.user import User
from core.deps import get_current_miniprogram_user, get_current_miniprogram_user_optional
from services.resource import ProjectService
from services.system import DictionaryService
from schemas.project import (
    ProjectCreate,
    ProjectUpdate,
    ProjectSwitchRequest,
    ProjectResponse,
    INDUSTRY_OPTIONS,
    TONE_OPTIONS,
    IPCollectRequest,
    IPCollectResponse,
    IPCompressRequest,
    IPCompressResponse,
)
from utils.response import success
from utils.exceptions import NotFoundException, BadRequestException
from services.agent.core import AgentExecutor
from services.routing import PromptEngine
from services.content import AIService
from models.agent import Agent
from sqlalchemy import select
from loguru import logger

router = APIRouter()


def _build_frontend_project(project_dict: dict) -> dict:
    """
    将项目数据转换为前端期望的扁平化格式
    
    persona_settings 字段会被展开为独立字段
    """
    persona_settings = project_dict.get("persona_settings", {})
    if not isinstance(persona_settings, dict):
        persona_settings = {}
    
    # 处理 ID：如果是 UUID，保持字符串；如果是数字，转换为数字
    project_id = project_dict.get("id", "")
    try:
        project_id_num = int(project_id) if str(project_id).isdigit() else project_id
    except (ValueError, TypeError):
        project_id_num = project_id
    
    return {
        "id": project_id_num,
        "name": project_dict.get("name", ""),
        "industry": project_dict.get("industry", ""),
        # 头像相关字段
        "avatar_letter": project_dict.get("avatar_letter", ""),
        "avatar_color": project_dict.get("avatar_color", "#3B82F6"),
        # 人设字段（扁平化，与 persona_settings 一一对应）
        "introduction": persona_settings.get("introduction", ""),
        "tone": persona_settings.get("tone", ""),
        "target_audience": persona_settings.get("target_audience", ""),
        "content_style": persona_settings.get("content_style", ""),
        "catchphrase": persona_settings.get("catchphrase", ""),
        "keywords": persona_settings.get("keywords", []),
        "taboos": persona_settings.get("taboos", []),
        "benchmark_accounts": persona_settings.get("benchmark_accounts", []),
        # 其他字段
        "isActive": project_dict.get("is_active", False),
        "createdAt": project_dict.get("created_at", "").isoformat() if project_dict.get("created_at") else "",
        "updatedAt": project_dict.get("updated_at", "").isoformat() if project_dict.get("updated_at") else ""
    }


@router.get("")
async def list_projects(
    current_user: Optional[User] = Depends(get_current_miniprogram_user_optional),
    db: AsyncSession = Depends(get_db)
):
    """获取当前用户的所有项目列表，按最后修改时间倒序排列（支持游客模式）"""
    project_service = ProjectService(db)

    # 游客模式：返回空列表
    if current_user is None:
        return success(
            data={
                "success": True,
                "projects": [],
                "active_project_id": None,
                "is_guest": True
            },
            msg="获取成功（游客模式）"
        )

    # 已登录用户：获取项目列表
    projects = await project_service.get_projects_by_user(current_user.id)
    active_project_id = await project_service.get_active_project(current_user.id)

    # 转换为响应格式（扁平化人设字段）
    project_list = []
    for project in projects:
        is_active = (active_project_id is not None and project.id == active_project_id)
        project_response = ProjectResponse.from_orm_with_active(project, is_active=is_active)
        project_dict = project_response.model_dump()
        frontend_project = _build_frontend_project(project_dict)
        project_list.append(frontend_project)

    return success(
        data={
            "success": True,
            "projects": project_list,
            "active_project_id": str(active_project_id) if active_project_id else None,
            "is_guest": False
        },
        msg="获取成功"
    )


@router.post("")
async def create_project(
    data: ProjectCreate,
    current_user: User = Depends(get_current_miniprogram_user),
    db: AsyncSession = Depends(get_db)
):
    """创建新项目"""
    project_service = ProjectService(db)
    
    project = await project_service.create_project(current_user.id, data)
    project_response = ProjectResponse.from_orm_with_active(project, is_active=False)
    project_dict = project_response.model_dump()
    frontend_project = _build_frontend_project(project_dict)
    
    return success(data=frontend_project, msg="创建成功")


@router.get("/active")
async def get_active_project_info(
    current_user: User = Depends(get_current_miniprogram_user),
    db: AsyncSession = Depends(get_db)
):
    """获取当前激活的项目详情"""
    project_service = ProjectService(db)
    
    active_id = await project_service.get_active_project(current_user.id)
    if not active_id:
        raise NotFoundException("没有激活的项目")
    
    project = await project_service.get_project_by_id(active_id, user_id=current_user.id)
    if not project:
        raise NotFoundException("激活的项目不存在")
    
    project_response = ProjectResponse.from_orm_with_active(project, is_active=True)
    project_dict = project_response.model_dump()
    frontend_project = _build_frontend_project(project_dict)
    
    return success(data=frontend_project, msg="获取成功")


@router.post("/switch")
async def switch_project(
    data: ProjectSwitchRequest,
    current_user: User = Depends(get_current_miniprogram_user),
    db: AsyncSession = Depends(get_db)
):
    """切换当前激活的项目"""
    project_service = ProjectService(db)
    
    try:
        project_id = int(data.project_id)
    except (ValueError, TypeError):
        raise NotFoundException("无效的项目ID格式")
    
    # 验证项目是否存在且属于当前用户
    project = await project_service.get_project_by_id(project_id, user_id=current_user.id)
    if not project:
        raise NotFoundException("项目不存在或无权访问")
    
    # 检查项目状态，冻结的项目不能切换
    from models.project import ProjectStatus
    if project.status == ProjectStatus.FROZEN.value:
        raise BadRequestException("该项目已冻结，无法切换。请续费会员以解锁。")
    
    await project_service.set_active_project(current_user.id, project_id)
    
    return success(
        data={
            "success": True,
            "message": f"已切换到项目: {project.name}",
            "project": ProjectResponse.from_orm_with_active(project, is_active=True).model_dump()
        },
        msg="切换成功"
    )


@router.get("/options")
async def get_project_options(
    db: AsyncSession = Depends(get_db)
):
    """
    获取项目配置选项（行业赛道和语气风格）
    
    优先从数据库读取，如果数据库中没有数据则使用默认值
    """
    dict_service = DictionaryService(db)
    
    # 从数据库获取行业赛道选项
    industries = await dict_service.get_items_by_code("industry", enabled_only=True)
    # 从数据库获取语气风格选项
    tones = await dict_service.get_items_by_code("tone", enabled_only=True)
    
    # 如果数据库中没有数据，使用默认值
    if not industries:
        industries = [{"label": item, "value": item} for item in INDUSTRY_OPTIONS]
    else:
        industries = [item.model_dump() for item in industries]
    
    if not tones:
        tones = [{"label": item, "value": item} for item in TONE_OPTIONS]
    else:
        tones = [item.model_dump() for item in tones]
    
    return success(
        data={
            "success": True,
            "industries": industries,
            "tones": tones
        },
        msg="获取成功"
    )


@router.get("/{project_id}")
async def get_project(
    project_id: int,
    current_user: User = Depends(get_current_miniprogram_user),
    db: AsyncSession = Depends(get_db)
):
    """获取指定项目详情"""
    project_service = ProjectService(db)
    
    project = await project_service.get_project_by_id(project_id, user_id=current_user.id)
    if not project:
        raise NotFoundException("项目不存在或无权访问")
    
    active_id = await project_service.get_active_project(current_user.id)
    is_active = (active_id == project_id)
    
    project_response = ProjectResponse.from_orm_with_active(project, is_active=is_active)
    project_dict = project_response.model_dump()
    # 转换为前端期望的扁平化格式，确保 id 为 number 类型
    frontend_project = _build_frontend_project(project_dict)
    
    return success(data=frontend_project, msg="获取成功")


@router.put("/{project_id}")
async def update_project_info(
    project_id: int,
    data: ProjectUpdate,
    current_user: User = Depends(get_current_miniprogram_user),
    db: AsyncSession = Depends(get_db)
):
    """更新项目信息"""
    project_service = ProjectService(db)
    
    project = await project_service.update_project(project_id, current_user.id, data)
    project_response = ProjectResponse.from_orm_with_active(project, is_active=False)
    project_dict = project_response.model_dump()
    frontend_project = _build_frontend_project(project_dict)
    
    return success(data=frontend_project, msg="更新成功")


@router.delete("/{project_id}")
async def delete_project_by_id(
    project_id: int,
    current_user: User = Depends(get_current_miniprogram_user),
    db: AsyncSession = Depends(get_db)
):
    """删除项目"""
    project_service = ProjectService(db)
    
    await project_service.delete_project(project_id, current_user.id)
    
    return success(data={"success": True, "message": "项目已删除"}, msg="删除成功")


@router.post("/ai-collect", summary="AI智能填写 - IP信息采集对话")
async def ai_collect_ip_info(
    request: IPCollectRequest,
    current_user: User = Depends(get_current_miniprogram_user),
    db: AsyncSession = Depends(get_db)
):
    """
    IP信息采集对话接口
    
    通过智能体对话的形式收集IP信息，使用数据库中配置的IP_COLLECTOR智能体进行引导式问答
    不注入IP基因，直接使用agent的system_prompt进行对话
    """
    try:
        # 1. 从数据库获取IP采集智能体配置
        from core.config import settings
        
        agent = None
        
        # 优先使用配置的agent ID
        if settings.IP_COLLECTOR_AGENT_ID:
            from sqlalchemy import or_
            agent_id = int(settings.IP_COLLECTOR_AGENT_ID)  # 确保是整数类型
            logger.info(f"尝试查找IP采集Agent: ID={agent_id}, 配置值={settings.IP_COLLECTOR_AGENT_ID}")
            
            # 先查询是否存在该Agent（不限制状态）
            result = await db.execute(
                select(Agent).filter(Agent.id == agent_id)
            )
            agent_check = result.scalar_one_or_none()
            
            if agent_check:
                logger.info(
                    f"找到Agent ID={agent_id}: name={agent_check.name}, "
                    f"is_system={agent_check.is_system}, status={agent_check.status}"
                )
                # 系统自用智能体可以绕过上架检查，普通智能体必须上架
                if agent_check.is_system == 1 or agent_check.status == 1:
                    agent = agent_check
                    logger.info(f"使用配置的IP_COLLECTOR_AGENT_ID={agent_id}")
                else:
                    logger.warning(
                        f"Agent ID={agent_id} 既不是系统自用（is_system=0）也未上架（status=0），"
                        f"无法使用"
                    )
            else:
                logger.warning(f"未找到Agent ID={agent_id}，将尝试通过名称查找")
        
        # 如果配置的ID不存在或不可用，通过名称查找
        if not agent:
            from sqlalchemy import or_
            logger.info("尝试通过名称'IP信息采集'查找Agent")
            result = await db.execute(
                select(Agent).filter(
                    Agent.name == "IP信息采集",
                    # 系统自用智能体可以绕过上架检查，普通智能体必须上架
                    or_(Agent.is_system == 1, Agent.status == 1)
                ).order_by(Agent.created_at.desc())
            )
            agent = result.scalar_one_or_none()
            if agent:
                logger.info(f"通过名称找到IP信息采集Agent: ID={agent.id}, is_system={agent.is_system}, status={agent.status}")
        
        # 如果还是找不到，抛出错误
        if not agent:
            error_msg = (
                f"未找到IP信息采集智能体配置。"
                f"配置的IP_COLLECTOR_AGENT_ID={settings.IP_COLLECTOR_AGENT_ID}，"
                f"请检查数据库中是否存在ID={settings.IP_COLLECTOR_AGENT_ID}的智能体，"
                f"且该智能体为系统自用（is_system=1）或已上架（status=1），"
                f"或者创建名称为'IP信息采集'的智能体"
            )
            logger.error(error_msg)
            raise NotFoundException(msg=error_msg)
        
        # 2. 构建历史对话消息列表
        conversation_messages = []
        
        # 处理历史对话消息
        for msg in request.messages:
            if isinstance(msg, dict):
                role = msg.get("role", "user")
                content = msg.get("content", "")
                if content:
                    conversation_messages.append({"role": role, "content": content})
        
        # 如果没有用户消息，添加一个初始提示
        if not any(msg.get("role") == "user" for msg in conversation_messages):
            conversation_messages.append({
                "role": "user",
                "content": "你好，我想创建一个新的IP项目，请帮我收集相关信息。"
            })
        
        # 获取最后一条用户消息（用于路由决策）
        user_input = ""
        for msg in reversed(conversation_messages):
            if msg.get("role") == "user":
                user_input = msg.get("content", "")
                break
        
        # 3. 使用AgentExecutor的路由和Prompt组装功能（不注入IP基因）
        executor = AgentExecutor(db)
        prompt_engine = PromptEngine()
        
        # 路由决策
        routing_result = await executor.master_router.route(
            db=db,
            agent=agent,
            user_input=user_input
        )
        
        # Prompt组装（不注入IP基因）
        prompt_result = await prompt_engine.assemble_prompt(
            db=db,
            agent=agent,
            selected_skill_ids=routing_result.selected_skill_ids,
            skill_variables=agent.skill_variables or {},
            persona_prompt=None,  # 不注入IP基因
            user_input=user_input
        )
        
        # 获取agent配置参数
        agent_config = agent.config or {}
        temperature = agent_config.get("temperature", 0.7)
        max_tokens = agent_config.get("maxTokens", agent_config.get("max_tokens", 2048))
        
        # 4. 构建完整的消息列表（包含系统提示词和历史对话）
        messages = [
            {"role": "system", "content": prompt_result.system_prompt}
        ]
        
        # 添加历史对话消息（排除system角色，因为已经添加了）
        for msg in conversation_messages:
            if msg.get("role") != "system":
                messages.append(msg)
        
        # 5. 使用AIService执行对话（支持历史消息）
        ai_service = AIService(db)
        
        # 解析模型ID（agent.model可能是数据库ID或模型标识）
        model_id = agent.model
        
        # 调用AI服务
        response = await ai_service.chat(
            messages=messages,
            model=model_id,
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        # 提取AI回复
        ai_reply = ""
        if isinstance(response, dict):
            if response.get("message"):
                ai_reply = response["message"].get("content", "")
            elif response.get("choices") and len(response["choices"]) > 0:
                ai_reply = response["choices"][0].get("message", {}).get("content", "")
            elif response.get("content"):
                ai_reply = response["content"]
        
        if not ai_reply:
            ai_reply = "抱歉，我暂时无法回复，请稍后再试。"
        
        # 获取token统计（如果有）
        token_count = 0
        if isinstance(response, dict) and response.get("usage"):
            usage = response["usage"]
            token_count = usage.get("total_tokens", 0)
        
        # 4. 判断是否收集完成（简单判断：如果AI提到"完成"、"总结"等关键词）
        is_complete = any(keyword in ai_reply for keyword in ["完成", "总结", "确认", "以上", "这些信息"])
        
        # 5. 构建响应
        response_data = IPCollectResponse(
            reply=ai_reply,
            next_step=request.step + 1 if request.step is not None else None,
            collected_info=request.context,
            is_complete=is_complete
        )
        
        logger.debug(f"IP信息采集对话完成: token_count={token_count}, is_complete={is_complete}")
        
        return success(data=response_data.model_dump(), msg="对话成功")
        
    except NotFoundException:
        raise
    except Exception as e:
        logger.error(f"AI采集对话失败: {e}", exc_info=True)
        raise BadRequestException(f"AI对话失败: {str(e)}")


@router.post("/ai-compress", summary="AI智能填写 - IP信息压缩")
async def ai_compress_ip_info(
    request: IPCompressRequest,
    current_user: User = Depends(get_current_miniprogram_user),
    db: AsyncSession = Depends(get_db)
):
    """
    AI总结压缩接口
    
    将收集到的IP信息压缩到极限字数，以控制token消耗
    - IP简介：压缩到200字以内
    - 目标受众：压缩到50字以内
    - 关键词：最多8个
    - 口头禅：保持简短
    """
    try:
        project_service = ProjectService(db)
        compressed_info = await project_service.compress_ip_info(request.raw_info)
        
        response_data = IPCompressResponse(compressed_info=compressed_info)
        
        return success(data=response_data.model_dump(), msg="压缩成功")
        
    except Exception as e:
        from loguru import logger
        logger.error(f"IP信息压缩失败: {e}")
        raise BadRequestException(f"信息压缩失败: {str(e)}")

