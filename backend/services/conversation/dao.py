"""
Conversation数据访问层（DAO）
负责会话和消息的CRUD操作、语义搜索、向量化等数据访问功能
不包含业务逻辑（权限验证、余额检查等）
"""
from typing import List, Optional, Dict
from sqlalchemy import select, func, and_, desc, asc, update
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from models.conversation import (
    Conversation,
    ConversationMessage,
    ConversationChunk,
    ConversationStatus,
    EmbeddingStatus,
    MessageStatus,
)
from schemas.conversation import (
    ConversationCreate,
    ConversationListParams,
    ConversationMessageCreate,
)
from utils.exceptions import NotFoundException
from utils.pagination import paginate_query, PageResult
from services.shared.vector_db import get_vector_db_service
from services.shared.embedding import get_embedding_service


class ConversationDAO:
    """
    Conversation数据访问层
    
    职责说明：
    - CRUD操作：会话和消息的增删改查
    - 语义搜索：从向量库搜索相关历史片段
    - 向量化：对话片段的向量化和存储
    - 统计更新：更新会话统计信息
    
    不涉及：
    - 用户权限验证
    - 余额检查
    - 业务逻辑编排
    
    使用示例：
        dao = ConversationDAO(db)
        conversation = await dao.create_conversation(user_id, conversation_data)
    """
    
    def __init__(self, db: AsyncSession):
        """
        初始化Conversation数据访问层
        
        Args:
            db: 异步数据库会话
        """
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
        创建新会话（数据访问层，无业务逻辑）
        
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
        根据ID获取会话（数据访问层，无业务逻辑）
        
        Args:
            conversation_id: 会话ID
            user_id: 用户ID（可选，用于筛选）
        
        Returns:
            Conversation: 会话对象
        
        Raises:
            NotFoundException: 会话不存在
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
        获取会话列表（分页，数据访问层）
        
        过滤规则：只显示至少有一条消息的会话（不限制消息状态）
        这样可以显示所有有对话记录的会话，包括处理中、失败等状态的会话
        
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
        
        # 过滤：只显示至少有一条消息的会话（不限制消息状态和角色）
        # 这样可以显示所有有对话记录的会话，包括：
        # - pending（待处理）状态的会话
        # - processing（处理中）状态的会话
        # - success（成功）状态的会话
        # - error（失败）状态的会话
        # 使用EXISTS子查询优化性能
        exists_subquery = select(1).where(
            ConversationMessage.conversation_id == Conversation.id
        ).exists()
        conditions.append(exists_subquery)
        
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
        title: str
    ) -> Conversation:
        """
        更新会话标题（数据访问层）
        
        Args:
            conversation_id: 会话ID
            title: 新标题
        
        Returns:
            Conversation: 更新后的会话对象
        """
        conversation = await self.get_conversation_by_id(conversation_id)
        conversation.title = title
        await self.db.flush()
        await self.db.refresh(conversation)
        
        logger.info(f"更新会话标题: {conversation_id}, 新标题: {title}")
        return conversation
    
    async def archive_conversation(
        self,
        conversation_id: int
    ) -> Conversation:
        """
        归档会话（数据访问层）
        
        Args:
            conversation_id: 会话ID
        
        Returns:
            Conversation: 更新后的会话对象
        """
        conversation = await self.get_conversation_by_id(conversation_id)
        conversation.status = ConversationStatus.ARCHIVED.value
        await self.db.flush()
        await self.db.refresh(conversation)
        
        logger.info(f"归档会话: {conversation_id}")
        return conversation
    
    async def delete_conversation(
        self,
        conversation_id: int
    ) -> None:
        """
        删除会话（数据访问层）
        
        注意：会删除向量数据库中的相关向量
        
        Args:
            conversation_id: 会话ID
        """
        conversation = await self.get_conversation_by_id(conversation_id)
        
        # 删除向量数据库中的相关向量
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
        获取会话消息列表（数据访问层）
        
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
        添加消息到会话（数据访问层）
        
        优化策略：
        - 只插入消息，不更新统计（避免锁冲突）
        - 统计信息通过独立异步任务更新
        
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
            status=message_data.status or MessageStatus.PENDING.value,
            error_message=message_data.error_message,
        )
        
        self.db.add(message)
        await self.db.flush()
        await self.db.refresh(message)
        
        return message
    
    async def update_message_status(
        self,
        message_id: int,
        status: str,
        error_message: Optional[str] = None
    ) -> None:
        """
        更新消息状态（数据访问层）
        
        Args:
            message_id: 消息ID
            status: 新状态
            error_message: 错误信息（可选）
        """
        await self.db.execute(
            update(ConversationMessage)
            .where(ConversationMessage.id == message_id)
            .values(
                status=status,
                error_message=error_message
            )
        )
        await self.db.flush()
    
    async def update_conversation_stats(
        self,
        conversation_id: int
    ) -> None:
        """
        更新会话统计信息（数据访问层）
        
        Args:
            conversation_id: 会话ID
        """
        # 统计消息数量和token总数
        # 注意：所有消息都计入message_count，但只有success消息的Token计入total_tokens
        all_messages_query = select(
            func.count(ConversationMessage.id)
        ).where(ConversationMessage.conversation_id == conversation_id)
        
        success_tokens_query = select(
            func.sum(ConversationMessage.tokens)
        ).where(
            and_(
                ConversationMessage.conversation_id == conversation_id,
                ConversationMessage.status == MessageStatus.SUCCESS.value
            )
        )
        
        count_result = await self.db.execute(all_messages_query)
        tokens_result = await self.db.execute(success_tokens_query)
        
        count = count_result.scalar_one() or 0
        total_tokens = int(tokens_result.scalar_one() or 0)
        
        # 使用原子UPDATE，避免锁冲突
        await self.db.execute(
            update(Conversation)
            .where(Conversation.id == conversation_id)
            .values(
                message_count=count,
                total_tokens=total_tokens
            )
        )
        
        await self.db.flush()
    
    async def update_conversation_stats_async(self, conversation_id: int):
        """
        异步更新会话统计（独立事务，失败不影响消息保存）
        
        核心优化：
        - 使用独立数据库会话，避免与消息插入产生锁冲突
        - 失败时只记录警告，不影响主流程
        - 使用原子UPDATE，避免锁等待
        
        Args:
            conversation_id: 会话ID
        """
        from db.session import async_session_maker
        
        try:
            # 使用独立的数据库会话
            async with async_session_maker() as db:
                # 查询统计信息（不需要锁）
                # 注意：所有消息都计入message_count，但只有success消息的Token计入total_tokens
                all_messages_query = select(
                    func.count(ConversationMessage.id)
                ).where(ConversationMessage.conversation_id == conversation_id)
                
                success_tokens_query = select(
                    func.sum(ConversationMessage.tokens)
                ).where(
                    and_(
                        ConversationMessage.conversation_id == conversation_id,
                        ConversationMessage.status == MessageStatus.SUCCESS.value
                    )
                )
                
                count_result = await db.execute(all_messages_query)
                tokens_result = await db.execute(success_tokens_query)
                
                count = count_result.scalar_one() or 0
                total_tokens = int(tokens_result.scalar_one() or 0)
                
                # 直接使用原子UPDATE，无需先SELECT FOR UPDATE
                result = await db.execute(
                    update(Conversation)
                    .where(Conversation.id == conversation_id)
                    .values(
                        message_count=count,
                        total_tokens=total_tokens
                    )
                )
                
                if result.rowcount > 0:
                    await db.commit()
                    logger.debug(
                        f"✅ [统计] 异步更新会话统计成功: "
                        f"会话{conversation_id}, 消息数={count}, tokens={total_tokens}"
                    )
                else:
                    # 会话不存在（可能被删除）
                    logger.debug(
                        f"⏭️ [统计] 会话{conversation_id}不存在，跳过统计更新"
                    )
        
        except Exception as e:
            # 统计更新失败不影响消息保存，只记录警告
            from sqlalchemy.exc import OperationalError
            if isinstance(e, OperationalError) and hasattr(e, 'orig') and hasattr(e.orig, 'args'):
                error_code = e.orig.args[0] if e.orig.args else None
                if error_code == 1205:
                    # 锁等待超时（防御性处理）
                    logger.debug(
                        f"⏭️ [统计] 会话{conversation_id}统计更新跳过（记录被锁定）"
                    )
                    return
            
            logger.warning(
                f"⚠️ [统计] 异步更新会话统计失败（可忽略）: "
                f"会话{conversation_id}, 错误: {e}"
            )
    
    # ============== 语义搜索相关方法 ==============
    
    async def search_relevant_chunks(
        self,
        conversation_id: int,
        query_text: str,
        top_k: int = 5,
        threshold: float = 0.7
    ) -> List[Dict]:
        """
        从向量库搜索相关历史片段（数据访问层）
        
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
            
            # 批量查询所有消息ID（修复N+1查询问题）
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
                
                # 从字典中快速查找消息（O(1)复杂度）
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
        基于搜索结果构建消息上下文（数据访问层）
        
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
    
    # ============== 向量化相关方法 ==============
    
    async def embed_conversation_async(
        self,
        conversation_id: int,
        user_message_id: int,
        assistant_message_id: int
    ):
        """
        异步向量化对话片段（后台任务，数据访问层）
        
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
    
    async def save_conversation_async(
        self,
        conversation_id: int,
        user_message: str,
        assistant_message: str,
        user_tokens: int = 0,
        assistant_tokens: int = 0,
        user_status: str = MessageStatus.SUCCESS.value,
        assistant_status: str = MessageStatus.SUCCESS.value,
        user_error_message: Optional[str] = None,
        assistant_error_message: Optional[str] = None
    ):
        """
        异步保存对话消息（后台任务，数据访问层）
        
        注意：此方法在后台任务中调用，需要创建新的数据库会话
        
        优化策略：
        - 只插入消息，不更新统计（避免锁冲突）
        - 统计信息通过独立异步任务更新
        
        Args:
            conversation_id: 会话ID
            user_message: 用户消息内容
            assistant_message: AI回复内容
            user_tokens: 用户消息token数
            assistant_tokens: AI回复token数
            user_status: 用户消息状态，默认success
            assistant_status: AI回复状态，默认success
            user_error_message: 用户消息错误信息（可选）
            assistant_error_message: AI回复错误信息（可选）
        """
        # 在后台任务中创建新的数据库会话
        from db.session import async_session_maker
        
        # 使用重试机制处理锁等待超时
        import asyncio
        from sqlalchemy.exc import OperationalError, DBAPIError
        
        max_retries = 3
        base_delay = 0.1
        
        for attempt in range(max_retries):
            try:
                async with async_session_maker() as db:
                    # 使用时间戳生成sequence，避免查询数据库导致的并发冲突
                    from utils.sequence import generate_sequence_pair
                    user_sequence, assistant_sequence = generate_sequence_pair()
                    
                    # 只插入消息，不更新统计（避免锁冲突）
                    user_msg = ConversationMessage(
                        conversation_id=conversation_id,
                        role="user",
                        content=user_message,
                        tokens=user_tokens,
                        sequence=user_sequence,
                        embedding_status=EmbeddingStatus.PENDING.value,
                        status=user_status,
                        error_message=user_error_message,
                    )
                    
                    assistant_msg = ConversationMessage(
                        conversation_id=conversation_id,
                        role="assistant",
                        content=assistant_message,
                        tokens=assistant_tokens,
                        sequence=assistant_sequence,
                        embedding_status=EmbeddingStatus.PENDING.value,
                        status=assistant_status,
                        error_message=assistant_error_message,
                    )
                    
                    db.add(user_msg)
                    db.add(assistant_msg)
                    
                    # 立即提交，不锁定Conversation表（避免锁冲突）
                    await db.commit()
                    
                    logger.info(
                        f"✅ [优化] 已保存对话消息: 会话{conversation_id}, "
                        f"消息{user_msg.id}-{assistant_msg.id}, "
                        f"尝试次数: {attempt + 1}"
                    )
                    
                    # 异步更新统计（独立事务，失败不影响消息保存）
                    asyncio.create_task(
                        self.update_conversation_stats_async(conversation_id)
                    )
                    
                    return  # 成功，直接返回
            
            except (OperationalError, DBAPIError) as e:
                # 检查是否是锁等待超时或死锁错误
                error_code = None
                if hasattr(e, 'orig') and hasattr(e.orig, 'args'):
                    error_code = e.orig.args[0] if e.orig.args else None
                
                # 1205: Lock wait timeout exceeded
                # 1213: Deadlock found when trying to get lock
                is_lock_error = error_code in (1205, 1213)
                
                if is_lock_error and attempt < max_retries - 1:
                    # 指数退避: 0.1s, 0.2s, 0.3s
                    delay = base_delay * (attempt + 1)
                    logger.warning(
                        f"⚠️ [优化] 保存对话时遇到间隙锁冲突(尝试 {attempt + 1}/{max_retries}): "
                        f"错误码={error_code}, {delay}秒后重试..."
                    )
                    await asyncio.sleep(delay)
                    continue
                else:
                    # 最后一次重试失败或非锁错误，抛出异常
                    logger.error(
                        f"❌ [优化] 保存对话失败(尝试 {attempt + 1}/{max_retries}): "
                        f"错误码={error_code}, {str(e)}"
                    )
                    raise
            
            except Exception as e:
                # 其他异常，直接抛出
                logger.error(f"❌ [优化] 保存对话时发生未预期错误: {str(e)}")
                raise

