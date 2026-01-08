"""
Redis Connection Management
"""
from typing import Optional
import redis.asyncio as aioredis
from redis.asyncio import Redis
from loguru import logger

from core.config import settings


# Redis 客户端实例
redis_client: Optional[Redis] = None


async def init_redis() -> None:
    """
    初始化 Redis 连接
    在应用启动时调用
    
    注意：Redis 是可选的，连接失败不会阻止应用启动
    """
    global redis_client
    
    logger.info("Initializing Redis connection...")
    
    try:
        redis_client = aioredis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
            socket_connect_timeout=2,  # 连接超时 2 秒
            socket_timeout=2,  # 操作超时 2 秒
        )
        
        # 测试连接
        await redis_client.ping()
        logger.info("Redis connection initialized successfully")
    except Exception as e:
        logger.warning(
            f"Redis connection failed: {e}. "
            "Application will continue without Redis. "
            "Rate limiting and caching features will be disabled."
        )
        redis_client = None
        
        # 如果创建了连接但测试失败，关闭它
        try:
            if redis_client:
                await redis_client.close()
        except:
            pass
        redis_client = None


async def close_redis() -> None:
    """
    关闭 Redis 连接
    在应用关闭时调用
    """
    global redis_client
    
    if redis_client:
        logger.info("Closing Redis connection...")
        await redis_client.close()
        logger.info("Redis connection closed")


async def get_redis() -> Optional[Redis]:
    """
    获取 Redis 客户端
    
    Returns:
        Redis 客户端实例，如果未初始化则返回 None
    """
    return redis_client


class RedisCache:
    """Redis 缓存工具类"""
    
    @staticmethod
    async def get(key: str) -> Optional[str]:
        """获取缓存值"""
        if redis_client:
            return await redis_client.get(key)
        return None
    
    @staticmethod
    async def set(
        key: str,
        value: str,
        expire: int = 3600
    ) -> bool:
        """设置缓存值"""
        if redis_client:
            await redis_client.set(key, value, ex=expire)
            return True
        return False
    
    @staticmethod
    async def delete(key: str) -> bool:
        """删除缓存"""
        if redis_client:
            await redis_client.delete(key)
            return True
        return False
    
    @staticmethod
    async def exists(key: str) -> bool:
        """检查键是否存在"""
        if redis_client:
            return await redis_client.exists(key) > 0
        return False
    
    @staticmethod
    async def expire(key: str, seconds: int) -> bool:
        """设置过期时间"""
        if redis_client:
            return await redis_client.expire(key, seconds)
        return False






