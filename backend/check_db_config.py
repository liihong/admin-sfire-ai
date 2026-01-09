#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速检查数据库中的LLM模型配置
"""

import asyncio
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from db.session import init_db, close_db, async_session_maker
from sqlalchemy import select
from models.llm_model import LLMModel


async def check_models():
    """检查数据库中的模型配置"""
    print("=" * 60)
    print("  检查数据库中的LLM模型配置")
    print("=" * 60)

    # 初始化数据库连接
    try:
        await init_db()
        print("✅ 数据库连接成功\n")
    except Exception as e:
        print(f"❌ 数据库连接失败: {e}")
        import traceback
        traceback.print_exc()
        return

    try:
        async with async_session_maker() as db:
            # 查询所有模型
            result = await db.execute(select(LLMModel))
            all_models = result.scalars().all()

            if not all_models:
                print("\n❌ 数据库中没有找到任何模型配置!")
                return

            print(f"\n找到 {len(all_models)} 个模型配置:\n")

            for model in all_models:
                print(f"{'=' * 60}")
                print(f"ID: {model.id}")
                print(f"名称: {model.name}")
                print(f"模型ID: {model.model_id}")
                print(f"Provider: {model.provider}")
                print(f"Base URL: {model.base_url}")
                print(f"是否启用: {model.is_enabled}")
                print(f"排序: {model.sort_order}")
                print(f"有API Key: {'是 (' + model.api_key[:10] + '...)' if model.api_key else '❌ 否'}")
                print(f"余额: {model.balance}")
                print(f"总Token使用: {model.total_tokens_used}")
                print(f"创建时间: {model.created_at}")

                # 诊断信息
                print(f"\n🔍 诊断:")
                issues = []

                if not model.is_enabled:
                    issues.append("⚠️  模型未启用")

                if not model.api_key:
                    issues.append("❌ 未配置API Key")

                if not model.base_url:
                    issues.append("❌ 未配置Base URL")
                else:
                    # 检查Base URL格式
                    if 'api.anthropic.com' in model.base_url and model.provider != 'anthropic':
                        issues.append(f"⚠️  Base URL包含Anthropic域名但provider是{model.provider}")
                    if 'api.deepseek.com' in model.base_url and model.provider != 'deepseek':
                        issues.append(f"⚠️  Base URL包含DeepSeek域名但provider是{model.provider}")

                    # 检查是否包含完整路径
                    if '/chat/completions' in model.base_url:
                        issues.append(f"⚠️  Base URL不应包含完整路径 (/chat/completions)")

                if not model.model_id:
                    issues.append("❌ 未配置model_id")

                if issues:
                    for issue in issues:
                        print(f"  {issue}")
                else:
                    print(f"  ✅ 配置看起来正常")

                print()

            # 检查启用的模型
            print("=" * 60)
            print("启用的模型 (可用于API调用):")
            print("=" * 60)

            enabled_models = [m for m in all_models if m.is_enabled]
            if not enabled_models:
                print("❌ 没有启用的模型!")
            else:
                provider_count = {}
                for model in enabled_models:
                    provider_count[model.provider] = provider_count.get(model.provider, 0) + 1
                    print(f"\n{model.name} (ID={model.id})")
                    print(f"  Provider: {model.provider}")
                    print(f"  Model ID: {model.model_id}")
                    print(f"  Base URL: {model.base_url}")

                print(f"\n按Provider统计:")
                for provider, count in provider_count.items():
                    print(f"  {provider}: {count}个")

                # 检查provider映射
                print(f"\n🔍 Provider映射检查:")
                print(f"  deepseek -> deepseek: {'✅' if provider_count.get('deepseek', 0) > 0 else '❌ 缺失'}")
                print(f"  doubao -> doubao: {'✅' if provider_count.get('doubao', 0) > 0 else '❌ 缺失'}")
                print(f"  claude -> anthropic: {'✅' if provider_count.get('anthropic', 0) > 0 else '❌ 缺失'}")

            print("\n" + "=" * 60)
            print("检查完成")
            print("=" * 60)

            if not enabled_models:
                print("\n💡 建议:")
                print("1. 在管理后台启用至少一个模型")
                print("2. 确保启用的模型配置了API Key和Base URL")
                print("3. 确保provider字段值正确 (deepseek/doubao/anthropic)")
            else:
                print("\n💡 Base URL格式检查:")
                print("✅ 正确格式: 'http://8.217.26.94' 或 'http://8.217.26.94/api'")
                print("❌ 错误格式: 'http://8.217.26.94/api/v1/chat/completions'")
                print("\n如果Base URL格式错误,请执行:")
                print("UPDATE llm_models SET base_url = 'http://8.217.26.94' WHERE id = <模型ID>;")

    except Exception as e:
        print(f"\n❌ 查询失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # 关闭数据库连接
        await close_db()


if __name__ == "__main__":
    try:
        asyncio.run(check_models())
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
