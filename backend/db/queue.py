"""
Redis Queue Manager for Conversation Save Operations
使用Redis List实现消息队列,解决会话保存时的数据库锁冲突问题
"""
import json
import asyncio
from typing import Optional, Dict, Any
from loguru import logger
from db.redis import get_redis


class ConversationQueue:
    """会话保存队列管理器"""

    # 队列键名
    QUEUE_KEY = "conversation:save:queue"
    PROCESSING_KEY = "conversation:save:processing"

    # 队列配置
    MAX_RETRIES = 3  # 最大重试次数
    RETRY_DELAY = 2  # 重试延迟(秒)
    QUEUE_TIMEOUT = 5  # 队列操作超时(秒)

    @staticmethod
    async def enqueue(
        conversation_id: int,
        user_message: str,
        assistant_message: str,
        user_tokens: int = 0,
        assistant_tokens: int = 0
    ) -> bool:
        """
        将保存任务加入队列

        Args:
            conversation_id: 会话ID
            user_message: 用户消息
            assistant_message: AI回复
            user_tokens: 用户消息token数
            assistant_tokens: AI回复token数

        Returns:
            是否成功加入队列
        """
        try:
            redis = await get_redis()
            if not redis:
                logger.warning("Redis未连接,跳过队列化处理")
                return False

            # 构建任务数据
            task_data = {
                "conversation_id": conversation_id,
                "user_message": user_message,
                "assistant_message": assistant_message,
                "user_tokens": user_tokens,
                "assistant_tokens": assistant_tokens,
                "retry_count": 0
            }

            # 将任务推入队列(左侧推入)
            await redis.lpush(
                ConversationQueue.QUEUE_KEY,
                json.dumps(task_data, ensure_ascii=False)
            )

            logger.info(
                f"✅ [队列] 会话保存任务已入队: "
                f"会话ID={conversation_id}, "
                f"用户消息长度={len(user_message)}, "
                f"AI回复长度={len(assistant_message)}"
            )

            return True

        except Exception as e:
            logger.error(f"❌ [队列] 入队失败: {e}")
            return False

    @staticmethod
    async def dequeue(timeout: int = QUEUE_TIMEOUT) -> Optional[Dict[str, Any]]:
        """
        从队列中取出一个任务(右侧取出,保证FIFO)

        Args:
            timeout: 阻塞等待超时时间(秒)

        Returns:
            任务数据字典,如果队列为空则返回None
        """
        try:
            redis = await get_redis()
            if not redis:
                return None

            # 从队列右侧阻塞弹出(FIFO)
            result = await redis.brpop(
                ConversationQueue.QUEUE_KEY,
                timeout=timeout
            )

            if not result:
                return None

            # result 是 tuple: (queue_name, task_data_json)
            _, task_json = result
            task_data = json.loads(task_json)

            logger.debug(f"📤 [队列] 取出任务: 会话ID={task_data.get('conversation_id')}")

            return task_data

        except asyncio.TimeoutError:
            return None
        except Exception as e:
            logger.error(f"❌ [队列] 出队失败: {e}")
            return None

    @staticmethod
    async def get_queue_size() -> int:
        """获取当前队列大小"""
        try:
            redis = await get_redis()
            if not redis:
                return 0

            size = await redis.llen(ConversationQueue.QUEUE_KEY)
            return size

        except Exception as e:
            logger.error(f"❌ [队列] 获取队列大小失败: {e}")
            return 0

    @staticmethod
    async def retry_task(task_data: Dict[str, Any]) -> bool:
        """
        重新将失败的任务加入队列

        Args:
            task_data: 任务数据

        Returns:
            是否成功重新加入队列
        """
        retry_count = task_data.get("retry_count", 0)

        if retry_count >= ConversationQueue.MAX_RETRIES:
            logger.error(
                f"❌ [队列] 任务重试次数已达上限: "
                f"会话ID={task_data.get('conversation_id')}, "
                f"重试次数={retry_count}"
            )
            return False

        # 增加重试计数
        task_data["retry_count"] = retry_count + 1

        # 延迟后重新入队
        await asyncio.sleep(ConversationQueue.RETRY_DELAY)

        try:
            redis = await get_redis()
            if not redis:
                return False

            await redis.lpush(
                ConversationQueue.QUEUE_KEY,
                json.dumps(task_data, ensure_ascii=False)
            )

            logger.warning(
                f"⚠️ [队列] 任务重新入队: "
                f"会话ID={task_data.get('conversation_id')}, "
                f"重试次数={retry_count + 1}/{ConversationQueue.MAX_RETRIES}"
            )

            return True

        except Exception as e:
            logger.error(f"❌ [队列] 重试入队失败: {e}")
            return False


# 队列Worker处理器
async def conversation_queue_worker(worker_id: str, stop_event: asyncio.Event):
    """
    会话保存队列Worker

    Args:
        worker_id: Worker标识
        stop_event: 停止事件
    """
    logger.info(f"🚀 [队列Worker-{worker_id}] 启动")

    from db.session import async_session_maker
    from services.conversation.dao import ConversationDAO
    from sqlalchemy import select, desc
    from models.conversation import ConversationMessage

    while not stop_event.is_set():
        try:
            # 1. 从队列取出任务
            task_data = await ConversationQueue.dequeue(timeout=1)

            if not task_data:
                continue  # 队列为空,继续等待

            conversation_id = task_data.get("conversation_id")

            # 2. 处理保存任务
            async with async_session_maker() as db:
                dao = ConversationDAO(db)

                await dao.save_conversation_async(
                    conversation_id=task_data["conversation_id"],
                    user_message=task_data["user_message"],
                    assistant_message=task_data["assistant_message"],
                    user_tokens=task_data.get("user_tokens", 0),
                    assistant_tokens=task_data.get("assistant_tokens", 0)
                )

                logger.info(
                    f"✅ [队列Worker-{worker_id}] 保存完成: "
                    f"会话ID={conversation_id}"
                )

            # 3. 触发向量化任务
            async with async_session_maker() as db:
                # 查询最新的两条消息（user + assistant）
                query = select(ConversationMessage).where(
                    ConversationMessage.conversation_id == conversation_id
                ).order_by(desc(ConversationMessage.sequence)).limit(2)

                result = await db.execute(query)
                messages = list(result.scalars().all())

                if len(messages) == 2:
                    # messages[0]是assistant, messages[1]是user（降序）
                    assistant_msg = messages[0]
                    user_msg = messages[1]

                    # 触发向量化任务
                    from routers.client.creation import embed_conversation_background_task
                    await embed_conversation_background_task(
                        conversation_id=conversation_id,
                        user_message_id=user_msg.id,
                        assistant_message_id=assistant_msg.id
                    )

                    logger.info(
                        f"✅ [队列Worker-{worker_id}] 向量化任务已触发: "
                        f"会话ID={conversation_id}, "
                        f"消息ID={user_msg.id}-{assistant_msg.id}"
                    )

        except Exception as e:
            logger.error(
                f"❌ [队列Worker-{worker_id}] 处理失败: "
                f"会话ID={task_data.get('conversation_id')}, "
                f"错误={e}"
            )

            # 重试逻辑
            if task_data:
                retry_success = await ConversationQueue.retry_task(task_data)
                if not retry_success:
                    # 重试失败,记录到错误日志
                    logger.error(
                        f"❌ [队列Worker-{worker_id}] 任务最终失败: "
                        f"会话ID={task_data.get('conversation_id')}, "
                        f"数据={task_data}"
                    )

    logger.info(f"🛑 [队列Worker-{worker_id}] 停止")
