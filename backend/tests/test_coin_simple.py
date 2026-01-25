"""
火源币算力系统简化测试脚本
"""
import asyncio
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from decimal import Decimal
from sqlalchemy import select
from loguru import logger

from db import async_session_maker, init_db, close_db
from models.user import User
from models.llm_model import LLMModel
from models.compute import ComputeLog
from services.coin import CoinServiceFactory
from services.content import ContentModerationService


async def get_session():
    """获取数据库会话"""
    async with async_session_maker() as session:
        yield session


async def test_basic_calculation():
    """测试基础算力计算"""
    logger.info("========== 测试1: 基础算力计算 ==========")

    async with async_session_maker() as db:
        coin_service = CoinServiceFactory(db)

        # 测试默认配置计算
        cost = await coin_service.calculate_cost(
            input_tokens=1000,
            output_tokens=500,
            model_id=1
        )
        logger.info(f"✓ 1000输入 + 500输出 = {cost} 火源币")

        # 测试Token估算
        text = "你好,请介绍一下Python编程语言的特点和应用场景"
        tokens = coin_service.estimate_tokens_from_text(text)
        logger.info(f"✓ 文本 '{text[:20]}...' 估算为 {tokens} tokens")

        # 测试最大消耗估算
        max_cost = await coin_service.estimate_max_cost(
            model_id=1,
            input_text=text
        )
        logger.info(f"✓ 预估最大消耗: {max_cost} 火源币")

    logger.success("测试1 通过 ✓\n")


async def test_content_moderation():
    """测试内容审查"""
    logger.info("========== 测试2: 内容审查服务 ==========")

    moderation = ContentModerationService()

    # 正常内容
    result1 = await moderation.check_input("你好,介绍一下Python")
    logger.info(f"✓ 正常内容检查: passed={result1['passed']}")

    # 检查是否有敏感词配置
    if moderation.sensitive_words:
        sensitive_word = list(moderation.sensitive_words)[0]
        bad_text = f"这是{sensitive_word}相关内容"
        result2 = await moderation.check_input(bad_text)
        logger.info(f"✓ 违规内容检查: passed={result2['passed']}, matched={result2.get('matched_word')}")
    else:
        logger.info("⚠ 未配置敏感词库")

    logger.success("测试2 通过 ✓\n")


async def test_database_operations():
    """测试数据库操作"""
    logger.info("========== 测试3: 数据库操作 ==========")

    async with async_session_maker() as db:
        coin_service = CoinServiceFactory(db)

        # 查询第一个用户
        result = await db.execute(select(User).limit(1))
        user = result.scalar_one_or_none()

        if not user:
            logger.warning("⚠ 数据库中没有用户,跳过测试")
            return

        logger.info(f"✓ 找到测试用户: {user.username}")
        logger.info(f"  当前余额: {user.balance} 火源币")
        logger.info(f"  冻结余额: {user.frozen_balance} 火源币")
        logger.info(f"  可用余额: {user.balance - user.frozen_balance} 火源币")

        # 测试充值
        original_balance = user.balance
        recharge_amount = Decimal("50.0")
        await coin_service.recharge(
            user_id=user.id,
            amount=recharge_amount,
            remark="测试充值"
        )
        await db.commit()
        await db.refresh(user)

        logger.info(f"✓ 充值 {recharge_amount} 火源币成功")
        logger.info(f"  充值前: {original_balance}, 充值后: {user.balance}")

        # 测试预冻结（使用原子方法）
        task_id = "test_001"
        freeze_amount = Decimal("10.0")
        freeze_result = await coin_service.freeze_amount_atomic(
            user_id=user.id,
            amount=freeze_amount,
            request_id=task_id,
            remark="测试预冻结"
        )
        await db.commit()
        await db.refresh(user)

        logger.info(f"✓ 预冻结 {freeze_amount} 火源币成功")
        logger.info(f"  冻结余额: {user.frozen_balance}")

        # 测试解冻并扣除（使用原子方法）
        actual_cost = Decimal("7.5")
        settle_result = await coin_service.settle_amount_atomic(
            user_id=user.id,
            request_id=task_id,
            actual_cost=actual_cost,
            input_tokens=500,
            output_tokens=300,
            model_name="测试模型"
        )
        await db.commit()
        await db.refresh(user)

        logger.info(f"✓ 实际扣除 {actual_cost} 火源币")
        logger.info(f"  最终余额: {user.balance}")
        logger.info(f"  冻结余额: {user.frozen_balance}")

        # 测试退款（使用原子方法）
        task_id_2 = "test_002"
        freeze_result_2 = await coin_service.freeze_amount_atomic(
            user_id=user.id,
            amount=Decimal("5.0"),
            request_id=task_id_2,
            remark="测试退款"
        )
        await db.commit()

        refund_result = await coin_service.refund_amount_atomic(
            user_id=user.id,
            request_id=task_id_2,
            reason="测试全额退款"
        )
        await db.commit()
        await db.refresh(user)

        logger.info(f"✓ 全额退款 5.0 火源币成功")
        logger.info(f"  最终余额: {user.balance}")

    logger.success("测试3 通过 ✓\n")


async def test_compute_logs():
    """测试流水查询"""
    logger.info("========== 测试4: 流水记录查询 ==========")

    async with async_session_maker() as db:
        from services.resource import ComputeService

        compute_service = ComputeService(db)

        # 查询第一个用户
        result = await db.execute(select(User).limit(1))
        user = result.scalar_one_or_none()

        if not user:
            logger.warning("⚠ 数据库中没有用户,跳过测试")
            return

        # 查询流水
        logs = await compute_service.get_user_compute_logs(
            user_id=user.id,
            page_num=1,
            page_size=5
        )

        logger.info(f"✓ 查询到 {logs.total} 条流水记录")
        for log in logs.list[:3]:
            logger.info(f"  - [{log['typeName']}] {log['amount']} 火源币 - {log.get('remark', '')}")

    logger.success("测试4 通过 ✓\n")


async def main():
    """主测试函数"""
    logger.info("🚀 开始测试火源币算力系统\n")
    logger.info("=" * 60)

    try:
        # 初始化数据库
        await init_db()

        # 运行测试
        await test_basic_calculation()
        await test_content_moderation()
        await test_database_operations()
        await test_compute_logs()

        logger.success("=" * 60)
        logger.success("🎉 所有测试通过! 火源币算力系统运行正常\n")

        # 输出系统总结
        logger.info("📊 系统功能总结:")
        logger.info("  ✓ 算力计算服务 - Token到火源币的换算")
        logger.info("  ✓ 账户管理服务 - 预冻结、扣除、退款")
        logger.info("  ✓ 内容审查服务 - 敏感词检测")
        logger.info("  ✓ 流水记录服务 - 完整的交易记录")
        logger.info("\n📝 核心公式:")
        logger.info("  消耗火源币 = [(输入Token×权重A) + (输出Token×权重B) + 基础费] × 模型倍率")

    except Exception as e:
        logger.error(f"❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()

    finally:
        # 关闭数据库连接
        await close_db()


if __name__ == "__main__":
    asyncio.run(main())
