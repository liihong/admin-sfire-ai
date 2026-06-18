"""
验证鸡丁米线过程场景注入（需 DB）

执行：cd backend && python -m scripts.verify_jiding_process_injection
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


async def main():
    from db import session as db_session
    from db.session import init_db, close_db
    from services.dingma.knowledge import DingmaKnowledgeService, CopywritingScene

    await init_db()
    try:
        async with db_session.async_session_maker() as db:
            user_input = "今天在家炒鸡丁米线的酱料，给我2个朋友圈文案"
            scene = DingmaKnowledgeService.detect_scene(user_input)
            block = await DingmaKnowledgeService.resolve_prompt_block(db=db, user_input=user_input)

            assert scene == CopywritingScene.PROCESS, f"scene={scene}"
            assert "传统鸡丁肉" in block, "应注入过程焦点组件"
            assert "鸡胸肉" in block or "香菇" in block or "豆瓣酱" in block
            assert "辣椒面" in block, "应包含过程禁写项"
            assert "勿写辣油" in block or "勿写" in block

            print("OK 过程场景检测:", scene.value)
            print("--- 注入块预览 ---")
            print(block[:1200])
    finally:
        await close_db()


if __name__ == "__main__":
    asyncio.run(main())
