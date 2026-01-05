"""
数据库连接检查脚本
用于验证数据库配置是否正确
"""
import asyncio
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from loguru import logger
from sqlalchemy import select
from db.session import init_db, async_session_maker, close_db
from models.user import User
from models.menu import Menu
from models.compute import ComputeLog
from core.config import settings


async def check_database():
    """检查数据库连接和表结构"""
    print("=" * 60)
    print("数据库配置检查")
    print("=" * 60)
    
    # 显示配置信息
    print(f"\n数据库配置:")
    print(f"  Host: {settings.MYSQL_HOST}")
    print(f"  Port: {settings.MYSQL_PORT}")
    print(f"  User: {settings.MYSQL_USER}")
    print(f"  Password: {'***' if settings.MYSQL_PASSWORD else '(empty)'}")
    print(f"  Database: {settings.MYSQL_DATABASE}")
    print(f"  Connection URL: {settings.MYSQL_DATABASE_URL.replace(settings.MYSQL_PASSWORD, '***')}")
    
    try:
        # 初始化数据库连接
        print(f"\n正在连接数据库...")
        await init_db()
        print("[SUCCESS] 数据库连接成功!")
        
        # 检查表是否存在
        async with async_session_maker() as db:
            print(f"\n检查数据库表...")
            
            # 检查 users 表
            try:
                result = await db.execute(select(User).limit(1))
                users = result.scalars().all()
                user_count = len(users)
                # 尝试获取总数
                try:
                    from sqlalchemy import func
                    count_result = await db.execute(select(func.count(User.id)))
                    user_count = count_result.scalar() or 0
                except:
                    pass
                print(f"  [OK] users 表存在，记录数: {user_count}")
            except Exception as e:
                print(f"  [ERROR] users 表不存在或错误: {e}")
            
            # 检查 menus 表
            try:
                result = await db.execute(select(Menu).limit(1))
                menus = result.scalars().all()
                menu_count = len(menus)
                try:
                    from sqlalchemy import func
                    count_result = await db.execute(select(func.count(Menu.id)))
                    menu_count = count_result.scalar() or 0
                except:
                    pass
                print(f"  [OK] menus 表存在，记录数: {menu_count}")
            except Exception as e:
                print(f"  [ERROR] menus 表不存在或错误: {e}")
            
            # 检查 compute_logs 表
            try:
                result = await db.execute(select(ComputeLog).limit(1))
                logs = result.scalars().all()
                log_count = len(logs)
                try:
                    from sqlalchemy import func
                    count_result = await db.execute(select(func.count(ComputeLog.id)))
                    log_count = count_result.scalar() or 0
                except:
                    pass
                print(f"  [OK] compute_logs 表存在，记录数: {log_count}")
            except Exception as e:
                print(f"  [ERROR] compute_logs 表不存在或错误: {e}")
            
            # 检查管理员用户
            print(f"\n检查管理员用户...")
            try:
                result = await db.execute(
                    select(User).where(User.username == "admin")
                )
                admin_user = result.scalar_one_or_none()
                if admin_user:
                    print(f"  [OK] 管理员用户存在: admin")
                    print(f"     状态: {'激活' if admin_user.is_active else '禁用'}")
                    print(f"     等级: {admin_user.level.value}")
                else:
                    print(f"  [WARNING] 管理员用户不存在，请运行初始化脚本")
            except Exception as e:
                print(f"  [ERROR] 检查管理员用户失败: {e}")
        
        print(f"\n{'=' * 60}")
        print("[SUCCESS] 数据库检查完成!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n[ERROR] 数据库连接失败!")
        print(f"错误信息: {e}")
        print(f"\n请检查:")
        print(f"  1. MySQL 服务是否运行")
        print(f"  2. 数据库配置是否正确（.env 文件）")
        print(f"  3. 用户是否有访问权限")
        print(f"  4. 网络连接是否正常")
        return False
    
    finally:
        await close_db()
    
    return True


if __name__ == "__main__":
    success = asyncio.run(check_database())
    sys.exit(0 if success else 1)

