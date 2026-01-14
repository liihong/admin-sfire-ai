"""
重新索引所有对话数据到向量数据库
将所有已完成的对话消息重新向量化并存储到向量数据库（使用1024维）
"""
import asyncio
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.session import init_db, async_session_maker, close_db
from models.conversation import ConversationMessage, ConversationChunk, EmbeddingStatus
from services.conversation import ConversationService
from services.embedding import get_embedding_service
from services.vector_db import get_vector_db_service


async def reindex_conversations():
    """
    重新索引所有对话数据
    """
    logger.info("=" * 50)
    logger.info("开始重新索引对话数据到向量数据库（1024维）...")
    logger.info("=" * 50)
    
    # 初始化数据库连接
    await init_db()
    
    # 初始化向量数据库（1024维）
    vector_db = get_vector_db_service(dimension=1024)
    embedding_service = get_embedding_service()
    
    stats = vector_db.get_stats()
    logger.info(f"向量数据库当前状态: {stats}")
    
    async with async_session_maker() as db:
        try:
            # 查询所有需要向量化的消息对（用户消息和助手消息配对）
            # 只处理已完成的消息对
            query = select(ConversationMessage).where(
                ConversationMessage.role == "user"
            ).order_by(ConversationMessage.conversation_id, ConversationMessage.sequence)
            
            result = await db.execute(query)
            user_messages = result.scalars().all()
            
            logger.info(f"找到 {len(user_messages)} 条用户消息")
            
            processed_count = 0
            success_count = 0
            error_count = 0
            
            for user_msg in user_messages:
                try:
                    # 查找对应的助手消息（sequence + 1）
                    assistant_query = select(ConversationMessage).where(
                        ConversationMessage.conversation_id == user_msg.conversation_id,
                        ConversationMessage.sequence == user_msg.sequence + 1,
                        ConversationMessage.role == "assistant"
                    )
                    assistant_result = await db.execute(assistant_query)
                    assistant_msg = assistant_result.scalar_one_or_none()
                    
                    if not assistant_msg:
                        logger.debug(f"未找到用户消息 {user_msg.id} 对应的助手消息，跳过")
                        continue
                    
                    # 检查是否已经存在chunk
                    chunk_query = select(ConversationChunk).where(
                        ConversationChunk.conversation_id == user_msg.conversation_id,
                        ConversationChunk.user_message_id == user_msg.id,
                        ConversationChunk.assistant_message_id == assistant_msg.id
                    )
                    chunk_result = await db.execute(chunk_query)
                    existing_chunk = chunk_result.scalar_one_or_none()
                    
                    # 组合对话片段文本
                    chunk_text = f"用户: {user_msg.content}\n\n助手: {assistant_msg.content}"
                    
                    # 更新状态为处理中
                    user_msg.embedding_status = EmbeddingStatus.PROCESSING.value
                    assistant_msg.embedding_status = EmbeddingStatus.PROCESSING.value
                    await db.flush()
                    
                    # 生成向量（使用1024维）
                    embedding = await embedding_service.generate_embedding(chunk_text, dimensions=1024)
                    
                    if embedding is None:
                        # 向量化失败
                        user_msg.embedding_status = EmbeddingStatus.FAILED.value
                        assistant_msg.embedding_status = EmbeddingStatus.FAILED.value
                        await db.flush()
                        logger.error(f"向量化失败: 会话{user_msg.conversation_id}, 消息{user_msg.id}-{assistant_msg.id}")
                        error_count += 1
                        continue
                    
                    # 生成向量ID
                    vector_id = f"conv_{user_msg.conversation_id}_chunk_{user_msg.id}_{assistant_msg.id}"
                    
                    # 保存到向量数据库
                    success = vector_db.add_embedding(
                        vector_id=vector_id,
                        embedding=embedding,
                        metadata={
                            "conversation_id": user_msg.conversation_id,
                            "user_message_id": user_msg.id,
                            "assistant_message_id": assistant_msg.id,
                            "chunk_text": chunk_text,
                        }
                    )
                    
                    if success:
                        # 创建或更新ConversationChunk记录
                        if not existing_chunk:
                            chunk = ConversationChunk(
                                conversation_id=user_msg.conversation_id,
                                user_message_id=user_msg.id,
                                assistant_message_id=assistant_msg.id,
                                chunk_text=chunk_text,
                                vector_id=vector_id,
                            )
                            db.add(chunk)
                        else:
                            existing_chunk.vector_id = vector_id
                            existing_chunk.chunk_text = chunk_text
                        
                        # 更新消息状态
                        user_msg.embedding_status = EmbeddingStatus.COMPLETED.value
                        assistant_msg.embedding_status = EmbeddingStatus.COMPLETED.value
                        
                        await db.flush()
                        success_count += 1
                        
                        if success_count % 10 == 0:
                            logger.info(f"已处理 {success_count} 条消息对...")
                    else:
                        # 向量数据库保存失败
                        user_msg.embedding_status = EmbeddingStatus.FAILED.value
                        assistant_msg.embedding_status = EmbeddingStatus.FAILED.value
                        await db.flush()
                        logger.error(f"向量数据库保存失败: 会话{user_msg.conversation_id}")
                        error_count += 1
                    
                    processed_count += 1
                    
                except Exception as e:
                    logger.error(f"处理消息对失败: {e}", exc_info=True)
                    error_count += 1
                    # 更新状态为失败
                    try:
                        user_msg.embedding_status = EmbeddingStatus.FAILED.value
                        if assistant_msg:
                            assistant_msg.embedding_status = EmbeddingStatus.FAILED.value
                        await db.flush()
                    except:
                        pass
            
            # 提交所有更改
            await db.commit()
            
            logger.info("=" * 50)
            logger.info("重新索引完成！")
            logger.info(f"总计处理: {processed_count} 条消息对")
            logger.info(f"成功: {success_count} 条")
            logger.info(f"失败: {error_count} 条")
            logger.info("=" * 50)
            
            # 显示最终统计
            final_stats = vector_db.get_stats()
            logger.info(f"向量数据库最终状态: {final_stats}")
            
        except Exception as e:
            logger.error(f"重新索引失败: {e}", exc_info=True)
            await db.rollback()
            raise
    
    # 关闭数据库连接
    await close_db()


if __name__ == "__main__":
    asyncio.run(reindex_conversations())













