"""
同步用户 unionid 数据修复脚本

说明：
1. unionid 只能通过微信 API 获取，需要用户重新登录小程序才能获取
2. 此脚本用于查询 unionid 为空的用户，并提供统计信息
3. 实际更新需要在用户重新登录时自动完成

使用方法：
1. 查询 unionid 为空的用户：python sync_user_unionid.py --query
2. 统计信息：python sync_user_unionid.py --stats
"""
import asyncio
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from db.session import async_session_maker
from models.user import User
from loguru import logger


async def query_users_without_unionid(limit: int = 100):
    """
    查询 unionid 为空的用户
    
    Args:
        limit: 返回的最大数量
    """
    async with async_session_maker() as db:
        query = select(User).where(
            User.unionid.is_(None),
            User.is_deleted == False
        ).limit(limit)
        
        result = await db.execute(query)
        users = result.scalars().all()
        
        return users


async def get_statistics():
    """
    获取用户统计信息
    """
    async with async_session_maker() as db:
        # 总用户数
        total_query = select(func.count(User.id)).where(User.is_deleted == False)
        total_result = await db.execute(total_query)
        total_users = total_result.scalar() or 0
        
        # 有 unionid 的用户数
        with_unionid_query = select(func.count(User.id)).where(
            User.unionid.isnot(None),
            User.is_deleted == False
        )
        with_unionid_result = await db.execute(with_unionid_query)
        with_unionid_count = with_unionid_result.scalar() or 0
        
        # 有 openid 但没有 unionid 的用户数
        openid_no_unionid_query = select(func.count(User.id)).where(
            User.openid.isnot(None),
            User.unionid.is_(None),
            User.is_deleted == False
        )
        openid_no_unionid_result = await db.execute(openid_no_unionid_query)
        openid_no_unionid_count = openid_no_unionid_result.scalar() or 0
        
        # 有手机号但没有 unionid 的用户数
        phone_no_unionid_query = select(func.count(User.id)).where(
            User.phone.isnot(None),
            User.unionid.is_(None),
            User.is_deleted == False
        )
        phone_no_unionid_result = await db.execute(phone_no_unionid_query)
        phone_no_unionid_count = phone_no_unionid_result.scalar() or 0
        
        return {
            "total_users": total_users,
            "with_unionid": with_unionid_count,
            "without_unionid": total_users - with_unionid_count,
            "openid_no_unionid": openid_no_unionid_count,
            "phone_no_unionid": phone_no_unionid_count,
        }


async def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="同步用户 unionid 数据修复脚本")
    parser.add_argument("--query", action="store_true", help="查询 unionid 为空的用户")
    parser.add_argument("--stats", action="store_true", help="显示统计信息")
    parser.add_argument("--limit", type=int, default=100, help="查询数量限制（默认100）")
    
    args = parser.parse_args()
    
    if args.stats:
        # 显示统计信息
        stats = await get_statistics()
        print("\n=== 用户 unionid 统计信息 ===")
        print(f"总用户数: {stats['total_users']}")
        print(f"有 unionid 的用户: {stats['with_unionid']}")
        print(f"没有 unionid 的用户: {stats['without_unionid']}")
        print(f"有 openid 但没有 unionid: {stats['openid_no_unionid']}")
        print(f"有手机号但没有 unionid: {stats['phone_no_unionid']}")
        print("\n说明：unionid 需要在用户重新登录小程序时自动更新")
        return
    
    if args.query:
        # 查询 unionid 为空的用户
        users = await query_users_without_unionid(limit=args.limit)
        print(f"\n=== 查询到 {len(users)} 个 unionid 为空的用户 ===")
        print(f"{'ID':<10} {'用户名':<20} {'手机号':<15} {'OpenID':<30} {'创建时间':<20}")
        print("-" * 100)
        
        for user in users:
            openid_display = user.openid[:27] + "..." if user.openid and len(user.openid) > 30 else (user.openid or "None")
            created_at = user.created_at.strftime("%Y-%m-%d %H:%M:%S") if user.created_at else "None"
            print(f"{user.id:<10} {user.username:<20} {user.phone or 'None':<15} {openid_display:<30} {created_at:<20}")
        
        print("\n说明：这些用户的 unionid 将在下次登录小程序时自动更新")
        return
    
    # 默认显示统计信息
    stats = await get_statistics()
    print("\n=== 用户 unionid 统计信息 ===")
    print(f"总用户数: {stats['total_users']}")
    print(f"有 unionid 的用户: {stats['with_unionid']}")
    print(f"没有 unionid 的用户: {stats['without_unionid']}")
    print(f"有 openid 但没有 unionid: {stats['openid_no_unionid']}")
    print(f"有手机号但没有 unionid: {stats['phone_no_unionid']}")
    print("\n使用 --query 查询详细列表，使用 --stats 查看统计信息")


if __name__ == "__main__":
    asyncio.run(main())

