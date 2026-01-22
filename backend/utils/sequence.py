"""
序列号生成工具
用于生成基于时间戳的唯一序列号，避免数据库查询导致的并发冲突
支持Redis原子递增模式（推荐）和时间戳模式（fallback）
"""
import time
import random
from typing import Optional
from loguru import logger

from db.redis import get_redis


def generate_sequence() -> int:
    """
    生成基于时间戳的序列号
    
    格式: 时间戳(毫秒) * 100000 + 随机数(5位)
    示例: 1705320653123 * 100000 + 12345 = 1705320653123012345
    
    优点:
    - 时间戳保证顺序性（按时间排序）
    - 随机数保证唯一性（降低碰撞概率）
    - 无需查询数据库，避免并发冲突
    
    Returns:
        int: 序列号（BIGINT类型，最大19位）
    """
    timestamp_ms = int(time.time() * 1000)  # 毫秒时间戳（13位）
    random_suffix = random.randint(0, 99999)  # 5位随机数（0-99999）
    return timestamp_ms * 100000 + random_suffix


def generate_sequence_pair() -> tuple[int, int]:
    """
    生成一对序列号（用于user和assistant消息）
    
    返回的序列号保证:
    - user_sequence < assistant_sequence
    - 两者在同一时间窗口内，便于后续查找
    
    Returns:
        tuple[int, int]: (user_sequence, assistant_sequence)
    """
    base_sequence = generate_sequence()
    return base_sequence, base_sequence + 1


async def generate_message_sequence(conversation_id: int) -> int:
    """
    使用Redis原子递增生成消息序列号（推荐方式）
    
    优点:
    - 保证唯一性（Redis原子操作）
    - 保证顺序性（递增）
    - 避免并发冲突
    
    Args:
        conversation_id: 会话ID
    
    Returns:
        int: 序列号（如果Redis不可用，fallback到时间戳模式）
    """
    redis = await get_redis()
    if not redis:
        logger.debug("Redis不可用，使用时间戳模式生成序列号")
        return generate_sequence()
    
    sequence_key = f"conversation:seq:{conversation_id}"
    
    try:
        # 使用INCR原子操作，保证唯一性和顺序性
        sequence = await redis.incr(sequence_key)
        
        # 设置过期时间（24小时），避免键无限增长
        await redis.expire(sequence_key, 86400)
        
        # 将Redis序列号转换为时间戳格式（保持兼容性）
        # 格式：时间戳(毫秒) * 100000 + Redis序列号（取后5位）
        timestamp_ms = int(time.time() * 1000)
        redis_suffix = sequence % 100000  # 取后5位
        return timestamp_ms * 100000 + redis_suffix
        
    except Exception as e:
        logger.warning(f"Redis序列号生成失败，使用时间戳模式: {e}")
        return generate_sequence()


async def generate_message_sequence_pair(conversation_id: int) -> tuple[int, int]:
    """
    使用Redis原子递增生成一对序列号（用于user和assistant消息）
    
    Args:
        conversation_id: 会话ID
    
    Returns:
        tuple[int, int]: (user_sequence, assistant_sequence)
    """
    user_sequence = await generate_message_sequence(conversation_id)
    assistant_sequence = await generate_message_sequence(conversation_id)
    
    # 确保 user_sequence < assistant_sequence
    if user_sequence >= assistant_sequence:
        assistant_sequence = user_sequence + 1
    
    return user_sequence, assistant_sequence








