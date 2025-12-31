"""
AI Chat Schemas
AI 对话相关 Schema
"""
from typing import List, Optional, Literal
from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    """对话消息"""
    role: Literal["user", "assistant", "system"] = Field(..., description="消息角色")
    content: str = Field(..., description="消息内容")


class ChatRequest(BaseModel):
    """对话请求参数"""
    messages: List[ChatMessage] = Field(..., description="消息列表", min_length=1)
    model: Optional[str] = Field(None, description="模型名称，如 gpt-3.5-turbo, gpt-4")
    temperature: Optional[float] = Field(0.7, ge=0, le=2, description="温度参数（0-2）")
    max_tokens: Optional[int] = Field(2000, ge=1, le=32000, description="最大token数")
    top_p: Optional[float] = Field(1.0, ge=0, le=1, description="Top P 采样")
    frequency_penalty: Optional[float] = Field(0.0, ge=-2, le=2, description="频率惩罚")
    presence_penalty: Optional[float] = Field(0.0, ge=-2, le=2, description="存在惩罚")
    stream: Optional[bool] = Field(False, description="是否流式输出")


class ChatResponse(BaseModel):
    """对话响应"""
    id: str = Field(..., description="响应ID")
    model: str = Field(..., description="使用的模型")
    message: ChatMessage = Field(..., description="回复消息")
    usage: Optional[dict] = Field(None, description="Token使用情况")
    finish_reason: Optional[str] = Field(None, description="完成原因")

