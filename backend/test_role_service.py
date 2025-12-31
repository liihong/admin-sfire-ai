"""测试RoleService"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from app.db.session import init_db, async_session_maker, close_db
from app.services.role import RoleService


async def test():
    try:
        await init_db()
        async with async_session_maker() as db:
            service = RoleService(db)
            roles = await service.get_roles()
            print(f"Found {len(roles)} roles")
            for role in roles:
                print(f"  - {role['name']} ({role['code']}): {role['user_count']} users")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await close_db()


if __name__ == "__main__":
    asyncio.run(test())

