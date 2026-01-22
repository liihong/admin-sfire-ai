"""
测试聊天接口的调试脚本
用于诊断为什么只返回 conversation_id 而没有返回对话内容
"""
import asyncio
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select
from db.session import async_session_maker
from models.agent import Agent
from models.llm_model import LLMModel


async def debug_chat():
    """调试聊天流程"""
    print("=" * 60)
    print("聊天接口调试")
    print("=" * 60)

    async with async_session_maker() as db:
        # 1. 查询智能体8
        print("\n[1] 查询智能体8...")
        result = await db.execute(select(Agent).where(Agent.id == 8))
        agent = result.scalar_one_or_none()

        if not agent:
            print("❌ 智能体8不存在")
            return

        print(f"✅ 找到智能体: {agent.name}")
        print(f"   - ID: {agent.id}")
        print(f"   - model字段: {agent.model}")
        print(f"   - status: {agent.status}")
        print(f"   - system_prompt长度: {len(agent.system_prompt)}")

        # 2. 查询模型配置
        print(f"\n[2] 查询模型配置 (agent.model = '{agent.model}')...")

        # 尝试三种方式查询模型
        from sqlalchemy import and_, or_

        result = await db.execute(
            select(LLMModel).where(
                and_(
                    or_(
                        LLMModel.provider == agent.model.lower(),
                        LLMModel.model_id == agent.model,
                        LLMModel.id == int(agent.model) if agent.model.isdigit() else False
                    ),
                    LLMModel.is_enabled == True
                )
            ).order_by(LLMModel.sort_order).limit(1)
        )
        llm_model = result.scalar_one_or_none()

        if not llm_model:
            print(f"❌ 未找到启用的模型 '{agent.model}'")
            print("\n所有启用的模型:")
            result = await db.execute(select(LLMModel).where(LLMModel.is_enabled == True))
            models = result.scalars().all()
            for m in models:
                print(f"   - {m.name} (id={m.id}, provider={m.provider}, model_id={m.model_id})")
            return

        print(f"✅ 找到模型配置:")
        print(f"   - ID: {llm_model.id}")
        print(f"   - Name: {llm_model.name}")
        print(f"   - Provider: {llm_model.provider}")
        print(f"   - Model ID: {llm_model.model_id}")
        print(f"   - Base URL: {llm_model.base_url}")
        print(f"   - API Key: {'已配置' if llm_model.api_key else '❌未配置'}")
        print(f"   - Enabled: {llm_model.is_enabled}")

        # 3. 检查 API Key 格式
        if llm_model.api_key:
            key_preview = llm_model.api_key[:10] + "..." if len(llm_model.api_key) > 10 else llm_model.api_key
            print(f"   - API Key Preview: {key_preview}")

        # 4. 测试 API 调用
        print(f"\n[3] 测试调用 AI 服务...")
        try:
            from services.content import AIService

            ai_service = AIService(db)

            # 构建测试消息
            test_messages = [
                {"role": "system", "content": "你是一个测试助手"},
                {"role": "user", "content": "你好，请回复'测试成功'"}
            ]

            print(f"   - Model ID for AI: {llm_model.id}")
            print(f"   - Messages: {len(test_messages)} 条")

            # 测试流式调用
            print(f"\n   开始流式调用...")
            chunk_count = 0
            async for chunk_json in ai_service.stream_chat(
                messages=test_messages,
                model=str(llm_model.id),
                temperature=0.7,
                max_tokens=100,
            ):
                chunk_count += 1
                import json
                try:
                    chunk_data = json.loads(chunk_json)
                    if "error" in chunk_data:
                        print(f"   ❌ 收到错误: {chunk_data['error']}")
                        break
                    if "delta" in chunk_data:
                        delta = chunk_data.get("delta", {})
                        content = delta.get("content", "")
                        if content:
                            print(f"   ✅ 收到内容块 [{chunk_count}]: {content[:20]}...")
                except:
                    print(f"   📦 收到原始块: {chunk_json[:100]}...")

            if chunk_count > 0:
                print(f"\n✅ 测试成功! 共收到 {chunk_count} 个数据块")
            else:
                print(f"\n❌ 测试失败! 没有收到任何数据块")

        except Exception as e:
            print(f"❌ AI 服务调用失败:")
            print(f"   - 错误类型: {type(e).__name__}")
            print(f"   - 错误信息: {str(e)}")
            import traceback
            print(f"   - Traceback:\n{traceback.format_exc()}")


if __name__ == "__main__":
    asyncio.run(debug_chat())
