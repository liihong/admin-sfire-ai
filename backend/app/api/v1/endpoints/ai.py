"""
AI Chat Endpoints
AI 对话相关接口（用于智能体调试中心）
"""
from typing import Optional
from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from app.db import get_db
from app.api.deps import get_current_user
from app.models.admin_user import AdminUser
from app.schemas.ai import ChatRequest
from app.services.ai import AIService

router = APIRouter()


@router.post("/chat/stream", summary="流式对话接口")
async def chat_stream(
    request: ChatRequest,
    current_user: AdminUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    SSE 流式对话接口
    
    用于智能体调试中心的实时对话测试
    支持流式输出，实时返回AI回复内容
    
    Args:
        request: 对话请求参数
        current_user: 当前登录用户（通过依赖注入获取）
        db: 数据库会话
    
    Returns:
        StreamingResponse: SSE 流式响应
    """
    ai_service = AIService(db)
    
    async def generate():
        """生成器函数，用于流式输出"""
        try:
            async for chunk in ai_service.stream_chat(
                messages=request.messages,
                model=request.model or "gpt-3.5-turbo",
                temperature=request.temperature,
                max_tokens=request.max_tokens,
                top_p=request.top_p,
                frequency_penalty=request.frequency_penalty,
                presence_penalty=request.presence_penalty,
            ):
                # SSE 格式：data: {json}\n\n
                yield f"data: {chunk}\n\n"
            
            # 发送结束标记
            yield "data: [DONE]\n\n"
        except Exception as e:
            logger.error(f"Stream chat error: {e}")
            error_chunk = {
                "error": {
                    "message": str(e),
                    "type": type(e).__name__
                }
            }
            yield f"data: {error_chunk}\n\n"
    
    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # 禁用Nginx缓冲
        }
    )


@router.post("/chat", summary="非流式对话接口")
async def chat(
    request: ChatRequest,
    current_user: AdminUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    非流式对话接口
    
    返回完整的对话响应（不流式输出）
    """
    ai_service = AIService(db)
    response = await ai_service.chat(
        messages=request.messages,
        model=request.model or "gpt-3.5-turbo",
        temperature=request.temperature,
        max_tokens=request.max_tokens,
        top_p=request.top_p,
        frequency_penalty=request.frequency_penalty,
        presence_penalty=request.presence_penalty,
    )
    
    from app.utils.response import success
    return success(data=response)

