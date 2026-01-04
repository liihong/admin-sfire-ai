"""
AI Chat Schemas
AI 对话相关 Schema
"""
from typing import List, Optional, Literal
from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    """聊天消息"""
    role: Literal["system", "user", "assistant"] = Field(..., description="消息角色")
    content: str = Field(..., description="消息内容")
    timestamp: Optional[int] = Field(None, description="时间戳")


class ChatRequest(BaseModel):
    """聊天请求"""
    messages: List[ChatMessage] = Field(..., description="消息列表")
    model: str = Field(..., description="模型ID")
    temperature: Optional[float] = Field(0.7, ge=0, le=2, description="温度参数")
    max_tokens: Optional[int] = Field(2000, ge=1, description="最大token数")
    top_p: Optional[float] = Field(1.0, ge=0, le=1, description="Top P采样")
    frequency_penalty: Optional[float] = Field(0.0, ge=-2, le=2, description="频率惩罚")
    presence_penalty: Optional[float] = Field(0.0, ge=-2, le=2, description="存在惩罚")
    stream: Optional[bool] = Field(False, description="是否流式输出")


class ChatCompletionResponse(BaseModel):
    """聊天完成响应（非流式）"""
    id: str = Field(..., description="响应ID")
    model: str = Field(..., description="模型名称")
    message: ChatMessage = Field(..., description="回复消息")
    usage: Optional[dict] = Field(None, description="使用统计")
    finish_reason: Optional[str] = Field(None, description="完成原因")

