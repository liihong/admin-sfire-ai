"""
Agent Management Endpoints
智能体管理相关接口
"""
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db import get_db
from core.deps import get_current_admin_user
from core.tenant_helpers import resolve_admin_agent_scope_tenant_id
from models.admin_user import AdminUser
from models.llm_model import LLMModel
from schemas.agent import (
    AgentCreate,
    AgentUpdate,
    AgentQueryParams,
    AgentStatusUpdate,
    AgentSortUpdate,
    BatchSortRequest,
)
from services.agent import AgentService
from services.resource import LLMModelService
from utils.response import success, page_response
from utils.serializers import agent_to_response
from constants.agent import PROMPT_TEMPLATES

router = APIRouter()


@router.get("", summary="获取智能体列表")
async def get_agents(
    pageNum: int = Query(1, ge=1, description="页码"),
    pageSize: int = Query(10, ge=1, le=1000, description="每页数量"),
    name: Optional[str] = Query(None, description="智能体名称（模糊查询）"),
    status: Optional[int] = Query(None, description="状态：0-下架, 1-上架"),
    agentMode: Optional[int] = Query(
        None,
        description="智能体模式：0-普通模式, 1-Skill 组装模式",
    ),
    db: AsyncSession = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin_user),
):
    """
    获取智能体列表（分页）
    
    支持按名称、状态、智能体模式筛选
    返回 modelName 供列表展示（模型名称而非 ID）
    """
    agent_service = AgentService(db)
    scope_tid = await resolve_admin_agent_scope_tenant_id(
        db,
        admin_tenant_id=current_admin.tenant_id,
        admin_username=current_admin.username,
    )

    params = AgentQueryParams(
        pageNum=pageNum,
        pageSize=pageSize,
        name=name,
        status=status,
        agentMode=agentMode,
    )
    
    result = await agent_service.get_agent_list(
        params,
        scoped_tenant_id=scope_tid,
    )
    
    # 收集所有 agent 使用的 model ID，批量查询模型名称
    model_ids = [int(mid) for mid in {str(a.model) for a in result.list if a.model} if str(mid).isdigit()]
    model_name_map: dict[str, str] = {}
    if model_ids:
        stmt = select(LLMModel.id, LLMModel.name).where(LLMModel.id.in_(model_ids))
        rows = (await db.execute(stmt)).all()
        model_name_map = {str(r.id): r.name for r in rows}
    
    items = [
        agent_to_response(
            agent,
            model_name=model_name_map.get(str(agent.model), "未知"),
            viewer_scoped_tenant_id=scope_tid,
        )
        for agent in result.list
    ]
    
    return page_response(
        items=items,
        total=result.total,
        page_num=pageNum,
        page_size=pageSize,
    )


@router.get("/templates", summary="获取预设模板列表")
async def get_prompt_templates():
    """获取预设模板列表"""
    return success(data=PROMPT_TEMPLATES)


@router.get("/models", summary="获取可用模型列表")
async def get_available_models(
    db: AsyncSession = Depends(get_db),
):
    """
    获取可用模型列表
    
    从数据库读取启用的模型列表，格式兼容前端
    """
    llm_model_service = LLMModelService(db)
    models = await llm_model_service.get_enabled_models()
    
    # 转换为前端需要的格式（兼容原有格式）
    items = [
        {
            "id": str(model.id),  # 前端需要字符串格式的 ID
            "name": model.name,
            "maxTokens": 4096,  # 默认值，可以根据模型类型设置不同值
        }
        for model in models
    ]
    
    # 如果没有配置任何模型，返回空列表（前端可能有默认值处理）
    return success(data=items)


@router.get("/{agent_id}", summary="获取智能体详情")
async def get_agent(
    agent_id: int,
    db: AsyncSession = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin_user),
):
    """获取智能体详情"""
    agent_service = AgentService(db)
    scope_tid = await resolve_admin_agent_scope_tenant_id(
        db,
        admin_tenant_id=current_admin.tenant_id,
        admin_username=current_admin.username,
    )
    agent = await agent_service.get_agent_by_id(agent_id, scoped_tenant_id=scope_tid)
    return success(data=agent_to_response(agent, viewer_scoped_tenant_id=scope_tid))


@router.post("", summary="创建智能体")
async def create_agent(
    agent_data: AgentCreate,
    db: AsyncSession = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin_user),
):
    """创建智能体"""
    agent_service = AgentService(db)
    scope_tid = await resolve_admin_agent_scope_tenant_id(
        db,
        admin_tenant_id=current_admin.tenant_id,
        admin_username=current_admin.username,
    )
    agent = await agent_service.create_agent(agent_data, scoped_tenant_id=scope_tid)
    await db.commit()
    return success(data=agent_to_response(agent, viewer_scoped_tenant_id=scope_tid), msg="创建成功")


@router.put("/{agent_id}", summary="更新智能体")
async def update_agent(
    agent_id: int,
    agent_data: AgentUpdate,
    db: AsyncSession = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin_user),
):
    """更新智能体"""
    agent_service = AgentService(db)
    scope_tid = await resolve_admin_agent_scope_tenant_id(
        db,
        admin_tenant_id=current_admin.tenant_id,
        admin_username=current_admin.username,
    )
    agent = await agent_service.update_agent(agent_id, agent_data, scoped_tenant_id=scope_tid)
    await db.commit()
    return success(data=agent_to_response(agent, viewer_scoped_tenant_id=scope_tid), msg="更新成功")


@router.delete("/{agent_id}", summary="删除智能体")
async def delete_agent(
    agent_id: int,
    db: AsyncSession = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin_user),
):
    """删除智能体"""
    agent_service = AgentService(db)
    scope_tid = await resolve_admin_agent_scope_tenant_id(
        db,
        admin_tenant_id=current_admin.tenant_id,
        admin_username=current_admin.username,
    )
    await agent_service.delete_agent(agent_id, scoped_tenant_id=scope_tid)
    await db.commit()
    return success(msg="删除成功")


@router.patch("/{agent_id}/status", summary="修改智能体状态")
async def change_agent_status(
    agent_id: int,
    status_data: AgentStatusUpdate,
    db: AsyncSession = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin_user),
):
    """修改智能体状态（上架/下架）"""
    agent_service = AgentService(db)
    scope_tid = await resolve_admin_agent_scope_tenant_id(
        db,
        admin_tenant_id=current_admin.tenant_id,
        admin_username=current_admin.username,
    )
    agent = await agent_service.update_status(agent_id, status_data.status, scoped_tenant_id=scope_tid)
    await db.commit()
    return success(data=agent_to_response(agent, viewer_scoped_tenant_id=scope_tid), msg="状态更新成功")


@router.patch("/{agent_id}/sort", summary="修改智能体排序")
async def update_agent_sort(
    agent_id: int,
    sort_data: AgentSortUpdate,
    db: AsyncSession = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin_user),
):
    """修改智能体排序"""
    agent_service = AgentService(db)
    scope_tid = await resolve_admin_agent_scope_tenant_id(
        db,
        admin_tenant_id=current_admin.tenant_id,
        admin_username=current_admin.username,
    )
    agent = await agent_service.update_sort_order(agent_id, sort_data.sortOrder, scoped_tenant_id=scope_tid)
    await db.commit()
    return success(data=agent_to_response(agent, viewer_scoped_tenant_id=scope_tid), msg="排序更新成功")


@router.post("/batch-sort", summary="批量修改排序")
async def batch_update_sort(
    batch_data: BatchSortRequest,
    db: AsyncSession = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin_user),
):
    """批量修改智能体排序"""
    agent_service = AgentService(db)
    scope_tid = await resolve_admin_agent_scope_tenant_id(
        db,
        admin_tenant_id=current_admin.tenant_id,
        admin_username=current_admin.username,
    )
    items = [{"id": item.id, "sortOrder": item.sortOrder} for item in batch_data.items]
    await agent_service.batch_update_sort(items, scoped_tenant_id=scope_tid)
    await db.commit()
    return success(msg="批量排序更新成功")

