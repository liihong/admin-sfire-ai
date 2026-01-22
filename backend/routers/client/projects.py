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
from constants.agent import get_agent_config, AgentType, DEFAULT_MODEL_ID
from services.content import AIService
from schemas.ai import ChatMessage

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
    
    通过智能体对话的形式收集IP信息，使用IP_COLLECTOR智能体进行引导式问答
    """
    try:
        # 获取IP采集智能体配置
        agent_config = get_agent_config(AgentType.IP_COLLECTOR)
        
        # 构建消息列表（包含系统提示词）
        messages = [
            {"role": "system", "content": agent_config["system_prompt"]}
        ]
        
        # 添加历史对话消息
        for msg in request.messages:
            if isinstance(msg, dict):
                role = msg.get("role", "user")
                content = msg.get("content", "")
                if content:
                    messages.append({"role": role, "content": content})
        
        # 如果没有用户消息，添加一个初始提示
        if not any(msg.get("role") == "user" for msg in request.messages):
            messages.append({
                "role": "user",
                "content": "你好，我想创建一个新的IP项目，请帮我收集相关信息。"
            })
        
        # 调用AI服务
        ai_service = AIService(db)

        # 从环境变量读取模型配置，使用预定义的默认值
        from core.config import settings
        model_id = settings.AI_COLLECT_MODEL_ID or DEFAULT_MODEL_ID
        
        # 如果环境变量中指定了API Key和Base URL，优先使用
        # 否则 AIService 会从数据库读取模型配置，或使用默认环境变量
        response = await ai_service.chat(
            messages=messages,
            model=model_id,
            temperature=agent_config.get("temperature", 0.7),
            max_tokens=agent_config.get("max_tokens", 1024)
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
        
        # 判断是否收集完成（简单判断：如果AI提到"完成"、"总结"等关键词）
        is_complete = any(keyword in ai_reply for keyword in ["完成", "总结", "确认", "以上", "这些信息"])
        
        # 构建响应
        response_data = IPCollectResponse(
            reply=ai_reply,
            next_step=request.step + 1 if request.step is not None else None,
            collected_info=request.context,
            is_complete=is_complete
        )
        
        return success(data=response_data.model_dump(), msg="对话成功")
        
    except Exception as e:
        from loguru import logger
        logger.error(f"AI采集对话失败: {e}")
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

