"""
MiniProgram Project Endpoints
小程序项目管理接口
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from db import get_db
from models.user import User
from core.deps import get_current_miniprogram_user
from services.project import ProjectService
from schemas.project import (
    ProjectCreate,
    ProjectUpdate,
    ProjectSwitchRequest,
    ProjectListResponse,
    ProjectSingleResponse,
    ProjectResponse,
    INDUSTRY_OPTIONS,
    TONE_OPTIONS,
)
from utils.response import success
from utils.exceptions import NotFoundException

router = APIRouter()


@router.get("")
async def list_projects(
    current_user: User = Depends(get_current_miniprogram_user),
    db: AsyncSession = Depends(get_db)
):
    """获取当前用户的所有项目列表，按最后修改时间倒序排列"""
    project_service = ProjectService(db)
    
    projects = await project_service.get_projects_by_user(current_user.id)
    active_project_id = await project_service.get_active_project(current_user.id)
    
    # 转换为响应格式（兼容前端字段名）
    project_list = []
    for project in projects:
        is_active = (active_project_id is not None and project.id == active_project_id)
        project_response = ProjectResponse.from_orm_with_active(project, is_active=is_active)
        project_dict = project_response.model_dump()
        
        # 转换为前端期望的字段格式
        persona_settings = project_dict.get("persona_settings", {})
        # 处理 ID：如果是 UUID，保持字符串；如果是数字，转换为数字
        project_id = project_dict.get("id", "")
        try:
            # 尝试转换为数字（如果后端返回的是数字ID）
            project_id_num = int(project_id) if str(project_id).isdigit() else project_id
        except (ValueError, TypeError):
            project_id_num = project_id
        
        frontend_project = {
            "id": project_id_num,
            "name": project_dict.get("name", ""),
            "industry": project_dict.get("industry", ""),
            "tone": persona_settings.get("tone", "") if isinstance(persona_settings, dict) else "",
            "ipPersona": persona_settings.get("introduction", "") if isinstance(persona_settings, dict) else "",
            "isActive": project_dict.get("is_active", False),
            "createdAt": project_dict.get("created_at", "").isoformat() if project_dict.get("created_at") else "",
            "updatedAt": project_dict.get("updated_at", "").isoformat() if project_dict.get("updated_at") else ""
        }
        project_list.append(frontend_project)
    
    return success(
        data={
            "success": True,
            "projects": project_list,
            "active_project_id": str(active_project_id) if active_project_id else None
        },
        msg="获取成功"
    )


@router.post("", response_model=ProjectSingleResponse)
async def create_project(
    data: ProjectCreate,
    current_user: User = Depends(get_current_miniprogram_user),
    db: AsyncSession = Depends(get_db)
):
    """创建新项目"""
    project_service = ProjectService(db)
    
    project = await project_service.create_project(current_user.id, data)
    project_response = ProjectResponse.from_orm_with_active(project, is_active=False)
    
    return ProjectSingleResponse(success=True, project=project_response)


@router.get("/active", response_model=ProjectSingleResponse)
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
    return ProjectSingleResponse(success=True, project=project_response)


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
async def get_project_options():
    """获取项目配置选项（行业赛道和语气风格）"""
    return success(
        data={
            "success": True,
            "industries": INDUSTRY_OPTIONS,
            "tones": TONE_OPTIONS
        },
        msg="获取成功"
    )


@router.get("/{project_id}", response_model=ProjectSingleResponse)
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
    return ProjectSingleResponse(success=True, project=project_response)


@router.put("/{project_id}", response_model=ProjectSingleResponse)
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
    
    return ProjectSingleResponse(success=True, project=project_response)


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

