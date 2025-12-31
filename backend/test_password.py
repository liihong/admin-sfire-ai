"""
测试密码加密和验证是否一致
"""
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent))

from app.core.security import hash_password, verify_password, get_password_hash

def test_password():
    """测试密码加密和验证"""
    # 预设密码
    plain_password = "admin123"
    
    print("=" * 50)
    print("密码加密和验证测试")
    print("=" * 50)
    print(f"原始密码: {plain_password}")
    print()
    
    # 测试 hash_password
    hashed1 = hash_password(plain_password)
    print(f"hash_password() 结果: {hashed1}")
    print(f"验证结果: {verify_password(plain_password, hashed1)}")
    print()
    
    # 测试 get_password_hash
    hashed2 = get_password_hash(plain_password)
    print(f"get_password_hash() 结果: {hashed2}")
    print(f"验证结果: {verify_password(plain_password, hashed2)}")
    print()
    
    # 测试不同哈希值（bcrypt 每次生成不同的哈希值）
    hashed3 = hash_password(plain_password)
    print(f"第二次 hash_password() 结果: {hashed3}")
    print(f"验证结果: {verify_password(plain_password, hashed3)}")
    print(f"两次哈希值是否相同: {hashed1 == hashed3}")
    print()
    
    # 测试错误密码
    wrong_password = "wrong_password"
    print(f"错误密码验证: {verify_password(wrong_password, hashed1)}")
    print()
    
    print("=" * 50)
    print("测试完成！")
    print("=" * 50)
    print()
    print("预设账号信息：")
    print("  用户名: admin")
    print("  密码: admin123")
    print()
    print("注意：bcrypt 每次生成的哈希值都不同，但都能正确验证原始密码")

if __name__ == "__main__":
    test_password()

