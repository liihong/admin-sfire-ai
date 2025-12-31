"""
Agent Management Endpoints
智能体管理相关接口
"""
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.schemas.agent import (
    AgentCreate,
    AgentUpdate,
    AgentQueryParams,
    AgentStatusUpdate,
    AgentSortUpdate,
    BatchSortRequest,
)
from app.services.agent import AgentService
from app.utils.response import success, page_response
from app.utils.serializers import agent_to_response
from app.constants.agent import PROMPT_TEMPLATES, AVAILABLE_MODELS

router = APIRouter()


@router.get("", summary="获取智能体列表")
async def get_agents(
    pageNum: int = Query(1, ge=1, description="页码"),
    pageSize: int = Query(10, ge=1, le=100, description="每页数量"),
    name: Optional[str] = Query(None, description="智能体名称（模糊查询）"),
    status: Optional[int] = Query(None, description="状态：0-下架, 1-上架"),
    db: AsyncSession = Depends(get_db),
):
    """
    获取智能体列表（分页）
    
    支持按名称、状态筛选
    """
    agent_service = AgentService(db)
    
    params = AgentQueryParams(
        pageNum=pageNum,
        pageSize=pageSize,
        name=name,
        status=status,
    )
    
    result = await agent_service.get_agent_list(params)
    items = [agent_to_response(agent) for agent in result.list]
    
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
async def get_available_models():
    """获取可用模型列表"""
    return success(data=AVAILABLE_MODELS)


@router.get("/{agent_id}", summary="获取智能体详情")
async def get_agent(
    agent_id: int,
    db: AsyncSession = Depends(get_db),
):
    """获取智能体详情"""
    agent_service = AgentService(db)
    agent = await agent_service.get_agent_by_id(agent_id)
    return success(data=agent_to_response(agent))


@router.post("", summary="创建智能体")
async def create_agent(
    agent_data: AgentCreate,
    db: AsyncSession = Depends(get_db),
):
    """创建智能体"""
    agent_service = AgentService(db)
    agent = await agent_service.create_agent(agent_data)
    await db.commit()
    return success(data=agent_to_response(agent), message="创建成功")


@router.put("/{agent_id}", summary="更新智能体")
async def update_agent(
    agent_id: int,
    agent_data: AgentUpdate,
    db: AsyncSession = Depends(get_db),
):
    """更新智能体"""
    agent_service = AgentService(db)
    agent = await agent_service.update_agent(agent_id, agent_data)
    await db.commit()
    return success(data=agent_to_response(agent), message="更新成功")


@router.delete("/{agent_id}", summary="删除智能体")
async def delete_agent(
    agent_id: int,
    db: AsyncSession = Depends(get_db),
):
    """删除智能体"""
    agent_service = AgentService(db)
    await agent_service.delete_agent(agent_id)
    await db.commit()
    return success(message="删除成功")


@router.patch("/{agent_id}/status", summary="修改智能体状态")
async def change_agent_status(
    agent_id: int,
    status_data: AgentStatusUpdate,
    db: AsyncSession = Depends(get_db),
):
    """修改智能体状态（上架/下架）"""
    agent_service = AgentService(db)
    agent = await agent_service.update_status(agent_id, status_data.status)
    await db.commit()
    return success(data=agent_to_response(agent), message="状态更新成功")


@router.patch("/{agent_id}/sort", summary="修改智能体排序")
async def update_agent_sort(
    agent_id: int,
    sort_data: AgentSortUpdate,
    db: AsyncSession = Depends(get_db),
):
    """修改智能体排序"""
    agent_service = AgentService(db)
    agent = await agent_service.update_sort_order(agent_id, sort_data.sortOrder)
    await db.commit()
    return success(data=agent_to_response(agent), message="排序更新成功")


@router.post("/batch-sort", summary="批量修改排序")
async def batch_update_sort(
    batch_data: BatchSortRequest,
    db: AsyncSession = Depends(get_db),
):
    """批量修改智能体排序"""
    agent_service = AgentService(db)
    items = [{"id": item.id, "sortOrder": item.sortOrder} for item in batch_data.items]
    await agent_service.batch_update_sort(items)
    await db.commit()
    return success(message="批量排序更新成功")

