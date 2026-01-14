"""
调试密码验证问题
"""
import asyncio
import sys
import bcrypt
import hashlib

sys.path.insert(0, '.')

async def main():
    from db import init_db, get_db
    from sqlalchemy import text

    # 初始化数据库
    await init_db()

    # 测试数据
    test_phone = "13261276633"
    test_password = "123456"
    md5_password = hashlib.md5(test_password.encode('utf-8')).hexdigest()

    print("=" * 70)
    print("Password Debug Tool")
    print("=" * 70)
    print(f"\nPhone: {test_phone}")
    print(f"Original Password: {test_password}")
    print(f"MD5 Password: {md5_password}\n")

    # 查询数据库
    async for db in get_db():
        sql = text("""
            SELECT id, username, phone, password_hash, is_active
            FROM users
            WHERE phone = :phone
        """)
        result = await db.execute(sql, {"phone": test_phone})
        user = result.fetchone()

        if not user:
            print(f"ERROR: User with phone {test_phone} not found!")
            break

        user_id, username, phone, password_hash, is_active = user
        print(f"User found:")
        print(f"  ID: {user_id}")
        print(f"  Username: {username}")
        print(f"  Phone: {phone}")
        print(f"  Password Hash: {password_hash}")
        print(f"  Is Active: {is_active}\n")

        print("=" * 70)
        print("Verification Tests:")
        print("=" * 70)

        # 测试1: 验证原始密码 (如果是原始密码的bcrypt)
        print("\n[Test 1] Verify original password against hash:")
        try:
            result1 = bcrypt.checkpw(
                test_password.encode('utf-8'),
                password_hash.encode('utf-8')
            )
            print(f"  bcrypt.checkpw('{test_password}', hash)")
            print(f"  Result: {result1}")
        except Exception as e:
            print(f"  Error: {e}")

        # 测试2: 验证MD5密码 (如果是MD5密码的bcrypt)
        print("\n[Test 2] Verify MD5 password against hash:")
        try:
            result2 = bcrypt.checkpw(
                md5_password.encode('utf-8'),
                password_hash.encode('utf-8')
            )
            print(f"  bcrypt.checkpw('{md5_password}', hash)")
            print(f"  Result: {result2}")
        except Exception as e:
            print(f"  Error: {e}")

        # 生成正确的哈希
        print("\n" + "=" * 70)
        print("Generate Correct Hash:")
        print("=" * 70)

        correct_bcrypt = bcrypt.hashpw(md5_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        print(f"\nMD5 password: {md5_password}")
        print(f"Correct bcrypt hash: {correct_bcrypt}")

        # 验证新生成的哈希
        result3 = bcrypt.checkpw(
            md5_password.encode('utf-8'),
            correct_bcrypt.encode('utf-8')
        )
        print(f"Verification: {result3}")

        print("\n" + "=" * 70)
        print("SQL to Fix:")
        print("=" * 70)
        print(f"""
UPDATE users
SET password_hash = '{correct_bcrypt}',
    updated_at = NOW()
WHERE phone = '{test_phone}';
        """)

        break

if __name__ == "__main__":
    asyncio.run(main())
