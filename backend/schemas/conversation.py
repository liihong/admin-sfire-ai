"""
对话会话和消息的 Pydantic Schemas
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field

from .common import PageParams


# ============== 基础 Schema ==============

class ConversationMessageCreate(BaseModel):
    """创建消息请求"""
    role: str = Field(..., description="角色: user/assistant/system")
    content: str = Field(..., description="消息内容")
    tokens: Optional[int] = Field(default=0, description="token数")
    sequence: Optional[int] = Field(None, description="消息序号")


class ConversationMessageResponse(BaseModel):
    """消息响应"""
    id: int = Field(..., description="消息ID")
    conversation_id: int = Field(..., description="会话ID")
    role: str = Field(..., description="角色")
    content: str = Field(..., description="消息内容")
    tokens: int = Field(default=0, description="token数")
    sequence: int = Field(..., description="消息序号")
    embedding_status: str = Field(..., description="向量化状态")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: Optional[datetime] = Field(None, description="更新时间")

    class Config:
        from_attributes = True


# ============== 会话 Schema ==============

class ConversationCreate(BaseModel):
    """创建会话请求"""
    agent_id: Optional[int] = Field(None, description="智能体ID")
    project_id: Optional[int] = Field(None, description="项目ID")
    title: Optional[str] = Field(None, description="会话标题（可选，会自动生成）")
    model_type: Optional[str] = Field(default="deepseek", description="模型类型")


class ConversationUpdate(BaseModel):
    """更新会话请求"""
    title: Optional[str] = Field(None, description="会话标题")
    status: Optional[str] = Field(None, description="状态: active/archived")


class ConversationResponse(BaseModel):
    """会话响应"""
    id: int = Field(..., description="会话ID")
    user_id: int = Field(..., description="用户ID")
    agent_id: Optional[int] = Field(None, description="智能体ID")
    project_id: Optional[int] = Field(None, description="项目ID")
    title: str = Field(..., description="会话标题")
    model_type: str = Field(..., description="模型类型")
    total_tokens: int = Field(default=0, description="总token数")
    message_count: int = Field(default=0, description="消息数量")
    status: str = Field(..., description="状态")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: Optional[datetime] = Field(None, description="更新时间")
    
    class Config:
        from_attributes = True


class ConversationDetailResponse(ConversationResponse):
    """会话详情响应（包含消息列表）"""
    messages: List[ConversationMessageResponse] = Field(default_factory=list, description="消息列表")
    
    # 可选关联信息
    agent_name: Optional[str] = Field(None, description="智能体名称")
    project_name: Optional[str] = Field(None, description="项目名称")


class ConversationListParams(PageParams):
    """会话列表查询参数"""
    status: Optional[str] = Field(None, description="状态筛选: active/archived")
    agent_id: Optional[int] = Field(None, description="智能体ID筛选")
    project_id: Optional[int] = Field(None, description="项目ID筛选")
    keyword: Optional[str] = Field(None, description="关键词搜索（标题）")


# ============== 对话片段 Schema ==============

class ConversationChunkResponse(BaseModel):
    """对话片段响应"""
    id: int = Field(..., description="片段ID")
    conversation_id: int = Field(..., description="会话ID")
    user_message_id: int = Field(..., description="用户消息ID")
    assistant_message_id: int = Field(..., description="AI回复消息ID")
    chunk_text: str = Field(..., description="片段文本")
    vector_id: Optional[str] = Field(None, description="向量ID")
    created_at: datetime = Field(..., description="创建时间")
    
    class Config:
        from_attributes = True










