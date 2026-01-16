"""
序列号生成工具
用于生成基于时间戳的唯一序列号，避免数据库查询导致的并发冲突
"""
import time
import random


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

