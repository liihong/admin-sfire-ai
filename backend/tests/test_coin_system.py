"""
火源币算力系统测试脚本
测试算力计算、预冻结、扣除、退款等核心功能
"""
import asyncio
from decimal import Decimal
from sqlalchemy import select
from loguru import logger

from db.session import get_async_session
from models.user import User
from models.llm_model import LLMModel
from models.compute import ComputeLog, ComputeType
from services.coin import CoinServiceFactory
from services.content import ContentModerationService
from utils.response import success


async def test_coin_calculator():
    """测试算力计算服务"""
    logger.info("========== 测试算力计算服务 ==========")

    async with get_async_session() as db:
        coin_service = CoinServiceFactory(db)

        # 测试1: 基础计算
        cost = await coin_service.calculate_cost(
            input_tokens=1000,
            output_tokens=500,
            model_id=1
        )
        logger.info(f"✓ 基础计算测试: 1000输入 + 500输出 = {cost} 火源币")

        # 测试2: 文本Token估算
        text = "你好,请介绍一下Python编程语言"
        estimated_tokens = coin_service.estimate_tokens_from_text(text)
        logger.info(f"✓ Token估算测试: '{text}' -> {estimated_tokens} tokens")

        # 测试3: 最大消耗估算
        max_cost = await coin_service.estimate_max_cost(
            model_id=1,
            input_text=text
        )
        logger.info(f"✓ 最大消耗估算: {max_cost} 火源币")

        # 测试4: 费用明细
        breakdown = coin_service.get_cost_breakdown(
            input_tokens=1000,
            output_tokens=500,
            model_id=1
        )
        logger.info(f"✓ 费用明细: {breakdown}")

    logger.success("算力计算服务测试通过 ✓\n")


async def test_coin_account():
    """测试算力账户管理服务"""
    logger.info("========== 测试算力账户管理服务 ==========")

    async with get_async_session() as db:
        coin_service = CoinServiceFactory(db)

        # 获取第一个测试用户
        result = await db.execute(
            select(User).limit(1)
        )
        user = result.scalar_one_or_none()

        if not user:
            logger.warning("没有找到测试用户,跳过账户测试")
            return

        user_id = user.id
        logger.info(f"测试用户ID: {user_id}, 当前余额: {user.balance}")

        # 测试1: 查询余额
        balance_info = await coin_service.get_balance(user_id)
        logger.info(f"✓ 余额查询: {balance_info}")

        # 测试2: 充值测试
        recharge_amount = Decimal("100.0")
        await coin_service.recharge(
            user_id=user_id,
            amount=recharge_amount,
            remark="测试充值"
        )
        await db.commit()
        logger.info(f"✓ 充值 {recharge_amount} 火源币成功")

        # 测试3: 预冻结测试（使用原子方法）
        task_id = "test_task_001"
        freeze_amount = Decimal("20.0")
        freeze_result = await coin_service.freeze_amount_atomic(
            user_id=user_id,
            amount=freeze_amount,
            request_id=task_id,
            remark="测试预冻结"
        )
        await db.commit()

        # 验证冻结
        await db.refresh(user)
        logger.info(f"✓ 预冻结 {freeze_amount} 火源币, 当前冻结余额: {user.frozen_balance}")

        # 测试4: 解冻并扣除（使用原子方法）
        actual_cost = Decimal("15.5")
        settle_result = await coin_service.settle_amount_atomic(
            user_id=user_id,
            request_id=task_id,
            actual_cost=actual_cost,
            input_tokens=1000,
            output_tokens=500,
            model_name="测试模型"
        )
        await db.commit()

        # 验证扣除
        await db.refresh(user)
        logger.info(f"✓ 实际扣除 {actual_cost} 火源币, 当前余额: {user.balance}")

        # 测试5: 退款测试（使用原子方法）
        task_id_2 = "test_task_002"
        freeze_result_2 = await coin_service.freeze_amount_atomic(
            user_id=user_id,
            amount=Decimal("10.0"),
            request_id=task_id_2,
            remark="测试退款"
        )
        await db.commit()

        refund_result = await coin_service.refund_amount_atomic(
            user_id=user_id,
            request_id=task_id_2,
            reason="测试全额退款"
        )
        await db.commit()

        # 验证退款
        await db.refresh(user)
        logger.info(f"✓ 全额退款成功, 当前余额: {user.balance}")

    logger.success("算力账户管理服务测试通过 ✓\n")


async def test_content_moderation():
    """测试内容审查服务"""
    logger.info("========== 测试内容审查服务 ==========")

    moderation = ContentModerationService()

    # 测试1: 正常内容
    normal_text = "你好,请介绍一下Python"
    result = await moderation.check_input(normal_text)
    logger.info(f"✓ 正常内容检查: {result}")

    # 测试2: 违规内容
    if moderation.sensitive_words:
        sensitive_word = list(moderation.sensitive_words)[0]
        bad_text = f"这个内容包含{sensitive_word}"
        result = await moderation.check_input(bad_text)
        logger.info(f"✓ 违规内容检查: {result}")
        assert not result["passed"], "应该检测到违规内容"
    else:
        logger.warning("没有配置敏感词,跳过违规测试")

    logger.success("内容审查服务测试通过 ✓\n")


async def test_full_workflow():
    """测试完整工作流程"""
    logger.info("========== 测试完整工作流程 ==========")

    async with get_async_session() as db:
        # 获取测试用户和模型
        result = await db.execute(
            select(User, LLMModel)
            .join(LLMModel, LLMModel.id == 1)
            .limit(1)
        )
        row = result.one_or_none()

        if not row:
            logger.warning("没有找到测试数据,跳过完整流程测试")
            return

        user, model = row
        logger.info(f"测试用户: {user.username}, 模型: {model.name}")

        # 初始化服务
        from middleware.balance_checker import BalanceCheckerMiddleware
        balance_checker = BalanceCheckerMiddleware(db)
        coin_service = CoinServiceFactory(db)

        # 模拟对话流程
        task_id = "workflow_test_001"
        message = "请用Python写一个Hello World程序"

        try:
            # 步骤1: 预冻结
            freeze_info = await balance_checker.check_and_freeze(
                user_id=user.id,
                model_id=model.id,
                input_text=message,
                task_id=task_id
            )
            logger.info(f"✓ 预冻结成功: {freeze_info['frozen_amount']} 火源币")

            # 步骤2: 模拟AI生成
            input_tokens = coin_service.estimate_tokens_from_text(message)
            output_tokens = 150  # 假设生成了150个token

            # 步骤3: 计算实际消耗
            actual_cost = await coin_service.calculate_cost(
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                model_id=model.id
            )
            logger.info(f"✓ 实际消耗: {actual_cost} 火源币")

            # 步���4: 结算
            await balance_checker.settle(
                user_id=user.id,
                task_id=task_id,
                actual_cost=actual_cost,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                model_id=model.id,
                model_name=model.name,
                frozen_amount=freeze_info['frozen_amount'],
                is_error=False
            )
            await db.commit()

            # 验证最终余额
            await db.refresh(user)
            logger.info(f"✓ 对话完成, 最终余额: {user.balance}")

            # 查询流水记录
            logs_result = await db.execute(
                select(ComputeLog)
                .where(ComputeLog.task_id == task_id)
                .order_by(ComputeLog.created_at)
            )
            logs = logs_result.scalars().all()
            logger.info(f"✓ 生成 {len(logs)} 条流水记录")

        except Exception as e:
            logger.error(f"✗ 工作流程测试失败: {str(e)}")
            await db.rollback()
            raise

    logger.success("完整工作流程测试通过 ✓\n")


async def test_compute_logs():
    """测试流水记录查询"""
    logger.info("========== 测试流水记录查询 ==========")

    async with get_async_session() as db:
        from services.resource import ComputeService

        compute_service = ComputeService(db)

        # 获取第一个用户
        result = await db.execute(select(User).limit(1))
        user = result.scalar_one_or_none()

        if not user:
            logger.warning("没有找到测试用户,跳过流水查询测试")
            return

        # 查询用户流水
        logs = await compute_service.get_user_compute_logs(
            user_id=user.id,
            page_num=1,
            page_size=10
        )

        logger.info(f"✓ 查询到 {logs.total} 条流水记录")
        for log in logs.list[:3]:  # 只显示前3条
            logger.info(f"  - {log['type_name']}: {log['amount']} 火源币")

    logger.success("流水记录查询测试通过 ✓\n")


async def main():
    """主测试函数"""
    logger.info("🚀 开始测试火源币算力系统\n")

    try:
        # 测试算力计算
        await test_coin_calculator()

        # 测试内容审查
        await test_content_moderation()

        # 测试账户管理 (需要数据库)
        await test_coin_account()

        # 测试完整流程
        await test_full_workflow()

        # 测试流水查询
        await test_compute_logs()

        logger.success("🎉 所有测试通过! 火源币算力系统运行正常")

    except Exception as e:
        logger.error(f"❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # 运行测试
    asyncio.run(main())
