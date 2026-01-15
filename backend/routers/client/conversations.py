"""
对话会话管理路由
"""
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from db import get_db
from models.user import User
from core.deps import get_current_miniprogram_user
from services.conversation import ConversationService
from schemas.conversation import (
    ConversationCreate,
    ConversationUpdate,
    ConversationListParams,
    ConversationDetailResponse,
    ConversationResponse,
)
from utils.response import success, page_response
from utils.exceptions import NotFoundException

router = APIRouter()


@router.post("/conversations", summary="创建新会话")
async def create_conversation(
    conversation_data: ConversationCreate,
    current_user: User = Depends(get_current_miniprogram_user),
    db: AsyncSession = Depends(get_db)
):
    """
    创建新会话
    
    - **agent_id**: 智能体ID（可选）
    - **project_id**: 项目ID（可选）
    - **title**: 会话标题（可选，会自动生成）
    - **model_type**: 模型类型
    """
    service = ConversationService(db)
    conversation = await service.create_conversation(
        user_id=current_user.id,
        conversation_data=conversation_data
    )
    
    return success(data=ConversationResponse.model_validate(conversation), msg="创建成功")


@router.get("/conversations", summary="获取会话列表")
async def get_conversation_list(
    pageNum: int = Query(default=1, ge=1, description="页码"),
    pageSize: int = Query(default=10, ge=1, le=100, description="每页数量"),
    status: Optional[str] = Query(default=None, description="状态筛选: active/archived"),
    agent_id: Optional[int] = Query(default=None, description="智能体ID筛选"),
    project_id: Optional[int] = Query(default=None, description="项目ID筛选"),
    keyword: Optional[str] = Query(default=None, description="关键词搜索（标题）"),
    current_user: User = Depends(get_current_miniprogram_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取会话列表（分页）
    """
    params = ConversationListParams(
        pageNum=pageNum,
        pageSize=pageSize,
        status=status,
        agent_id=agent_id,
        project_id=project_id,
        keyword=keyword,
    )
    
    service = ConversationService(db)
    result = await service.list_conversations(
        user_id=current_user.id,
        params=params
    )
    
    # 转换为响应格式
    items = [ConversationResponse.model_validate(conv) for conv in result.list]
    
    return page_response(
        items=items,
        total=result.total,
        page_num=result.pageNum,
        page_size=result.pageSize,
        msg="获取成功"
    )


@router.get("/conversations/{conversation_id}", summary="获取会话详情")
async def get_conversation_detail(
    conversation_id: int,
    current_user: User = Depends(get_current_miniprogram_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取会话详情（包含消息列表）
    """
    service = ConversationService(db)
    conversation = await service.get_conversation_by_id(
        conversation_id=conversation_id,
        user_id=current_user.id
    )

    # 获取消息列表
    messages = await service.get_conversation_messages(conversation_id)

    # 构建响应 - 先转换为基础响应，再手动添加 messages
    from schemas.conversation import ConversationMessageResponse

    # 使用 ConversationResponse 而不是 ConversationDetailResponse
    base_data = ConversationResponse.model_validate(conversation).model_dump()

    # 手动添加 messages 和其他字段
    detail = ConversationDetailResponse(
        **base_data,
        messages=[ConversationMessageResponse.model_validate(msg) for msg in messages],
        agent_name=conversation.agent.name if conversation.agent else None,
        project_name=conversation.project.name if conversation.project else None,
    )

    return success(data=detail, msg="获取成功")


@router.put("/conversations/{conversation_id}/title", summary="更新会话标题")
async def update_conversation_title(
    conversation_id: int,
    title: str = Query(..., description="新标题"),
    current_user: User = Depends(get_current_miniprogram_user),
    db: AsyncSession = Depends(get_db)
):
    """
    更新会话标题
    """
    service = ConversationService(db)
    conversation = await service.update_conversation_title(
        conversation_id=conversation_id,
        title=title,
        user_id=current_user.id
    )
    
    return success(data=ConversationResponse.model_validate(conversation), msg="更新成功")


@router.delete("/conversations/{conversation_id}", summary="删除会话")
async def delete_conversation(
    conversation_id: int,
    current_user: User = Depends(get_current_miniprogram_user),
    db: AsyncSession = Depends(get_db)
):
    """
    删除会话（软删除）
    """
    service = ConversationService(db)
    await service.delete_conversation(
        conversation_id=conversation_id,
        user_id=current_user.id
    )
    
    return success(msg="删除成功")


@router.post("/conversations/{conversation_id}/archive", summary="归档会话")
async def archive_conversation(
    conversation_id: int,
    current_user: User = Depends(get_current_miniprogram_user),
    db: AsyncSession = Depends(get_db)
):
    """
    归档会话
    """
    service = ConversationService(db)
    conversation = await service.archive_conversation(
        conversation_id=conversation_id,
        user_id=current_user.id
    )
    
    return success(data=ConversationResponse.model_validate(conversation), msg="归档成功")















