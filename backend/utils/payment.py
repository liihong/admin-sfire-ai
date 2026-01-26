"""
支付相关工具类
用于订单号生成、支付签名等
"""
import time
import random
import hashlib
import hmac
from typing import Dict, Any
from loguru import logger


async def generate_order_id(prefix: str = "R") -> str:
    """
    生成唯一订单号（使用Redis原子递增确保唯一性）
    
    格式: 前缀 + 时间戳(秒) + Redis序列号(6位)
    示例: R20240101123456789012
    
    Args:
        prefix: 订单号前缀，默认为 "R"（Recharge）
    
    Returns:
        订单号字符串
    """
    from db.redis import get_redis
    
    timestamp = int(time.time())
    
    # 尝试使用Redis原子递增
    redis = await get_redis()
    if redis:
        try:
            sequence_key = f"order:seq:{timestamp}"
            sequence = await redis.incr(sequence_key)
            await redis.expire(sequence_key, 60)  # 60秒过期
            # 取后6位
            suffix = str(sequence % 1000000).zfill(6)
            return f"{prefix}{timestamp}{suffix}"
        except Exception as e:
            logger.warning(f"Redis订单号生成失败，使用随机数: {e}")
    
    # Fallback: 使用时间戳+随机数
    random_suffix = random.randint(100000, 999999)  # 6位随机数
    return f"{prefix}{timestamp}{random_suffix}"


def generate_wechat_sign(params: Dict[str, Any], api_key: str) -> str:
    """
    生成微信支付签名
    
    签名算法：
    1. 将所有参数按key排序
    2. 拼接成 key1=value1&key2=value2 格式
    3. 拼接API密钥：stringA&key=API_KEY
    4. MD5加密并转大写
    
    Args:
        params: 参数字典
        api_key: 微信支付API密钥
    
    Returns:
        签名字符串（大写）
    """
    # 过滤空值和sign字段
    filtered_params = {
        k: v for k, v in params.items()
        if v is not None and v != "" and k != "sign"
    }
    
    # 按键名排序
    sorted_params = sorted(filtered_params.items())
    
    # 拼接字符串
    string_a = "&".join([f"{k}={v}" for k, v in sorted_params])
    string_sign_temp = f"{string_a}&key={api_key}"
    
    # MD5加密并转大写
    sign = hashlib.md5(string_sign_temp.encode("utf-8")).hexdigest().upper()
    
    return sign


def verify_wechat_sign(params: Dict[str, Any], api_key: str, sign: str) -> bool:
    """
    验证微信支付签名
    
    Args:
        params: 参数字典
        api_key: 微信支付API密钥
        sign: 待验证的签名
    
    Returns:
        是否验证通过
    """
    calculated_sign = generate_wechat_sign(params, api_key)
    return calculated_sign == sign.upper()


def format_amount(amount: float) -> int:
    """
    格式化金额（元转分）
    
    Args:
        amount: 金额（元）
    
    Returns:
        金额（分）
    """
    return int(amount * 100)


def parse_amount(amount: int) -> float:
    """
    解析金额（分转元）
    
    Args:
        amount: 金额（分）
    
    Returns:
        金额（元）
    """
    return amount / 100.0

