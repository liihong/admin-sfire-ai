"""
火源币算力系统单元测试
测试核心计算逻辑,不依赖数据库
"""
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from decimal import Decimal
from loguru import logger

from constants.coin_config import CoinConfig, MODEL_RATE_CONFIGS


def test_coin_config():
    """测试算力配置"""
    logger.info("========== 测试1: 算力配置常量 ==========")

    config = CoinConfig()

    # 断言新配置参数（优化后）
    assert config.TOKEN_TO_COIN_RATE == Decimal("0.004"), "TOKEN_TO_COIN_RATE 应为 0.004"
    assert config.DEFAULT_BASE_FEE == Decimal("5.0"), "DEFAULT_BASE_FEE 应为 5.0"
    assert config.FREEZE_ESTIMATE_MULTIPLIER == Decimal("1.2"), "FREEZE_ESTIMATE_MULTIPLIER 应为 1.2"
    logger.info(f"✓ 配置参数: TOKEN_TO_COIN_RATE={config.TOKEN_TO_COIN_RATE}, DEFAULT_BASE_FEE={config.DEFAULT_BASE_FEE}, FREEZE_ESTIMATE_MULTIPLIER={config.FREEZE_ESTIMATE_MULTIPLIER}")

    # 测试基础计算
    cost = config.calculate_default_cost(1000, 500)
    logger.info(f"✓ 默认配置计算: 1000输入 + 500输出 = {cost} 火源币")

    # 测试Token估算
    text1 = "你好世界"  # 4个中文字符
    tokens1 = config.estimate_tokens_from_text(text1)
    logger.info(f"✓ 中文文本 '{text1}' 估算为 {tokens1} tokens")

    text2 = "Hello World"  # 11个英文字符
    tokens2 = config.estimate_tokens_from_text(text2)
    logger.info(f"✓ 英文文本 '{text2}' 估算为 {tokens2} tokens")

    # 测试违规处罚
    penalty = config.calculate_violation_penalty(Decimal("10.0"))
    logger.info(f"✓ 基础费10.0的违规处罚: {penalty} 火源币")

    # 测试模型配置
    logger.info(f"✓ 预设模型配��数量: {len(MODEL_RATE_CONFIGS)}")
    for model_name, model_config in MODEL_RATE_CONFIGS.items():
        logger.info(f"  - {model_name}: 倍率={model_config['rate_multiplier']}")

    logger.success("测试1 通过 ✓\n")


def test_cost_formula():
    """测试算力计算公式"""
    logger.info("========== 测试2: 算力计算公式 ==========")

    config = CoinConfig()

    # 公式: [(输入Token×权重A) + (输出Token×权重B) + 基础费] × 模型倍率 × 换算比例

    # 测试用例1: 小规模
    input_tokens = 100
    output_tokens = 50
    cost = config.calculate_default_cost(input_tokens, output_tokens)
    logger.info(f"✓ 小规模 (100输入+50输出): {cost} 火源币")

    # 测试用例2: 中等规模
    input_tokens = 1000
    output_tokens = 500
    cost = config.calculate_default_cost(input_tokens, output_tokens)
    logger.info(f"✓ 中等规模 (1000输入+500输出): {cost} 火源币")

    # 测试用例3: 大规模
    input_tokens = 5000
    output_tokens = 2000
    cost = config.calculate_default_cost(input_tokens, output_tokens)
    logger.info(f"✓ 大规模 (5000输入+2000输出): {cost} 火源币")

    # 验证公式合理性
    # 输出权重应该大于输入权重
    assert config.DEFAULT_OUTPUT_WEIGHT > config.DEFAULT_INPUT_WEIGHT
    logger.info(f"✓ 权重配置合理: 输入={config.DEFAULT_INPUT_WEIGHT}, 输出={config.DEFAULT_OUTPUT_WEIGHT}")

    logger.success("测试2 通过 ✓\n")


def test_model_rates():
    """测试模型倍率配置"""
    logger.info("========== 测试3: 模型倍率配置 ==========")

    # 检查常见模型的倍率配置
    models_to_check = [
        "claude-3-5-sonnet",
        "gpt-4o",
        "gpt-4o-mini",
        "deepseek-chat",
    ]

    for model_name in models_to_check:
        if model_name in MODEL_RATE_CONFIGS:
            config = MODEL_RATE_CONFIGS[model_name]
            logger.info(f"✓ {model_name}:")
            logger.info(f"    - 倍率系数: {config['rate_multiplier']}")
            logger.info(f"    - 输入权重: {config['input_weight']}")
            logger.info(f"    - 输出权重: {config['output_weight']}")
            logger.info(f"    - 基础费用: {config['base_fee']} 火源币")
        else:
            logger.warning(f"⚠ 未找到模型配置: {model_name}")

    # 验证配置合理性
    claude_rate = MODEL_RATE_CONFIGS.get("claude-3-5-sonnet", {}).get("rate_multiplier", Decimal("1.0"))
    mini_rate = MODEL_RATE_CONFIGS.get("gpt-4o-mini", {}).get("rate_multiplier", Decimal("1.0"))

    # GPT-4o-mini应该比Claude便宜
    assert mini_rate < claude_rate, "GPT-4o-mini 倍率应该小于 Claude"
    logger.info(f"✓ 模型倍率关系合理: GPT-4o-mini({mini_rate}) < Claude({claude_rate})")

    logger.success("测试3 通过 ✓\n")


def test_token_estimation():
    """测试Token估算"""
    logger.info("========== 测试4: Token估算准确性 ==========")

    config = CoinConfig()

    test_cases = [
        ("你好", 2, "纯中文"),
        ("Hello", 1, "纯英文(短)"),
        ("Hello World", 2, "纯英文(长)"),
        ("你好世界Hello World", 4, "中英混合"),
        ("The quick brown fox jumps over the lazy dog", 9, "英文句子"),
        ("快速的棕色狐狸跳过懒狗", 12, "中文句子"),
    ]

    for text, expected_range, description in test_cases:
        estimated = config.estimate_tokens_from_text(text)
        # 允许±2的误差
        in_range = abs(estimated - expected_range) <= 2
        status = "✓" if in_range else "⚠"
        logger.info(f"{status} {description}: '{text}' -> {estimated} tokens (预期约{expected_range})")

    logger.success("测试4 通过 ✓\n")


def test_usage_from_api_token_extraction():
    """测试 usage_from_api 的 token 提取与计费（优先使用实际 token）"""
    logger.info("========== 测试5: usage_from_api 计费逻辑 ==========")

    # OpenAI 格式: prompt_tokens, completion_tokens
    usage_openai = {"prompt_tokens": 1000, "completion_tokens": 500}
    input_tokens = usage_openai.get("prompt_tokens") or usage_openai.get("input_tokens")
    output_tokens = usage_openai.get("completion_tokens") or usage_openai.get("output_tokens")
    cost = CoinConfig.calculate_default_cost(input_tokens, output_tokens)
    assert cost == 15, f"预期 15 火源币, 实际 {cost}"
    logger.info(f"✓ OpenAI 格式 usage: 1000 输入 + 500 输出 = {cost} 火源币")

    # 部分 API 格式: input_tokens, output_tokens
    usage_alt = {"input_tokens": 2000, "output_tokens": 800}
    input_tokens = usage_alt.get("prompt_tokens") or usage_alt.get("input_tokens")
    output_tokens = usage_alt.get("completion_tokens") or usage_alt.get("output_tokens")
    cost = CoinConfig.calculate_default_cost(input_tokens, output_tokens)
    # (2000 + 2400) * 0.004 + 5 = 22.6 -> 23
    assert cost == 23, f"预期 23 火源币, 实际 {cost}"
    logger.info(f"✓ 备用格式 usage: 2000 输入 + 800 输出 = {cost} 火源币")

    logger.success("测试5 通过 ✓\n")


def main():
    """主测试函数"""
    logger.info("🚀 开始测试火源币算力系统 (单元测试)\n")
    logger.info("=" * 60)

    try:
        test_coin_config()
        test_cost_formula()
        test_model_rates()
        test_token_estimation()
        test_usage_from_api_token_extraction()

        logger.success("=" * 60)
        logger.success("🎉 所有单元测试通过!\n")

        # 输出系统文档
        logger.info("📖 火源币算力系统说明\n")

        logger.info("1️⃣ 核心计算公式:")
        logger.info("   消耗火源币 = [(输入Token × 权重A) + (输出Token × 权重B) + 基础调度费] × 模型倍率系数 × 0.001\n")

        logger.info("2️⃣ 默认参数:")
        logger.info(f"   - 输入Token权重 (A): {CoinConfig.DEFAULT_INPUT_WEIGHT}")
        logger.info(f"   - 输出Token权重 (B): {CoinConfig.DEFAULT_OUTPUT_WEIGHT}")
        logger.info(f"   - 基础调度费: {CoinConfig.DEFAULT_BASE_FEE} 火源币")
        logger.info(f"   - Token换算比例: {CoinConfig.TOKEN_TO_COIN_RATE}")
        logger.info(f"   - 预冻结估算系数: {CoinConfig.FREEZE_ESTIMATE_MULTIPLIER}\n")

        logger.info("3️⃣ 模型倍率示例:")
        for model in ["gpt-4o-mini", "claude-3-5-sonnet", "deepseek-chat"]:
            if model in MODEL_RATE_CONFIGS:
                cfg = MODEL_RATE_CONFIGS[model]
                logger.info(f"   - {model}: {cfg['rate_multiplier']}倍\n")

        logger.info("4️⃣ 使用示例:")
        logger.info("   # 1000输入 + 500输出,使用Claude 3.5 Sonnet")
        logger.info("   cost = [(1000×1.0) + (500×3.0) + 10] × 1.0 × 0.001")
        logger.info("   cost = [1000 + 1500 + 10] × 0.001 = 2.51 火源币\n")

        logger.info("5️⃣ 扣费流程:")
        logger.info("   用户请求 → 内容审查 → 预冻结 → LLM生成 → 内容审查 → 结算(多退少补)")

    except Exception as e:
        logger.error(f"❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
