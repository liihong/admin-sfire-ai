"""
对话会话管理服务
提供会话和消息的CRUD操作，以及语义搜索功能
"""
from typing import List, Optional, Tuple, Dict
from sqlalchemy import select, func, and_, desc, asc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
import numpy as np
from loguru import logger

from models.conversation import (
    Conversation,
    ConversationMessage,
    ConversationChunk,
    ConversationStatus,
    EmbeddingStatus,
)
from schemas.conversation import (
    ConversationCreate,
    ConversationUpdate,
    ConversationListParams,
    ConversationMessageCreate,
)
from utils.exceptions import NotFoundException, BadRequestException
from utils.pagination import paginate_query, PageResult
from services.vector_db import get_vector_db_service
from services.embedding import get_embedding_service


class ConversationService:
    """对话会话管理服务类"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.vector_db = get_vector_db_service()
        self.embedding_service = get_embedding_service()
    
    # ============== 会话CRUD ==============
    
    async def create_conversation(
        self,
        user_id: int,
        conversation_data: ConversationCreate
    ) -> Conversation:
        """
        创建新会话
        
        Args:
            user_id: 用户ID
            conversation_data: 会话创建数据
        
        Returns:
            Conversation: 创建的会话对象
        """
        title = conversation_data.title or "新对话"
        
        conversation = Conversation(
            user_id=user_id,
            agent_id=conversation_data.agent_id,
            project_id=conversation_data.project_id,
            title=title,
            model_type=conversation_data.model_type or "deepseek",
            status=ConversationStatus.ACTIVE.value,
        )
        
        self.db.add(conversation)
        await self.db.flush()
        await self.db.refresh(conversation)
        
        logger.info(f"创建新会话: {conversation.id}, 用户: {user_id}")
        return conversation
    
    async def get_conversation_by_id(
        self,
        conversation_id: int,
        user_id: Optional[int] = None
    ) -> Conversation:
        """
        根据ID获取会话
        
        Args:
            conversation_id: 会话ID
            user_id: 用户ID（可选，用于权限验证）
        
        Returns:
            Conversation: 会话对象
        """
        query = select(Conversation).where(Conversation.id == conversation_id)
        
        if user_id:
            query = query.where(Conversation.user_id == user_id)
        
        result = await self.db.execute(query)
        conversation = result.scalar_one_or_none()
        
        if not conversation:
            raise NotFoundException(f"会话 {conversation_id} 不存在")
        
        return conversation
    
    async def list_conversations(
        self,
        user_id: int,
        params: ConversationListParams
    ) -> PageResult[Conversation]:
        """
        获取会话列表（分页）
        
        Args:
            user_id: 用户ID
            params: 查询参数
        
        Returns:
            PageResult[Conversation]: 分页结果
        """
        query = select(Conversation).where(Conversation.user_id == user_id)
        conditions = [Conversation.user_id == user_id]
        
        # 状态筛选
        if params.status:
            conditions.append(Conversation.status == params.status)
        
        # 智能体筛选
        if params.agent_id:
            conditions.append(Conversation.agent_id == params.agent_id)
        
        # 项目筛选
        if params.project_id:
            conditions.append(Conversation.project_id == params.project_id)
        
        # 关键词搜索（标题）
        if params.keyword:
            conditions.append(Conversation.title.like(f"%{params.keyword}%"))
        
        query = query.where(and_(*conditions))
        query = query.order_by(desc(Conversation.updated_at))
        
        count_query = select(func.count(Conversation.id)).where(and_(*conditions))
        
        return await paginate_query(
            self.db,
            query,
            count_query,
            page_num=params.pageNum,
            page_size=params.pageSize,
        )
    
    async def update_conversation_title(
        self,
        conversation_id: int,
        title: str,
        user_id: Optional[int] = None
    ) -> Conversation:
        """
        更新会话标题
        
        Args:
            conversation_id: 会话ID
            title: 新标题
            user_id: 用户ID（可选，用于权限验证）
        
        Returns:
            Conversation: 更新后的会话对象
        """
        conversation = await self.get_conversation_by_id(conversation_id, user_id)
        conversation.title = title
        await self.db.flush()
        await self.db.refresh(conversation)
        
        logger.info(f"更新会话标题: {conversation_id}, 新标题: {title}")
        return conversation
    
    async def archive_conversation(
        self,
        conversation_id: int,
        user_id: Optional[int] = None
    ) -> Conversation:
        """
        归档会话
        
        Args:
            conversation_id: 会话ID
            user_id: 用户ID（可选）
        
        Returns:
            Conversation: 更新后的会话对象
        """
        conversation = await self.get_conversation_by_id(conversation_id, user_id)
        conversation.status = ConversationStatus.ARCHIVED.value
        await self.db.flush()
        await self.db.refresh(conversation)
        
        logger.info(f"归档会话: {conversation_id}")
        return conversation
    
    async def delete_conversation(
        self,
        conversation_id: int,
        user_id: Optional[int] = None
    ) -> None:
        """
        删除会话（软删除，实际标记为已删除状态）
        
        Args:
            conversation_id: 会话ID
            user_id: 用户ID（可选）
        """
        conversation = await self.get_conversation_by_id(conversation_id, user_id)
        
        # 删除向量数据库中的相关向量
        # 查询该会话的所有chunks
        chunks_query = select(ConversationChunk).where(
            ConversationChunk.conversation_id == conversation_id
        )
        chunks_result = await self.db.execute(chunks_query)
        chunks = chunks_result.scalars().all()
        
        for chunk in chunks:
            if chunk.vector_id:
                self.vector_db.delete_embedding(chunk.vector_id)
        
        # 删除数据库记录（级联删除消息和chunks）
        await self.db.delete(conversation)
        await self.db.flush()
        
        logger.info(f"删除会话: {conversation_id}")
    
    # ============== 消息管理 ==============
    
    async def get_conversation_messages(
        self,
        conversation_id: int,
        limit: Optional[int] = None
    ) -> List[ConversationMessage]:
        """
        获取会话消息列表
        
        Args:
            conversation_id: 会话ID
            limit: 限制返回数量（可选）
        
        Returns:
            List[ConversationMessage]: 消息列表
        """
        query = select(ConversationMessage).where(
            ConversationMessage.conversation_id == conversation_id
        ).order_by(asc(ConversationMessage.sequence))
        
        if limit:
            query = query.limit(limit)
        
        result = await self.db.execute(query)
        return list(result.scalars().all())
    
    async def add_message(
        self,
        conversation_id: int,
        message_data: ConversationMessageCreate
    ) -> ConversationMessage:
        """
        添加消息到会话
        
        Args:
            conversation_id: 会话ID
            message_data: 消息数据
        
        Returns:
            ConversationMessage: 创建的消息对象
        """
        # 如果未指定sequence，使用时间戳生成（避免查询数据库导致的并发冲突）
        if message_data.sequence is None:
            from utils.sequence import generate_sequence
            sequence = generate_sequence()
        else:
            sequence = message_data.sequence
        
        message = ConversationMessage(
            conversation_id=conversation_id,
            role=message_data.role,
            content=message_data.content,
            tokens=message_data.tokens or 0,
            sequence=sequence,
            embedding_status=EmbeddingStatus.PENDING.value,
        )
        
        self.db.add(message)
        await self.db.flush()
        await self.db.refresh(message)
        
        # 更新会话统计
        await self._update_conversation_stats(conversation_id)
        
        return message
    
    async def _update_conversation_stats(self, conversation_id: int):
        """更新会话统计信息"""
        conversation = await self.get_conversation_by_id(conversation_id)
        
        # 统计消息数量和token总数
        stats_query = select(
            func.count(ConversationMessage.id),
            func.sum(ConversationMessage.tokens)
        ).where(ConversationMessage.conversation_id == conversation_id)
        
        stats_result = await self.db.execute(stats_query)
        count, total_tokens = stats_result.one()
        
        conversation.message_count = count or 0
        conversation.total_tokens = int(total_tokens or 0)
        
        await self.db.flush()
    
    # ============== 语义搜索相关方法 ==============
    
    async def search_relevant_chunks(
        self,
        conversation_id: int,
        query_text: str,
        top_k: int = 5,
        threshold: float = 0.7
    ) -> List[Dict]:
        """
        从向量库搜索相关历史片段
        
        Args:
            conversation_id: 会话ID
            query_text: 查询文本（用户新消息）
            top_k: 返回最相关的k个片段
            threshold: 相似度阈值
        
        Returns:
            List[Dict]: 相关片段列表，每个元素包含 {chunk_id, similarity, chunk_text, messages}
        """
        try:
            # 对查询文本进行向量化
            query_embedding = await self.embedding_service.generate_embedding(query_text)
            if query_embedding is None:
                logger.warning("查询文本向量化失败")
                return []
            
            # 从向量库搜索相似片段
            # 注意：这里需要先查询该会话的所有chunks的vector_id
            chunks_query = select(ConversationChunk).where(
                ConversationChunk.conversation_id == conversation_id
            )
            chunks_result = await self.db.execute(chunks_query)
            chunks = chunks_result.scalars().all()
            
            if not chunks:
                return []
            
            # 搜索相似向量
            results = self.vector_db.search_similar(
                query_embedding,
                top_k=top_k,
                threshold=threshold
            )
            
            # ✅ 优化：批量查询所有消息ID（修复N+1查询问题）
            message_ids = set()
            for chunk in chunks:
                message_ids.add(chunk.user_message_id)
                message_ids.add(chunk.assistant_message_id)

            # 一次性查询所有消息
            if message_ids:
                messages_query = select(ConversationMessage).where(
                    ConversationMessage.id.in_(message_ids)
                )
                messages_result = await self.db.execute(messages_query)
                messages_dict = {msg.id: msg for msg in messages_result.scalars().all()}
            else:
                messages_dict = {}

            # 将结果转换为消息格式
            relevant_chunks = []
            for vector_id, similarity, metadata in results:
                # 查找对应的chunk
                chunk = next((c for c in chunks if c.vector_id == vector_id), None)
                if not chunk:
                    continue

                # ✅ 从字典中快速查找消息（O(1)复杂度）
                user_msg = messages_dict.get(chunk.user_message_id)
                assistant_msg = messages_dict.get(chunk.assistant_message_id)

                if user_msg and assistant_msg:
                    relevant_chunks.append({
                        "chunk_id": chunk.id,
                        "similarity": similarity,
                        "chunk_text": chunk.chunk_text,
                        "messages": [
                            {"role": "user", "content": user_msg.content},
                            {"role": "assistant", "content": assistant_msg.content},
                        ]
                    })

            return relevant_chunks
            
        except Exception as e:
            logger.error(f"搜索相关片段失败: {e}")
            return []
    
    async def build_context_from_search(
        self,
        conversation_id: int,
        query_text: str,
        relevant_chunks: List[Dict],
        include_recent: int = 2
    ) -> List[Dict]:
        """
        基于搜索结果构建消息上下文
        
        Args:
            conversation_id: 会话ID
            query_text: 当前查询文本
            relevant_chunks: 相关片段列表
            include_recent: 包含最近N条消息（保证连续性）
        
        Returns:
            List[Dict]: 消息列表，格式为 [{"role": "user", "content": "..."}, ...]
        """
        messages = []
        
        # 1. 添加相关片段的消息
        for chunk in relevant_chunks:
            messages.extend(chunk["messages"])
        
        # 2. 添加最近的消息（保证连续性）
        recent_messages = await self.get_conversation_messages(
            conversation_id,
            limit=include_recent * 2  # 包含最近N轮对话（每轮2条消息）
        )
        
        # 避免重复添加
        recent_message_ids = {msg.id for msg in recent_messages}
        for chunk in relevant_chunks:
            # 从recent_messages中移除已在relevant_chunks中的消息
            recent_messages = [
                msg for msg in recent_messages
                if msg.id not in [chunk.get("user_msg_id"), chunk.get("assistant_msg_id")]
            ]
        
        # 添加最近消息
        for msg in recent_messages:
            messages.append({
                "role": msg.role,
                "content": msg.content
            })
        
        # 3. 添加当前用户消息
        messages.append({
            "role": "user",
            "content": query_text
        })
        
        return messages
    
    # ============== 异步任务方法 ==============
    
    async def save_conversation_async(
        self,
        conversation_id: int,
        user_message: str,
        assistant_message: str,
        user_tokens: int = 0,
        assistant_tokens: int = 0
    ):
        """
        异步保存对话消息（后台任务）
        注意：此方法在后台任务中调用，需要创建新的数据库会话
        
        Args:
            conversation_id: 会话ID
            user_message: 用户消息内容
            assistant_message: AI回复内容
            user_tokens: 用户消息token数
            assistant_tokens: AI回复token数
        """
        # 在后台任务中创建新的数据库会话
        from db.session import async_session_maker
        
        # 使用重试机制处理锁等待超时
        import asyncio
        from sqlalchemy.exc import OperationalError, DBAPIError
        from pymysql.err import OperationalError as PyMySQLOperationalError

        max_retries = 5  # 增加重试次数
        base_delay = 0.3  # 300ms基础延迟

        last_error = None
        for attempt in range(max_retries):
            try:
                async with async_session_maker() as db:
                    # ✅ 优化：使用时间戳生成sequence，避免查询数据库导致的并发冲突
                    from utils.sequence import generate_sequence_pair
                    user_sequence, assistant_sequence = generate_sequence_pair()

                    # 保存用户消息
                    user_msg = ConversationMessage(
                        conversation_id=conversation_id,
                        role="user",
                        content=user_message,
                        tokens=user_tokens,
                        sequence=user_sequence,
                        embedding_status=EmbeddingStatus.PENDING.value,
                    )

                    # 保存AI回复
                    assistant_msg = ConversationMessage(
                        conversation_id=conversation_id,
                        role="assistant",
                        content=assistant_message,
                        tokens=assistant_tokens,
                        sequence=assistant_sequence,
                        embedding_status=EmbeddingStatus.PENDING.value,
                    )

                    db.add(user_msg)
                    db.add(assistant_msg)
                    await db.flush()
                    await db.refresh(user_msg)
                    await db.refresh(assistant_msg)

                    # ✅ 优化：使用增量更新而不是重新统计（提升性能）
                    # 使用 skip_locked 避免锁等待，如果锁被占用则跳过（配合重试机制）
                    conversation_query = select(Conversation).where(
                        Conversation.id == conversation_id
                    ).with_for_update(skip_locked=True)
                    conversation_result = await db.execute(conversation_query)
                    conversation = conversation_result.scalar_one_or_none()

                    # 如果因为锁冲突没获取到记录，触发重试
                    if conversation is None:
                        from sqlalchemy.exc import OperationalError
                        raise OperationalError("锁冲突，记录被其他事务占用", orig=type('obj', (object,), {'args': [1205]}))

                    # 增量更新统计信息
                    conversation.message_count += 2  # user + assistant
                    conversation.total_tokens += user_tokens + assistant_tokens

                    await db.flush()
                    await db.commit()

                    logger.info(
                        f"已保存对话消息: 会话{conversation_id}, "
                        f"消息{user_msg.id}-{assistant_msg.id}, "
                        f"尝试次数: {attempt + 1}"
                    )

                    # 成功，跳出重试循环
                    return

            except (OperationalError, DBAPIError) as e:
                # 检查是否是锁等待超时或死锁错误
                error_code = None
                if hasattr(e, 'orig') and hasattr(e.orig, 'args'):
                    error_code = e.orig.args[0] if e.orig.args else None

                # 1205: Lock wait timeout exceeded
                # 1213: Deadlock found when trying to get lock
                is_lock_error = error_code in (1205, 1213)

                if is_lock_error and attempt < max_retries - 1:
                    last_error = e
                    # 指数退避: 0.3s, 0.6s, 1.2s, 1.8s, 2.4s
                    delay = base_delay * (attempt + 1)
                    logger.warning(
                        f"保存对话时遇到锁冲突(尝试 {attempt + 1}/{max_retries}): "
                        f"错误码={error_code}, {delay}秒后重试..."
                    )
                    await asyncio.sleep(delay)
                    continue
                else:
                    # 最后一次重试失败或非锁错误，抛出异常
                    logger.error(
                        f"保存对话失败(尝试 {attempt + 1}/{max_retries}): "
                        f"错误码={error_code}, {str(e)}"
                    )
                    raise

            except Exception as e:
                # 其他异常，直接抛出
                logger.error(f"保存对话时发生未预期错误: {str(e)}")
                raise
    
    async def embed_conversation_async(
        self,
        conversation_id: int,
        user_message_id: int,
        assistant_message_id: int
    ):
        """
        异步向量化对话片段（后台任务）
        
        Args:
            conversation_id: 会话ID
            user_message_id: 用户消息ID
            assistant_message_id: AI回复消息ID
        """
        try:
            # 获取消息内容
            user_msg_query = select(ConversationMessage).where(
                ConversationMessage.id == user_message_id
            )
            assistant_msg_query = select(ConversationMessage).where(
                ConversationMessage.id == assistant_message_id
            )
            
            user_msg_result = await self.db.execute(user_msg_query)
            assistant_msg_result = await self.db.execute(assistant_msg_query)
            
            user_msg = user_msg_result.scalar_one_or_none()
            assistant_msg = assistant_msg_result.scalar_one_or_none()
            
            if not user_msg or not assistant_msg:
                logger.error(f"消息不存在: user_msg={user_message_id}, assistant_msg={assistant_message_id}")
                return
            
            # 组合对话片段文本
            chunk_text = f"用户: {user_msg.content}\n\n助手: {assistant_msg.content}"
            
            # 更新状态为处理中
            user_msg.embedding_status = EmbeddingStatus.PROCESSING.value
            assistant_msg.embedding_status = EmbeddingStatus.PROCESSING.value
            await self.db.flush()
            
            # 生成向量
            embedding = await self.embedding_service.generate_embedding(chunk_text)
            
            if embedding is None:
                # 向量化失败
                user_msg.embedding_status = EmbeddingStatus.FAILED.value
                assistant_msg.embedding_status = EmbeddingStatus.FAILED.value
                await self.db.flush()
                logger.error(f"向量化失败: 会话{conversation_id}")
                return
            
            # 生成向量ID
            vector_id = f"conv_{conversation_id}_chunk_{user_message_id}_{assistant_message_id}"
            
            # 保存到向量数据库
            success = self.vector_db.add_embedding(
                vector_id=vector_id,
                embedding=embedding,
                metadata={
                    "conversation_id": conversation_id,
                    "user_message_id": user_message_id,
                    "assistant_message_id": assistant_message_id,
                    "chunk_text": chunk_text,
                }
            )
            
            if success:
                # 创建或更新ConversationChunk记录
                chunk_query = select(ConversationChunk).where(
                    and_(
                        ConversationChunk.conversation_id == conversation_id,
                        ConversationChunk.user_message_id == user_message_id,
                        ConversationChunk.assistant_message_id == assistant_message_id,
                    )
                )
                chunk_result = await self.db.execute(chunk_query)
                chunk = chunk_result.scalar_one_or_none()
                
                if not chunk:
                    chunk = ConversationChunk(
                        conversation_id=conversation_id,
                        user_message_id=user_message_id,
                        assistant_message_id=assistant_message_id,
                        chunk_text=chunk_text,
                        vector_id=vector_id,
                    )
                    self.db.add(chunk)
                else:
                    chunk.vector_id = vector_id
                    chunk.chunk_text = chunk_text
                
                # 更新消息状态
                user_msg.embedding_status = EmbeddingStatus.COMPLETED.value
                assistant_msg.embedding_status = EmbeddingStatus.COMPLETED.value
                
                await self.db.flush()
                logger.info(f"向量化完成: 会话{conversation_id}, vector_id={vector_id}")
            else:
                # 向量数据库保存失败
                user_msg.embedding_status = EmbeddingStatus.FAILED.value
                assistant_msg.embedding_status = EmbeddingStatus.FAILED.value
                await self.db.flush()
                logger.error(f"向量数据库保存失败: 会话{conversation_id}")
                
        except Exception as e:
            logger.error(f"异步向量化失败: {e}")
            # 更新状态为失败
            try:
                user_msg_query = select(ConversationMessage).where(
                    ConversationMessage.id == user_message_id
                )
                assistant_msg_query = select(ConversationMessage).where(
                    ConversationMessage.id == assistant_message_id
                )
                
                user_msg_result = await self.db.execute(user_msg_query)
                assistant_msg_result = await self.db.execute(assistant_msg_query)
                
                user_msg = user_msg_result.scalar_one_or_none()
                assistant_msg = assistant_msg_result.scalar_one_or_none()
                
                if user_msg:
                    user_msg.embedding_status = EmbeddingStatus.FAILED.value
                if assistant_msg:
                    assistant_msg.embedding_status = EmbeddingStatus.FAILED.value
                
                await self.db.flush()
            except Exception as e2:
                logger.error(f"更新失败状态时出错: {e2}")

