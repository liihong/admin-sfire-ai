"""
Conversation业务服务（业务逻辑层）
负责权限验证、会话管理等业务逻辑
调用数据访问层完成CRUD操作
"""
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from models.conversation import Conversation
from schemas.conversation import (
    ConversationCreate,
    ConversationListParams,
    ConversationMessageCreate,
)
from utils.exceptions import NotFoundException, ForbiddenException, BadRequestException
from utils.pagination import PageResult
from utils.redis_lock import RedisLock
from .dao import ConversationDAO


class ConversationBusinessService:
    """
    Conversation业务服务类
    
    职责说明：
    - 权限验证：验证用户是否有权限访问会话
    - 会话管理：创建和管理对话会话
    - 业务编排：调用数据访问层完成CRUD操作
    
    依赖关系：
    - 依赖ConversationDAO（数据访问）
    
    使用示例：
        service = ConversationBusinessService(db)
        conversation = await service.create_conversation(user_id, conversation_data)
    """
    
    def __init__(self, db: AsyncSession):
        """
        初始化Conversation业务服务
        
        Args:
            db: 异步数据库会话
        """
        self.db = db
        self.dao = ConversationDAO(db)
    
    async def create_conversation(
        self,
        user_id: int,
        conversation_data: ConversationCreate
    ) -> Conversation:
        """
        创建新会话（业务逻辑层，包含并发控制和去重）
        
        业务逻辑：
        1. 检查用户并发限制（最多3个并发会话）
        2. 检查会话去重（相同agent+project，5分钟内）
        3. 调用数据访问层创建会话
        4. 设置去重标记和并发计数
        
        Args:
            user_id: 用户ID
            conversation_data: 会话创建数据
        
        Returns:
            Conversation: 创建的会话对象
        
        Raises:
            BadRequestException: 并发限制或去重检查失败
        """
        # 1. 检查用户并发限制
        can_create = await RedisLock.check_user_conversation_limit(user_id, max_count=3)
        if not can_create:
            raise BadRequestException("您同时进行的会话数量已达上限（3个），请先完成或删除现有会话")
        
        # 2. 检查会话去重（相同agent+project，5分钟内）
        duplicate_conversation_id = await RedisLock.check_conversation_duplicate(
            user_id=user_id,
            agent_id=conversation_data.agent_id,
            project_id=conversation_data.project_id
        )
        if duplicate_conversation_id:
            logger.info(
                f"发现重复会话: user_id={user_id}, "
                f"agent_id={conversation_data.agent_id}, "
                f"project_id={conversation_data.project_id}, "
                f"conversation_id={duplicate_conversation_id}"
            )
            # 返回已存在的会话
            return await self.dao.get_conversation_by_id(duplicate_conversation_id, user_id)
        
        # 3. 调用数据访问层创建会话
        conversation = await self.dao.create_conversation(user_id, conversation_data)
        
        # 4. 设置去重标记和并发计数
        await RedisLock.set_conversation_duplicate(
            user_id=user_id,
            agent_id=conversation_data.agent_id,
            project_id=conversation_data.project_id,
            conversation_id=conversation.id
        )
        await RedisLock.increment_user_conversation_count(user_id)
        
        logger.info(f"创建新会话: {conversation.id}, 用户: {user_id}")
        return conversation
    
    async def get_conversation(
        self,
        conversation_id: int,
        user_id: int
    ) -> Conversation:
        """
        获取会话（业务逻辑层，包含权限验证）
        
        业务逻辑：
        1. 验证用户是否有权限访问该会话
        
        Args:
            conversation_id: 会话ID
            user_id: 用户ID（必须，用于权限验证）
        
        Returns:
            Conversation: 会话对象
        
        Raises:
            NotFoundException: 会话不存在
            ForbiddenException: 用户无权限访问该会话
        """
        # 调用数据访问层获取会话（带用户ID筛选）
        conversation = await self.dao.get_conversation_by_id(conversation_id, user_id)
        
        # 额外权限验证（防御性编程）
        if conversation.user_id != user_id:
            raise ForbiddenException("无权访问该会话")
        
        return conversation
    
    async def list_conversations(
        self,
        user_id: int,
        params: ConversationListParams
    ) -> PageResult[Conversation]:
        """
        获取会话列表（分页，业务逻辑层）
        
        Args:
            user_id: 用户ID
            params: 查询参数
        
        Returns:
            PageResult[Conversation]: 分页结果
        """
        return await self.dao.list_conversations(user_id, params)
    
    async def update_conversation_title(
        self,
        conversation_id: int,
        title: str,
        user_id: int
    ) -> Conversation:
        """
        更新会话标题（业务逻辑层，包含权限验证）
        
        Args:
            conversation_id: 会话ID
            title: 新标题
            user_id: 用户ID（必须，用于权限验证）
        
        Returns:
            Conversation: 更新后的会话对象
        
        Raises:
            NotFoundException: 会话不存在
            ForbiddenException: 用户无权限访问该会话
        """
        # 验证权限
        await self.get_conversation(conversation_id, user_id)
        
        # 调用数据访问层更新标题
        return await self.dao.update_conversation_title(conversation_id, title)
    
    async def archive_conversation(
        self,
        conversation_id: int,
        user_id: int
    ) -> Conversation:
        """
        归档会话（业务逻辑层，包含权限验证）
        
        Args:
            conversation_id: 会话ID
            user_id: 用户ID（必须，用于权限验证）
        
        Returns:
            Conversation: 更新后的会话对象
        """
        # 验证权限
        await self.get_conversation(conversation_id, user_id)
        
        # 调用数据访问层归档
        return await self.dao.archive_conversation(conversation_id)
    
    async def delete_conversation(
        self,
        conversation_id: int,
        user_id: int
    ) -> None:
        """
        删除会话（业务逻辑层，包含权限验证）
        
        Args:
            conversation_id: 会话ID
            user_id: 用户ID（必须，用于权限验证）
        """
        # 验证权限并获取会话信息（用于减少并发计数）
        conversation = await self.get_conversation(conversation_id, user_id)
        
        # 调用数据访问层删除
        await self.dao.delete_conversation(conversation_id)
        
        # 减少用户并发计数
        await RedisLock.decrement_user_conversation_count(user_id)
    
    async def get_conversation_messages(
        self,
        conversation_id: int,
        user_id: int,
        limit: Optional[int] = None
    ) -> List:
        """
        获取会话消息列表（业务逻辑层，包含权限验证）
        
        Args:
            conversation_id: 会话ID
            user_id: 用户ID（必须，用于权限验证）
            limit: 限制返回数量（可选）
        
        Returns:
            List: 消息列表
        """
        # 验证权限
        await self.get_conversation(conversation_id, user_id)
        
        # 调用数据访问层获取消息
        return await self.dao.get_conversation_messages(conversation_id, limit)
    
    async def add_message(
        self,
        conversation_id: int,
        message_data: ConversationMessageCreate,
        user_id: int
    ):
        """
        添加消息到会话（业务逻辑层，包含权限验证）
        
        Args:
            conversation_id: 会话ID
            message_data: 消息数据
            user_id: 用户ID（必须，用于权限验证）
        
        Returns:
            ConversationMessage: 创建的消息对象
        """
        # 验证权限
        await self.get_conversation(conversation_id, user_id)
        
        # 调用数据访问层添加消息
        message = await self.dao.add_message(conversation_id, message_data)
        
        # 异步更新统计（独立事务，失败不影响消息保存）
        import asyncio
        asyncio.create_task(
            self.dao.update_conversation_stats_async(conversation_id)
        )
        
        return message
    
    async def search_relevant_chunks(
        self,
        conversation_id: int,
        query_text: str,
        user_id: int,
        top_k: int = 5,
        threshold: float = 0.7
    ) -> List:
        """
        搜索相关历史片段（业务逻辑层，包含权限验证）
        
        Args:
            conversation_id: 会话ID
            query_text: 查询文本
            user_id: 用户ID（必须，用于权限验证）
            top_k: 返回最相关的k个片段
            threshold: 相似度阈值
        
        Returns:
            List: 相关片段列表
        """
        # 验证权限
        await self.get_conversation(conversation_id, user_id)
        
        # 调用数据访问层搜索
        return await self.dao.search_relevant_chunks(
            conversation_id, query_text, top_k, threshold
        )
    
    async def build_context_from_search(
        self,
        conversation_id: int,
        query_text: str,
        relevant_chunks: List,
        user_id: int,
        include_recent: int = 2
    ) -> List:
        """
        基于搜索结果构建消息上下文（业务逻辑层，包含权限验证）
        
        Args:
            conversation_id: 会话ID
            query_text: 当前查询文本
            relevant_chunks: 相关片段列表
            user_id: 用户ID（必须，用于权限验证）
            include_recent: 包含最近N条消息
        
        Returns:
            List: 消息列表
        """
        # 验证权限
        await self.get_conversation(conversation_id, user_id)
        
        # 调用数据访问层构建上下文
        return await self.dao.build_context_from_search(
            conversation_id, query_text, relevant_chunks, include_recent
        )

