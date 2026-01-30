"""
Redis Connection Management
"""
from typing import Optional, Any, Dict, List
import json
import redis.asyncio as aioredis
from redis.asyncio import Redis
from loguru import logger

from core.config import settings
from utils.json_utils import json_dumps, json_loads


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
    """Redis 缓存工具类（支持JSON序列化）"""
    
    @staticmethod
    async def get(key: str) -> Optional[str]:
        """获取缓存值（字符串）"""
        if redis_client:
            try:
                return await redis_client.get(key)
            except Exception as e:
                logger.warning(f"Redis get 失败: {key}, 错误: {e}")
                return None
        return None
    
    @staticmethod
    async def get_json(key: str) -> Optional[Any]:
        """获取缓存值（JSON对象）"""
        value = await RedisCache.get(key)
        if value:
            try:
                return json_loads(value)
            except (json.JSONDecodeError, TypeError):
                logger.warning(f"Redis JSON解析失败: {key}")
                return None
        return None
    
    @staticmethod
    async def set(
        key: str,
        value: str,
        expire: int = 3600
    ) -> bool:
        """设置缓存值（字符串）"""
        if redis_client:
            try:
                await redis_client.set(key, value, ex=expire)
                return True
            except Exception as e:
                logger.warning(f"Redis set 失败: {key}, 错误: {e}")
                return False
        return False
    
    @staticmethod
    async def set_json(
        key: str,
        value: Any,
        expire: int = 3600
    ) -> bool:
        """设置缓存值（JSON对象）"""
        try:
            json_str = json_dumps(value)
            return await RedisCache.set(key, json_str, expire)
        except (TypeError, ValueError) as e:
            logger.warning(f"Redis JSON序列化失败: {key}, 错误: {e}")
            return False
    
    @staticmethod
    async def delete(key: str) -> bool:
        """删除缓存"""
        if redis_client:
            try:
                await redis_client.delete(key)
                return True
            except Exception as e:
                logger.warning(f"Redis delete 失败: {key}, 错误: {e}")
                return False
        return False
    
    @staticmethod
    async def delete_pattern(pattern: str) -> int:
        """按模式删除缓存（支持通配符）"""
        if redis_client:
            try:
                keys = []
                async for key in redis_client.scan_iter(match=pattern):
                    keys.append(key)
                if keys:
                    return await redis_client.delete(*keys)
                return 0
            except Exception as e:
                logger.warning(f"Redis delete_pattern 失败: {pattern}, 错误: {e}")
                return 0
        return 0
    
    @staticmethod
    async def exists(key: str) -> bool:
        """检查键是否存在"""
        if redis_client:
            try:
                return await redis_client.exists(key) > 0
            except Exception as e:
                logger.warning(f"Redis exists 失败: {key}, 错误: {e}")
                return False
        return False
    
    @staticmethod
    async def expire(key: str, seconds: int) -> bool:
        """设置过期时间"""
        if redis_client:
            try:
                return await redis_client.expire(key, seconds)
            except Exception as e:
                logger.warning(f"Redis expire 失败: {key}, 错误: {e}")
                return False
        return False
    
    @staticmethod
    async def get_or_set(
        key: str,
        fetch_func,
        expire: int = 3600,
        use_json: bool = True
    ) -> Any:
        """
        获取缓存，如果不存在则调用fetch_func获取并缓存
        
        Args:
            key: 缓存键
            fetch_func: 获取数据的异步函数
            expire: 过期时间（秒）
            use_json: 是否使用JSON序列化
        
        Returns:
            缓存值或fetch_func的返回值
        """
        # 尝试从缓存获取
        if use_json:
            cached = await RedisCache.get_json(key)
        else:
            cached = await RedisCache.get(key)
        
        if cached is not None:
            return cached
        
        # 缓存未命中，调用fetch_func
        try:
            value = await fetch_func() if callable(fetch_func) else fetch_func
            
            # 写入缓存
            if use_json:
                await RedisCache.set_json(key, value, expire)
            else:
                await RedisCache.set(key, str(value), expire)
            
            return value
        except Exception as e:
            logger.warning(f"Redis get_or_set 执行fetch_func失败: {key}, 错误: {e}")
            # 即使缓存失败，也返回fetch_func的结果
            return value if 'value' in locals() else None






