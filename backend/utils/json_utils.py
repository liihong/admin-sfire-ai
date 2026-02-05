"""
JSON工具函数
确保所有JSON序列化都使用 ensure_ascii=False，支持中文
"""
import json
from typing import Any


def json_dumps(obj: Any, **kwargs) -> str:
    """
    JSON序列化，默认使用 ensure_ascii=False 支持中文
    
    Args:
        obj: 要序列化的对象
        **kwargs: 其他json.dumps参数
    
    Returns:
        JSON字符串
    """
    kwargs.setdefault('ensure_ascii', False)
    return json.dumps(obj, **kwargs)


def json_loads(s: str, **kwargs) -> Any:
    """
    JSON反序列化
    
    Args:
        s: JSON字符串
        **kwargs: 其他json.loads参数
    
    Returns:
        反序列化后的对象
    """
    return json.loads(s, **kwargs)






