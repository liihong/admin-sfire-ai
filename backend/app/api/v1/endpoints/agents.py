"""
Agent Management Endpoints
智能体管理相关接口
"""
from typing import Optional
from fastapi import APIRouter, Depends, Query, Body
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.schemas.agent import (
    AgentCreate,
    AgentUpdate,
    AgentQueryParams,
    AgentResponse,
    AgentStatusUpdate,
    AgentSortUpdate,
    BatchSortRequest,
    PromptTemplate,
)
from app.services.agent import AgentService
from app.utils.response import success, page_response
from app.models.agent import Agent

router = APIRouter()


def _agent_to_response(agent: Agent) -> dict:
    """将 Agent 模型转换为响应格式"""
    from app.schemas.agent import AgentConfig
    
    # 处理配置参数
    config_data = agent.config or {}
    config = AgentConfig(**config_data)
    
    return {
        "id": str(agent.id),
        "name": agent.name,
        "icon": agent.icon,
        "description": agent.description or "",
        "systemPrompt": agent.system_prompt,
        "model": agent.model,
        "config": config.model_dump(),
        "sortOrder": agent.sort_order,
        "status": agent.status,
        "usageCount": agent.usage_count,
        "createTime": agent.created_at.strftime("%Y-%m-%d %H:%M:%S"),
        "updateTime": agent.updated_at.strftime("%Y-%m-%d %H:%M:%S") if agent.updated_at else "",
    }


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
    
    # 转换为响应格式
    # PageResult 使用 list 属性，不是 items
    items = [_agent_to_response(agent) for agent in result.list]
    
    return page_response(
        items=items,
        total=result.total,
        page_num=pageNum,
        page_size=pageSize,
    )


@router.get("/templates", summary="获取预设模板列表")
async def get_prompt_templates():
    """获取预设模板列表"""
    templates = [
        {
            "id": "1",
            "name": "通用助手",
            "content": "你是一个有用的AI助手，能够回答各种问题并提供帮助。",
            "category": "通用"
        },
        {
            "id": "2",
            "name": "代码助手",
            "content": "你是一个专业的编程助手，擅长编写、调试和优化代码。请提供清晰、可执行的代码示例。",
            "category": "编程"
        },
        {
            "id": "3",
            "name": "写作助手",
            "content": "你是一个专业的写作助手，能够帮助用户创作各种类型的文本内容，包括文章、故事、诗歌等。",
            "category": "写作"
        },
        {
            "id": "4",
            "name": "翻译助手",
            "content": "你是一个专业的翻译助手，能够准确翻译各种语言的内容，保持原意和风格。",
            "category": "翻译"
        },
        {
            "id": "5",
            "name": "数据分析师",
            "content": "你是一个数据分析专家，能够分析数据、生成报告并提供数据驱动的建议。",
            "category": "分析"
        },
    ]
    return success(data=templates)


@router.get("/models", summary="获取可用模型列表")
async def get_available_models():
    """获取可用模型列表"""
    models = [
        {
            "id": "gpt-4",
            "name": "GPT-4",
            "maxTokens": 8192
        },
        {
            "id": "gpt-3.5-turbo",
            "name": "GPT-3.5 Turbo",
            "maxTokens": 4096
        },
        {
            "id": "gpt-4-turbo",
            "name": "GPT-4 Turbo",
            "maxTokens": 128000
        },
    ]
    return success(data=models)


@router.get("/{agent_id}", summary="获取智能体详情")
async def get_agent(
    agent_id: int,
    db: AsyncSession = Depends(get_db),
):
    """获取智能体详情"""
    agent_service = AgentService(db)
    agent = await agent_service.get_agent_by_id(agent_id)
    return success(data=_agent_to_response(agent))


@router.post("", summary="创建智能体")
async def create_agent(
    agent_data: AgentCreate,
    db: AsyncSession = Depends(get_db),
):
    """创建智能体"""
    agent_service = AgentService(db)
    agent = await agent_service.create_agent(agent_data)
    await db.commit()
    return success(data=_agent_to_response(agent), message="创建成功")


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
    return success(data=_agent_to_response(agent), message="更新成功")


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
    return success(data=_agent_to_response(agent), message="状态更新成功")


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
    return success(data=_agent_to_response(agent), message="排序更新成功")


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

