"""
顶妈（dingma）C端路由
独立于主程序 creation.py，不影响主程序 /chat。
"""
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from core.client_public_scope import resolve_optional_public_tenant_id
from core.deps import get_current_miniprogram_user
from db import get_db
from models.user import User
from routers.client.creation import ChatRequest
from services.dingma.chat_executor import generate_dingma_chat

router = APIRouter()


@router.post("/chat")
async def dingma_chat(
    request: ChatRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_miniprogram_user),
    db: AsyncSession = Depends(get_db),
    scoped_public_tenant_id: Optional[int] = Depends(resolve_optional_public_tenant_id),
):
    """
    dingma 专用对话接口：自动注入产品知识库（copywriting 模式）。
    主程序 /chat 不受影响。
    """
    return await generate_dingma_chat(
        request=request,
        background_tasks=background_tasks,
        current_user=current_user,
        db=db,
        scoped_public_tenant_id=scoped_public_tenant_id,
    )
