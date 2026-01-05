"""
AI Chat Endpoints
AI 对话相关接口
"""
import json
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from db import get_db
from schemas.ai import ChatRequest, ChatCompletionResponse
from services.ai import AIService
from utils.response import success

router = APIRouter()


@router.post("/chat", summary="AI对话（非流式）")
async def chat(
    request: ChatRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    AI对话接口（非流式）
    
    - **messages**: 消息列表
    - **model**: 模型ID
    - **temperature**: 温度参数（可选）
    - **max_tokens**: 最大token数（可选）
    """
    ai_service = AIService(db)
    
    # 转换消息格式
    messages = [
        {"role": msg.role, "content": msg.content}
        for msg in request.messages
    ]
    
    result = await ai_service.chat(
        messages=messages,
        model=request.model,
        temperature=request.temperature,
        max_tokens=request.max_tokens,
        top_p=request.top_p,
        frequency_penalty=request.frequency_penalty,
        presence_penalty=request.presence_penalty,
    )
    
    return success(data=result)


@router.post("/chat/stream", summary="AI对话（流式）")
async def chat_stream(
    request: ChatRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    AI对话接口（流式SSE）
    
    - **messages**: 消息列表
    - **model**: 模型ID
    - **temperature**: 温度参数（可选）
    - **max_tokens**: 最大token数（可选）
    - **stream**: 必须为 True（流式输出）
    """
    ai_service = AIService(db)
    
    # 转换消息格式
    messages = [
        {"role": msg.role, "content": msg.content}
        for msg in request.messages
    ]
    
    async def generate_stream():
        """生成SSE流"""
        try:
            async for chunk in ai_service.stream_chat(
                messages=messages,
                model=request.model,
                temperature=request.temperature,
                max_tokens=request.max_tokens,
                top_p=request.top_p,
                frequency_penalty=request.frequency_penalty,
                presence_penalty=request.presence_penalty,
            ):
                # 格式化为SSE格式
                yield f"data: {chunk}\n\n"
            
            # 发送结束标记
            yield "data: [DONE]\n\n"
        except Exception as e:
            error_chunk = json.dumps({
                "error": {
                    "message": str(e),
                    "type": type(e).__name__
                }
            })
            yield f"data: {error_chunk}\n\n"
    
    return StreamingResponse(
        generate_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )


@router.get("/models", summary="获取可用模型列表")
async def get_models(
    db: AsyncSession = Depends(get_db),
):
    """
    获取可用模型列表
    
    从数据库读取启用的模型列表
    """
    from services.llm_model import LLMModelService
    
    llm_model_service = LLMModelService(db)
    models = await llm_model_service.get_enabled_models()
    
    # 转换为前端需要的格式
    items = [
        {
            "id": str(model.id),
            "name": model.name,
            "model_id": model.model_id,
            "provider": model.provider,
        }
        for model in models
    ]
    
    return success(data=items)

