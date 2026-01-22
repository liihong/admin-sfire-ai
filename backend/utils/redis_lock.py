"""
Redis分布式锁工具类
用于实现会话并发控制、用户并发限制、会话去重等功能
"""
import uuid
from typing import Optional
from loguru import logger

from db.redis import get_redis


class RedisLock:
    """Redis分布式锁工具类"""
    
    # 锁键前缀
    CONVERSATION_LOCK_PREFIX = "lock:conversation:"
    USER_CONVERSATION_COUNT_PREFIX = "user:conversation:count:"
    CONVERSATION_DUPLICATE_PREFIX = "conversation:duplicate:"
    
    # 默认超时时间（秒）
    DEFAULT_LOCK_TIMEOUT = 60
    DUPLICATE_CHECK_TTL = 300  # 5分钟
    
    @staticmethod
    async def acquire_conversation_lock(
        conversation_id: int,
        timeout: int = DEFAULT_LOCK_TIMEOUT
    ) -> Optional[str]:
        """
        获取会话锁（防止同一会话并发请求）
        
        Args:
            conversation_id: 会话ID
            timeout: 锁超时时间（秒），默认60秒
        
        Returns:
            锁标识符（用于释放锁），如果获取失败返回None
        """
        redis = await get_redis()
        if not redis:
            logger.warning("Redis不可用，跳过并发控制")
            return None
        
        lock_key = f"{RedisLock.CONVERSATION_LOCK_PREFIX}{conversation_id}"
        lock_value = str(uuid.uuid4())  # 唯一标识符，用于安全释放锁
        
        try:
            # 使用SET NX EX实现原子操作
            # NX: 只在键不存在时设置
            # EX: 设置过期时间（秒）
            result = await redis.set(lock_key, lock_value, nx=True, ex=timeout)
            
            if result:
                logger.debug(f"获取会话锁成功: conversation_id={conversation_id}")
                return lock_value
            else:
                logger.warning(f"获取会话锁失败（已被占用）: conversation_id={conversation_id}")
                return None
                
        except Exception as e:
            logger.error(f"获取会话锁异常: {e}")
            return None
    
    @staticmethod
    async def release_conversation_lock(
        conversation_id: int,
        lock_value: str
    ) -> bool:
        """
        释放会话锁
        
        Args:
            conversation_id: 会话ID
            lock_value: 锁标识符（必须匹配才能释放）
        
        Returns:
            是否成功释放
        """
        redis = await get_redis()
        if not redis:
            return False
        
        lock_key = f"{RedisLock.CONVERSATION_LOCK_PREFIX}{conversation_id}"
        
        try:
            # 使用Lua脚本确保原子性：只有锁值匹配时才删除
            lua_script = """
            if redis.call("get", KEYS[1]) == ARGV[1] then
                return redis.call("del", KEYS[1])
            else
                return 0
            end
            """
            result = await redis.eval(lua_script, 1, lock_key, lock_value)
            
            if result:
                logger.debug(f"释放会话锁成功: conversation_id={conversation_id}")
                return True
            else:
                logger.warning(f"释放会话锁失败（锁值不匹配或已过期）: conversation_id={conversation_id}")
                return False
                
        except Exception as e:
            logger.error(f"释放会话锁异常: {e}")
            return False
    
    @staticmethod
    async def check_user_conversation_limit(user_id: int, max_count: int = 3) -> bool:
        """
        检查用户并发会话限制
        
        Args:
            user_id: 用户ID
            max_count: 最大并发会话数，默认3个
        
        Returns:
            True-可以创建新会话，False-已达到上限
        """
        redis = await get_redis()
        if not redis:
            logger.warning("Redis不可用，跳过并发限制检查")
            return True
        
        count_key = f"{RedisLock.USER_CONVERSATION_COUNT_PREFIX}{user_id}"
        
        try:
            current_count = await redis.get(count_key)
            current_count = int(current_count) if current_count else 0
            
            if current_count >= max_count:
                logger.warning(
                    f"用户并发会话数已达上限: user_id={user_id}, "
                    f"当前={current_count}, 上限={max_count}"
                )
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"检查用户并发限制异常: {e}")
            return True  # 异常时允许创建，避免阻塞用户
    
    @staticmethod
    async def increment_user_conversation_count(user_id: int) -> bool:
        """
        增加用户并发会话计数
        
        Args:
            user_id: 用户ID
        
        Returns:
            是否成功
        """
        redis = await get_redis()
        if not redis:
            return False
        
        count_key = f"{RedisLock.USER_CONVERSATION_COUNT_PREFIX}{user_id}"
        
        try:
            await redis.incr(count_key)
            await redis.expire(count_key, 3600)  # 1小时过期
            return True
        except Exception as e:
            logger.error(f"增加用户并发计数异常: {e}")
            return False
    
    @staticmethod
    async def decrement_user_conversation_count(user_id: int) -> bool:
        """
        减少用户并发会话计数
        
        Args:
            user_id: 用户ID
        
        Returns:
            是否成功
        """
        redis = await get_redis()
        if not redis:
            return False
        
        count_key = f"{RedisLock.USER_CONVERSATION_COUNT_PREFIX}{user_id}"
        
        try:
            count = await redis.decr(count_key)
            if count <= 0:
                await redis.delete(count_key)  # 计数为0时删除键
            return True
        except Exception as e:
            logger.error(f"减少用户并发计数异常: {e}")
            return False
    
    @staticmethod
    async def check_conversation_duplicate(
        user_id: int,
        agent_id: Optional[int],
        project_id: Optional[int],
        ttl: int = DUPLICATE_CHECK_TTL
    ) -> Optional[int]:
        """
        检查会话去重（相同agent+project，5分钟内）
        
        Args:
            user_id: 用户ID
            agent_id: Agent ID（可选）
            project_id: 项目ID（可选）
            ttl: 去重检查时间窗口（秒），默认300秒（5分钟）
        
        Returns:
            如果存在重复会话，返回会话ID；否则返回None
        """
        redis = await get_redis()
        if not redis:
            return None
        
        # 构建去重键：user_id:agent_id:project_id
        duplicate_key = (
            f"{RedisLock.CONVERSATION_DUPLICATE_PREFIX}"
            f"{user_id}:{agent_id or 'none'}:{project_id or 'none'}"
        )
        
        try:
            conversation_id = await redis.get(duplicate_key)
            if conversation_id:
                logger.debug(
                    f"发现重复会话: user_id={user_id}, "
                    f"agent_id={agent_id}, project_id={project_id}, "
                    f"conversation_id={conversation_id}"
                )
                return int(conversation_id)
            return None
            
        except Exception as e:
            logger.error(f"检查会话去重异常: {e}")
            return None
    
    @staticmethod
    async def set_conversation_duplicate(
        user_id: int,
        agent_id: Optional[int],
        project_id: Optional[int],
        conversation_id: int,
        ttl: int = DUPLICATE_CHECK_TTL
    ) -> bool:
        """
        设置会话去重标记
        
        Args:
            user_id: 用户ID
            agent_id: Agent ID（可选）
            project_id: 项目ID（可选）
            conversation_id: 会话ID
            ttl: 过期时间（秒），默认300秒（5分钟）
        
        Returns:
            是否成功
        """
        redis = await get_redis()
        if not redis:
            return False
        
        duplicate_key = (
            f"{RedisLock.CONVERSATION_DUPLICATE_PREFIX}"
            f"{user_id}:{agent_id or 'none'}:{project_id or 'none'}"
        )
        
        try:
            await redis.set(duplicate_key, str(conversation_id), ex=ttl)
            return True
        except Exception as e:
            logger.error(f"设置会话去重标记异常: {e}")
            return False


