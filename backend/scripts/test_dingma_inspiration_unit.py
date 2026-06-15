"""
顶妈灵感生成知识库注入单元测试（不调用 LLM）
"""
import asyncio
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from services.dingma.inspiration_generate import DingmaInspirationGenerateService


async def test_build_system_prompt_injects_knowledge():
    """system prompt 末尾 append 成分护栏，智能体技能在前"""
    db = AsyncMock()
    service = DingmaInspirationGenerateService(db)

    mock_agent = MagicMock()
    mock_agent.agent_mode = 0
    mock_agent.system_prompt = "你是口播文案助手"
    mock_agent.is_routing_enabled = 0

    knowledge_block = "【后台参考·成分护栏】\n含：朝鲜面、泡菜"

    with patch(
        "services.dingma.inspiration_generate.DingmaKnowledgeService.resolve_prompt_block",
        new_callable=AsyncMock,
        return_value=knowledge_block,
    ):
        prompt, _kb = await service._build_system_prompt(
            db_agent=mock_agent,
            agent_config_fallback=None,
            project=None,
            user_input="泡菜朝鲜面口播灵感",
            scoped_public_tenant_id=2,
        )

    assert "产品事实铁律" in prompt or "后台参考" in prompt
    assert "口播文案助手" in prompt
    assert prompt.index("口播文案助手") < prompt.index("后台参考")
    print("OK: knowledge block appended to inspiration system prompt")


if __name__ == "__main__":
    asyncio.run(test_build_system_prompt_injects_knowledge())
