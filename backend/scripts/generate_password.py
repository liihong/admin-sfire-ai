"""
生成测试用户密码
直接生成MD5和bcrypt哈希，无需交互
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
    except Exception as e:
        print(f"验证失败: {e}")
        return False


if __name__ == "__main__":
    # 默认测试密码
    test_password = "123456"
    test_phone = "13261276633"

    print("=" * 70)
    print("测试用户密码生成")
    print("=" * 70)
    print(f"\n原始密码: {test_password}")
    print(f"手机号: {test_phone}\n")

    # 1. 前端MD5加密
    md5_password = md5_hash(test_password)
    print(f"1. 前端MD5加密 (传输密码): {md5_password}")

    # 2. 数据库bcrypt哈希 (使用原始密码)
    bcrypt_password = bcrypt_hash(test_password)
    print(f"2. 数据库bcrypt哈希 (存储密码): {bcrypt_password}")

    # 3. 验证逻辑
    print("\n" + "=" * 70)
    print("验证流程:")
    print("=" * 70)

    # 方式1: 使用原始密码验证 (错误的方式)
    print("\n❌ 方式1 (错误): 直接验证原始密码")
    result1 = verify_password(test_password, bcrypt_password)
    print(f"   verify_password('{test_password}', bcrypt_hash) = {result1}")

    # 方式2: 使用MD5密码验证 (应该成功)
    print("\n✓ 方式2 (正确): 验证MD5加密的密码")
    result2 = verify_password(md5_password, bcrypt_password)
    print(f"   verify_password(md5('{test_password}'), bcrypt_hash) = {result2}")

    print("\n" + "=" * 70)
    print("SQL 插入语句:")
    print("=" * 70)
    print(f"""
-- 更新用户密码 (手机号: {test_phone}, 原始密码: {test_password})
UPDATE users
SET password_hash = '{bcrypt_password}',
    updated_at = NOW()
WHERE phone = '{test_phone}';

-- 或者创建新用户
INSERT INTO users (username, phone, password_hash, nickname, is_active, level, created_at, updated_at)
VALUES (
    'user_{test_phone}',
    '{test_phone}',
    '{bcrypt_password}',
    '测试用户',
    1,
    'normal',
    NOW(),
    NOW()
);
    """)

    print("\n" + "=" * 70)
    print("问题分析:")
    print("=" * 70)
    print("\n当前实现的问题:")
    print("- 前端发送MD5加密的密码:", md5_password)
    print("- 数据库存储的是原始密码的bcrypt哈希")
    print("- bcrypt无法验证MD5哈希值与原始密码的bcrypt哈希")
    print("\n解决方案:")
    print("方案1: 数据库存储MD5密码的bcrypt哈希 (推荐)")
    print("方案2: 前端直接发送原始密码 (不安全)")
    print("方案3: 使用RSA加密替代MD5 (最安全)")

    # 生成正确的bcrypt哈希 (MD5密码的bcrypt)
    print("\n" + "=" * 70)
    print("方案1实现: 存储MD5密码的bcrypt哈希")
    print("=" * 70)
    bcrypt_for_md5 = bcrypt_hash(md5_password)
    print(f"\nMD5密码: {md5_password}")
    print(f"MD5密码的bcrypt哈希: {bcrypt_for_md5}")
    result3 = verify_password(md5_password, bcrypt_for_md5)
    print(f"验证结果: {result3} ✓")

    print(f"""
-- 使用MD5密码的bcrypt哈希 (正确方案)
UPDATE users
SET password_hash = '{bcrypt_for_md5}',
    updated_at = NOW()
WHERE phone = '{test_phone}';
    """)
