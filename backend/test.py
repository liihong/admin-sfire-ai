import secrets
import zlib  # 修正：使用 zlib 处理 CRC32

def generate_api_v2_key(prefix="sk", env="live"):
    """
    生成一个结构化的 APIv2 密钥
    格式: prefix_env_randomString_checksum
    """
    # 1. 生成加密级随机字符串 (32字节)
    random_part = secrets.token_urlsafe(32).replace('-', '').replace('_', '')
    
    # 2. 构造有效负载
    payload = f"{prefix}_{env}_{random_part}"
    
    # 3. 计算 CRC32 校验码
    # zlib.crc32 返回的是无符号整数
    checksum_int = zlib.crc32(payload.encode()) & 0xffffffff
    # 转换为 2 字节（4位16进制）作为简易校验码
    checksum = (checksum_int & 0xffff).to_bytes(2, 'big').hex()
    
    full_key = f"{payload}_{checksum}"
    return full_key

# 测试
try:
    new_key = generate_api_v2_key("myapi", "prod")
    print(f"✅ 成功生成 APIv2 密钥:\n{new_key}")
except Exception as e:
    print(f"❌ 出错: {e}")