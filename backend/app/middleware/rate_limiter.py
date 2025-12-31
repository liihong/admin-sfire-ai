"""
API Rate Limiter Middleware
API 请求频率限制中间件

功能:
- 监控每个用户的 API 调用次数
- 1 分钟内超过 60 次调用自动标记为异常
- 记录异常用户到 Redis
"""
import json
import time
from datetime import datetime
from typing import Optional, List, Dict, Any
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from loguru import logger

from app.db.redis import redis_client


# Redis 键前缀
RATE_LIMIT_PREFIX = "rate_limit:"           # 用户调用计数前缀
ABNORMAL_USERS_KEY = "dashboard:abnormal_users"  # 异常用户列表键

# 限流配置
RATE_LIMIT_WINDOW = 60      # 时间窗口（秒）: 1 分钟
RATE_LIMIT_MAX_CALLS = 60   # 最大调用次数: 60 次/分钟
ABNORMAL_RECORD_LIMIT = 100  # 最多保留的异常记录数


class RateLimiter:
    """
    API 限流器
    
    使用 Redis 实现滑动窗口限流
    """
    
    @staticmethod
    async def check_and_increment(
        user_id: int,
        endpoint: str,
        ip_address: str = "",
    ) -> tuple[bool, int]:
        """
        检查并增加用户调用计数
        
        Args:
            user_id: 用户 ID
            endpoint: 请求的接口路径
            ip_address: 客户端 IP 地址
        
        Returns:
            tuple[bool, int]: (是否超过限制, 当前调用次数)
        """
        if not redis_client:
            # Redis 不可用时，跳过限流检查
            return False, 0
        
        key = f"{RATE_LIMIT_PREFIX}{user_id}"
        current_time = int(time.time())
        window_start = current_time - RATE_LIMIT_WINDOW
        
        try:
            # 使用 Redis Pipeline 保证原子性
            async with redis_client.pipeline() as pipe:
                # 移除过期的调用记录
                await pipe.zremrangebyscore(key, 0, window_start)
                # 添加当前调用记录
                await pipe.zadd(key, {str(current_time * 1000 + hash(endpoint) % 1000): current_time})
                # 获取当前窗口内的调用次数
                await pipe.zcard(key)
                # 设置键的过期时间
                await pipe.expire(key, RATE_LIMIT_WINDOW + 10)
                
                results = await pipe.execute()
                call_count = results[2]  # zcard 的结果
            
            # 判断是否超过限制
            is_exceeded = call_count > RATE_LIMIT_MAX_CALLS
            
            if is_exceeded:
                # 记录异常用户
                await RateLimiter.record_abnormal_user(
                    user_id=user_id,
                    call_count=call_count,
                    endpoint=endpoint,
                    ip_address=ip_address,
                )
                logger.warning(
                    f"Rate limit exceeded: user_id={user_id}, "
                    f"calls={call_count}, endpoint={endpoint}"
                )
            
            return is_exceeded, call_count
            
        except Exception as e:
            logger.error(f"Rate limiter error: {e}")
            return False, 0
    
    @staticmethod
    async def record_abnormal_user(
        user_id: int,
        call_count: int,
        endpoint: str,
        ip_address: str = "",
    ) -> None:
        """
        记录异常用户
        
        Args:
            user_id: 用户 ID
            call_count: 调用次数
            endpoint: 请求的接口路径
            ip_address: 客户端 IP 地址
        """
        if not redis_client:
            return
        
        try:
            record = {
                "user_id": user_id,
                "call_count": call_count,
                "endpoint": endpoint,
                "ip_address": ip_address,
                "reason": f"1分钟内调用API {call_count} 次，超过限制 {RATE_LIMIT_MAX_CALLS} 次",
                "detected_at": datetime.now().isoformat(),
                "timestamp": int(time.time()),
            }
            
            # 使用 List 存储异常记录，新记录插入到头部
            await redis_client.lpush(ABNORMAL_USERS_KEY, json.dumps(record, ensure_ascii=False))
            
            # 保持列表长度不超过限制
            await redis_client.ltrim(ABNORMAL_USERS_KEY, 0, ABNORMAL_RECORD_LIMIT - 1)
            
            logger.info(f"Abnormal user recorded: {record}")
            
        except Exception as e:
            logger.error(f"Failed to record abnormal user: {e}")
    
    @staticmethod
    async def get_abnormal_users(limit: int = 5) -> List[Dict[str, Any]]:
        """
        获取最近的异常用户记录
        
        Args:
            limit: 返回的记录数量，默认 5 条
        
        Returns:
            List[Dict]: 异常用户记录列表
        """
        if not redis_client:
            return []
        
        try:
            # 从 Redis 获取最近的异常记录
            records = await redis_client.lrange(ABNORMAL_USERS_KEY, 0, limit - 1)
            
            abnormal_users = []
            for record_str in records:
                try:
                    record = json.loads(record_str)
                    abnormal_users.append(record)
                except json.JSONDecodeError:
                    continue
            
            return abnormal_users
            
        except Exception as e:
            logger.error(f"Failed to get abnormal users: {e}")
            return []
    
    @staticmethod
    async def get_user_call_count(user_id: int) -> int:
        """
        获取用户当前的调用次数
        
        Args:
            user_id: 用户 ID
        
        Returns:
            int: 当前调用次数
        """
        if not redis_client:
            return 0
        
        try:
            key = f"{RATE_LIMIT_PREFIX}{user_id}"
            current_time = int(time.time())
            window_start = current_time - RATE_LIMIT_WINDOW
            
            # 移除过期记录
            await redis_client.zremrangebyscore(key, 0, window_start)
            # 获取当前窗口内的调用次数
            count = await redis_client.zcard(key)
            
            return count or 0
            
        except Exception as e:
            logger.error(f"Failed to get user call count: {e}")
            return 0
    
    @staticmethod
    async def clear_abnormal_records() -> bool:
        """
        清空异常记录
        
        Returns:
            bool: 是否成功
        """
        if not redis_client:
            return False
        
        try:
            await redis_client.delete(ABNORMAL_USERS_KEY)
            return True
        except Exception as e:
            logger.error(f"Failed to clear abnormal records: {e}")
            return False


class RateLimiterMiddleware(BaseHTTPMiddleware):
    """
    API 限流中间件
    
    功能:
    - 从请求中提取用户 ID
    - 检查用户调用频率
    - 超过限制时记录异常并返回 429 状态码
    """
    
    # 不需要限流的路径
    EXCLUDED_PATHS = {
        "/docs",
        "/redoc",
        "/openapi.json",
        "/health",
        "/api/v1/auth/login",
        "/api/v1/auth/refresh",
        "/api/v1/dashboard/stats",
        "/api/v1/dashboard/overview",
        "/api/v1/dashboard/api-monitoring",
        "/api/v1/dashboard/charts",
    }
    
    async def dispatch(self, request: Request, call_next) -> Response:
        """
        处理请求
        
        Args:
            request: HTTP 请求
            call_next: 下一个处理函数
        
        Returns:
            Response: HTTP 响应
        """
        # 检查是否需要跳过限流
        path = request.url.path
        if path in self.EXCLUDED_PATHS or not path.startswith("/api/"):
            return await call_next(request)
        
        # 尝试从请求中获取用户 ID
        user_id = await self._extract_user_id(request)
        
        if user_id:
            # 获取客户端 IP
            ip_address = self._get_client_ip(request)
            
            # 检查限流
            is_exceeded, call_count = await RateLimiter.check_and_increment(
                user_id=user_id,
                endpoint=path,
                ip_address=ip_address,
            )
            
            if is_exceeded:
                # 返回 429 Too Many Requests
                return Response(
                    content=json.dumps({
                        "code": 429,
                        "data": None,
                        "msg": f"请求过于频繁，请稍后再试。当前1分钟内已调用 {call_count} 次，限制 {RATE_LIMIT_MAX_CALLS} 次。"
                    }, ensure_ascii=False),
                    status_code=429,
                    media_type="application/json",
                )
        
        return await call_next(request)
    
    async def _extract_user_id(self, request: Request) -> Optional[int]:
        """
        从请求中提取用户 ID
        
        尝试从 JWT Token 中解析用户 ID
        
        Args:
            request: HTTP 请求
        
        Returns:
            Optional[int]: 用户 ID，未找到返回 None
        """
        try:
            # 从 Authorization header 获取 token
            authorization = request.headers.get("Authorization", "")
            if not authorization.startswith("Bearer "):
                return None
            
            token = authorization[7:]  # 移除 "Bearer " 前缀
            
            # 解码 JWT Token
            from app.core.security import decode_token
            payload = decode_token(token)
            
            if payload:
                user_id = payload.get("sub")
                if user_id:
                    return int(user_id)
            
            return None
            
        except Exception as e:
            logger.debug(f"Failed to extract user_id from request: {e}")
            return None
    
    def _get_client_ip(self, request: Request) -> str:
        """
        获取客户端 IP 地址
        
        Args:
            request: HTTP 请求
        
        Returns:
            str: 客户端 IP 地址
        """
        # 尝试从 X-Forwarded-For 获取（反向代理情况）
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        # 尝试从 X-Real-IP 获取
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        # 直接获取客户端地址
        if request.client:
            return request.client.host
        
        return ""


