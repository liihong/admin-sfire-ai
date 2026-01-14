"""
测试用户密码生成工具
用于生成C端用户的MD5加密密码和bcrypt哈希密码
"""
import hashlib
import bcrypt


def md5_hash(text: str) -> str:
    """生成MD5哈希"""
    return hashlib.md5(text.encode('utf-8')).hexdigest()


def bcrypt_hash(text: str) -> str:
    """生成bcrypt哈希"""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(text.encode('utf-8'), salt)
    return hashed.decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码"""
    try:
        return bcrypt.checkpw(
            plain_password.encode('utf-8'),
            hashed_password.encode('utf-8')
        )
    except Exception:
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("测试用户密码生成工具")
    print("=" * 60)
    print()

    # 测试密码
    test_password = input("请输入测试密码 (直接回车使用默认密码 '123456'): ").strip()
    if not test_password:
        test_password = "123456"

    print(f"\n原始密码: {test_password}")
    print(f"MD5加密后 (前端传输): {md5_hash(test_password)}")
    print(f"bcrypt哈希后 (数据库存储): {bcrypt_hash(test_password)}")

    # 验证流程
    print("\n" + "=" * 60)
    print("验证流程:")
    print("=" * 60)

    # 1. 前端MD5加密
    md5_password = md5_hash(test_password)
    print(f"\n1. 前端将密码进行MD5加密: {md5_password}")

    # 2. 后端生成bcrypt哈希并存入数据库
    bcrypt_password = bcrypt_hash(test_password)
    print(f"2. 后端将原始密码进行bcrypt哈希并存入数据库")
    print(f"   数据库中的哈希值: {bcrypt_password}")

    # 3. 前端发送MD5密码到后端
    print(f"\n3. 前端将MD5加密的密码发送到后端: {md5_password}")

    # 4. 后端验证MD5密码与bcrypt哈希
    print(f"\n4. 后端验证MD5密码与数据库中的bcrypt哈希")
    is_valid = verify_password(md5_password, bcrypt_password)
    print(f"   验证结果: {'✓ 成功' if is_valid else '✗ 失败'}")

    print("\n" + "=" * 60)
    print("SQL 插入语句示例:")
    print("=" * 60)
    print(f"""
-- 插入C端测试用户 (手机号: 13800138000, 密码: {test_password})
INSERT INTO users (username, phone, password_hash, nickname, is_active, level, vip_expire_date, created_at, updated_at)
VALUES (
    'test_user_13800138000',
    '13800138000',
    '{bcrypt_password}',
    '测试用户',
    1,
    'normal',
    NULL,
    NOW(),
    NOW()
);
    """)

    print("\n注意:")
    print("- 前端传输的是MD5加密后的密码")
    print("- 后端数据库存储的是bcrypt哈希后的密码")
    print("- 后端验证时，直接将前端传来的MD5密码与数据库的bcrypt哈希进行对比")
    print("- bcrypt算法会自动处理MD5的验证")
