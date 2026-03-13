"""
AI Chat Schemas
AI 对话相关 Schema
"""
from typing import List, Optional, Literal
from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    """聊天消息"""
    role: Literal["system", "user", "assistant"] = Field(..., description="消息角色：system-系统提示, user-用户, assistant-AI回复")
    content: str = Field(..., description="消息文本内容")
    timestamp: Optional[int] = Field(None, description="时间戳（可选）")


class ChatRequest(BaseModel):
    """聊天请求"""
    messages: List[ChatMessage] = Field(..., description="消息列表，格式：[{role, content}, ...]")
    model: str = Field(..., description="模型ID（对应llm_models表的model_id）")
    temperature: Optional[float] = Field(0.7, ge=0, le=2, description="温度参数，控制随机性，0-2，越高越随机")
    max_tokens: Optional[int] = Field(2000, ge=1, description="最大生成token数")
    top_p: Optional[float] = Field(1.0, ge=0, le=1, description="Top P采样，核采样参数")
    frequency_penalty: Optional[float] = Field(0.0, ge=-2, le=2, description="频率惩罚，降低重复")
    presence_penalty: Optional[float] = Field(0.0, ge=-2, le=2, description="存在惩罚，鼓励新话题")
    stream: Optional[bool] = Field(False, description="是否流式输出（SSE）")


class ChatCompletionResponse(BaseModel):
    """聊天完成响应（非流式）"""
    id: str = Field(..., description="响应唯一ID")
    model: str = Field(..., description="使用的模型名称")
    message: ChatMessage = Field(..., description="AI回复消息")
    usage: Optional[dict] = Field(None, description="Token使用统计：{prompt_tokens, completion_tokens, total_tokens}")
    finish_reason: Optional[str] = Field(None, description="完成原因：stop/length/content_filter等")


