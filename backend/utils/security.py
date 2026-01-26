"""
安全工具类
用于IP验证、签名验证等安全相关功能
"""
import ipaddress
from typing import List
from loguru import logger


def verify_ip_whitelist(client_ip: str, whitelist_str: str) -> bool:
    """
    验证IP是否在白名单内
    
    Args:
        client_ip: 客户端IP地址
        whitelist_str: 白名单字符串（逗号分隔的IP段，如 "182.254.48.0/24,140.207.54.0/24"）
    
    Returns:
        是否在白名单内
    """
    if not whitelist_str or not client_ip:
        return False
    
    try:
        # 解析白名单
        whitelist = [ip.strip() for ip in whitelist_str.split(",") if ip.strip()]
        
        if not whitelist:
            logger.warning("IP白名单为空，拒绝所有请求")
            return False
        
        # 检查IP是否在任何白名单段内
        client_ip_obj = ipaddress.ip_address(client_ip)
        
        for ip_range in whitelist:
            try:
                network = ipaddress.ip_network(ip_range, strict=False)
                if client_ip_obj in network:
                    return True
            except ValueError as e:
                logger.warning(f"无效的IP段格式: {ip_range}, 错误: {e}")
                continue
        
        return False
        
    except Exception as e:
        logger.error(f"IP白名单验证失败: {e}")
        return False

