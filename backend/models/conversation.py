"""
对话会话和消息模型
用于存储用户与AI智能体的对话历史
"""
import enum
from typing import Optional, List, TYPE_CHECKING
from sqlalchemy import (
    String,
    BigInteger,
    Integer,
    Text,
    ForeignKey,
    Index,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import BaseModel

if TYPE_CHECKING:
    from models.user import User
    from models.agent import Agent
    from models.project import Project


class ConversationStatus(enum.Enum):
    """会话状态枚举"""
    ACTIVE = "active"       # 活跃
    ARCHIVED = "archived"   # 归档


class EmbeddingStatus(enum.Enum):
    """向量化状态枚举"""
    PENDING = "pending"         # 待处理
    PROCESSING = "processing"   # 处理中
    COMPLETED = "completed"     # 已完成
    FAILED = "failed"           # 失败


class Conversation(BaseModel):
    """
    对话会话模型
    
    核心字段:
        - user_id: 用户ID
        - agent_id: 智能体ID（可选）
        - project_id: 项目ID（可选）
        - title: 会话标题（自动生成）
        - model_type: 使用的模型类型
        - total_tokens: 总token数
        - message_count: 消息数量
        - status: 状态（active/archived）
    """
    __tablename__ = "conversations"
    __table_args__ = (
        Index("ix_conversations_user_id", "user_id"),
        Index("ix_conversations_agent_id", "agent_id"),
        Index("ix_conversations_project_id", "project_id"),
        Index("ix_conversations_status", "status"),
        Index("ix_conversations_created_at", "created_at"),
        {"comment": "对话会话表"},
    )
    
    # === 关联字段 ===
    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        comment="用户ID",
    )
    
    agent_id: Mapped[Optional[int]] = mapped_column(
        BigInteger,
        ForeignKey("agents.id", ondelete="SET NULL"),
        nullable=True,
        comment="智能体ID（可选）",
    )
    
    project_id: Mapped[Optional[int]] = mapped_column(
        BigInteger,
        ForeignKey("projects.id", ondelete="SET NULL"),
        nullable=True,
        comment="项目ID（可选）",
    )
    
    # === 基本信息 ===
    title: Mapped[str] = mapped_column(
        String(256),
        nullable=False,
        default="新对话",
        comment="会话标题（自动生成，首条用户消息摘要）",
    )
    
    model_type: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        default="deepseek",
        comment="使用的模型类型",
    )
    
    # === 统计字段 ===
    total_tokens: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="总token数（用于统计）",
    )
    
    message_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="消息数量",
    )
    
    # === 状态字段 ===
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=ConversationStatus.ACTIVE.value,
        comment="状态：active-活跃, archived-归档",
    )
    
    # === 关系定义 ===
    user: Mapped["User"] = relationship(
        "User",
        back_populates="conversations",
        lazy="selectin",
    )
    
    agent: Mapped[Optional["Agent"]] = relationship(
        "Agent",
        lazy="selectin",
    )
    
    project: Mapped[Optional["Project"]] = relationship(
        "Project",
        lazy="selectin",
    )
    
    messages: Mapped[List["ConversationMessage"]] = relationship(
        "ConversationMessage",
        back_populates="conversation",
        cascade="all, delete-orphan",
        lazy="dynamic",
        order_by="ConversationMessage.sequence",
    )
    
    def __repr__(self) -> str:
        return f"<Conversation(id={self.id}, title='{self.title}', user_id={self.user_id})>"


class ConversationMessage(BaseModel):
    """
    对话消息模型
    
    核心字段:
        - conversation_id: 会话ID
        - role: 角色（user/assistant/system）
        - content: 消息内容
        - tokens: token数
        - sequence: 消息序号
        - embedding_status: 向量化状态
    """
    __tablename__ = "conversation_messages"
    __table_args__ = (
        Index("ix_conversation_messages_conversation_id", "conversation_id"),
        Index("ix_conversation_messages_sequence", "conversation_id", "sequence"),
        Index("ix_conversation_messages_embedding_status", "embedding_status"),
        {"comment": "对话消息表"},
    )
    
    # === 关联字段 ===
    conversation_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False,
        comment="会话ID",
    )
    
    # === 消息内容 ===
    role: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        comment="角色：user-用户, assistant-AI助手, system-系统",
    )
    
    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="消息内容",
    )
    
    # === 统计字段 ===
    tokens: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="该消息的token数（用于统计）",
    )
    
    sequence: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="消息序号（用于排序）",
    )
    
    # === 向量化状态 ===
    embedding_status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=EmbeddingStatus.PENDING.value,
        comment="向量化状态：pending-待处理, processing-处理中, completed-已完成, failed-失败",
    )
    
    # === 关系定义 ===
    conversation: Mapped["Conversation"] = relationship(
        "Conversation",
        back_populates="messages",
        lazy="selectin",
    )
    
    def __repr__(self) -> str:
        return f"<ConversationMessage(id={self.id}, role='{self.role}', sequence={self.sequence})>"


class ConversationChunk(BaseModel):
    """
    对话片段模型（可选，用于存储完整的User+AI轮次）
    
    核心字段:
        - conversation_id: 会话ID
        - user_message_id: 用户消息ID
        - assistant_message_id: AI回复消息ID
        - chunk_text: 片段文本
        - vector_id: 向量数据库中的ID
    """
    __tablename__ = "conversation_chunks"
    __table_args__ = (
        Index("ix_conversation_chunks_conversation_id", "conversation_id"),
        Index("ix_conversation_chunks_vector_id", "vector_id"),
        {"comment": "对话片段表"},
    )
    
    # === 关联字段 ===
    conversation_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False,
        comment="会话ID",
    )
    
    user_message_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("conversation_messages.id", ondelete="CASCADE"),
        nullable=False,
        comment="用户消息ID",
    )
    
    assistant_message_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("conversation_messages.id", ondelete="CASCADE"),
        nullable=False,
        comment="AI回复消息ID",
    )
    
    # === 片段内容 ===
    chunk_text: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="片段文本（User消息 + AI回复的组合）",
    )
    
    vector_id: Mapped[Optional[str]] = mapped_column(
        String(128),
        nullable=True,
        comment="向量数据库中的ID（用于关联）",
    )
    
    def __repr__(self) -> str:
        return f"<ConversationChunk(id={self.id}, conversation_id={self.conversation_id}, vector_id={self.vector_id})>"















