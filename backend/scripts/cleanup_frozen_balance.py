"""
清理用户未释放的冻结余额

用于清理异常情况下的冻结记录，恢复用户的可用余额
"""
import asyncio
import sys
from decimal import Decimal
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select, update
from core.config import settings
from db.session import init_db
from models.user import User
from models.compute_freeze import ComputeFreezeLog, FreezeStatus


async def cleanup_user_frozen_balance(user_id: int, dry_run: bool = True):
    """
    清理指定用户的冻结余额

    Args:
        user_id: 用户ID
        dry_run: 是否只模拟不执行（True=只显示，False=实际执行）
    """
    # 初始化数据库连接
    await init_db()

    # 导入 async_session_maker（初始化后才能使用）
    from db.session import async_session_maker

    async with async_session_maker() as db:
        # 1. 查询用户当前余额状态
        user_result = await db.execute(
            select(User.balance, User.frozen_balance, User.version)
            .where(User.id == user_id)
        )
        user_info = user_result.first()

        if not user_info:
            print(f"❌ 用户 {user_id} 不存在")
            return

        balance, frozen, version = user_info
        available = balance - frozen

        print("=" * 80)
        print(f"[Balance] User {user_id} balance status:")
        print(f"  Total balance:       {float(balance):.2f} coins")
        print(f"  Frozen balance:      {float(frozen):.2f} coins")
        print(f"  Available balance:   {float(available):.2f} coins")
        print("=" * 80)

        # 2. 查询未释放的冻结记录
        result = await db.execute(
            select(ComputeFreezeLog)
            .where(ComputeFreezeLog.user_id == user_id)
            .where(ComputeFreezeLog.status == FreezeStatus.FROZEN.value)
            .order_by(ComputeFreezeLog.created_at.desc())
        )
        frozen_logs = result.scalars().all()

        if not frozen_logs:
            print("[OK] No unreleased freeze records found")
            return

        print(f"\n[Found] {len(frozen_logs)} unreleased freeze records:")
        print(f"{'ID':<8} {'Amount':<12} {'ModelID':<8} {'ConvID':<10} {'Created Time':<20} {'request_id'}")
        print("-" * 120)

        total_frozen = Decimal('0')
        for log in frozen_logs:
            total_frozen += log.amount
            created_str = log.created_at.strftime('%Y-%m-%d %H:%M:%S') if log.created_at else 'N/A'
            model_id = log.model_id or 0
            conversation_id = log.conversation_id or 0
            request_id_preview = (log.request_id[:30] + '...') if log.request_id else 'N/A'
            print(f"{log.id:<8} {float(log.amount):<12.2f} {model_id:<8} {conversation_id:<10} {created_str:<20} {request_id_preview}")

        print("-" * 120)
        print(f"[Total] Frozen amount: {float(total_frozen):.2f} coins")

        # 验证冻结金额是否匹配
        if abs(total_frozen - frozen) > 0.01:
            print(f"\n[WARNING] Freeze records total ({float(total_frozen):.2f}) does not match user frozen_balance ({float(frozen):.2f})!")
            print(f"   Difference: {float(abs(total_frozen - frozen)):.2f} coins")

        # 3. 执行清理
        if dry_run:
            print("\n" + "=" * 80)
            print("[Dry Run] Operations to be executed:")
            print(f"  1. Change status of {len(frozen_logs)} freeze records to REFUNDED")
            print(f"  2. Subtract {float(total_frozen):.2f} from user's frozen_balance")
            print(f"  3. User's available balance will restore to: {float(available + total_frozen):.2f}")
            print(f"\n[Tip] To execute, run: python scripts/cleanup_frozen_balance.py {user_id} --execute")
            print("=" * 80)
        else:
            print("\n" + "=" * 80)
            print("[Execute] Starting to cleanup freeze records...")

            try:
                # 使用 CAS 乐观锁更新用户余额
                update_result = await db.execute(
                    update(User)
                    .where(
                        User.id == user_id,
                        User.version == version  # CAS 版本号
                    )
                    .values(
                        frozen_balance=User.frozen_balance - total_frozen,
                        version=User.version + 1
                    )
                )

                if update_result.rowcount == 0:
                    print("[ERROR] CAS update failed: version conflict or user modified")
                    print("   Please rerun this script")
                    return

                # 批量更新冻结记录状态
                from datetime import datetime
                for log in frozen_logs:
                    log.status = FreezeStatus.REFUNDED.value
                    log.refunded_at = datetime.now()
                    log.remark = "System batch cleanup abnormal freeze records"

                await db.commit()

                print(f"[SUCCESS] Cleanup completed!")
                print(f"  - Released freeze records: {len(frozen_logs)}")
                print(f"  - Released amount: {float(total_frozen):.2f} coins")
                print(f"  - User available balance: {float(available):.2f} -> {float(available + total_frozen):.2f}")
                print("=" * 80)

            except Exception as e:
                await db.rollback()
                print(f"[ERROR] Cleanup failed: {e}")
                import traceback
                traceback.print_exc()


async def main():
    import argparse

    parser = argparse.ArgumentParser(description="清理用户未释放的冻结余额")
    parser.add_argument("user_id", type=int, help="用户ID")
    parser.add_argument("--execute", action="store_true", help="实际执行清理（默认为模拟模式）")

    args = parser.parse_args()

    await cleanup_user_frozen_balance(args.user_id, dry_run=not args.execute)


if __name__ == "__main__":
    asyncio.run(main())
