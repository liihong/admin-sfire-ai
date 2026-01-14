"""
修复用户密码
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
    print("Fix Password")
    print("=" * 70)
    print(f"\nPhone: {test_phone}")
    print(f"Original Password: {test_password}")
    print(f"MD5 Password: {md5_password}\n")

    # 生成正确的MD5密码的bcrypt哈希
    correct_bcrypt = bcrypt.hashpw(md5_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    print(f"New bcrypt hash: {correct_bcrypt}\n")

    # 更新数据库
    async for db in get_db():
        # 更新密码
        update_sql = text("""
            UPDATE users
            SET password_hash = :hash,
                updated_at = NOW()
            WHERE phone = :phone
        """)
        result = await db.execute(update_sql, {
            "hash": correct_bcrypt,
            "phone": test_phone
        })
        await db.commit()

        print(f"Updated {result.rowcount} user(s)\n")

        # 验证更新
        check_sql = text("""
            SELECT id, username, phone, password_hash, is_active
            FROM users
            WHERE phone = :phone
        """)
        result = await db.execute(check_sql, {"phone": test_phone})
        user = result.fetchone()

        if user:
            user_id, username, phone, password_hash, is_active = user
            print("Verification:")
            print(f"  ID: {user_id}")
            print(f"  Username: {username}")
            print(f"  Phone: {phone}")
            print(f"  Password Hash: {password_hash}")
            print(f"  Is Active: {is_active}\n")

            # 验证密码
            verify_result = bcrypt.checkpw(
                md5_password.encode('utf-8'),
                password_hash.encode('utf-8')
            )
            print(f"Password verification: {verify_result} {'✓' if verify_result else '✗'}")

        print("\n" + "=" * 70)
        print("Now you can test login with:")
        print(f"  Phone: {test_phone}")
        print(f"  Password: {test_password}")
        print("=" * 70)

        break

if __name__ == "__main__":
    asyncio.run(main())
