"""
顶妈知识库 v2 Admin 单元测试（需 DB）

执行：cd backend && python -m scripts.test_dingma_knowledge_admin_unit
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


async def run_tests():
    from db import session as db_session
    from db.session import init_db, close_db
    from schemas.dingma.knowledge import SkuQueryParams, ComponentQueryParams
    from services.dingma.knowledge_admin import DingmaKnowledgeAdminService

    await init_db()
    try:
        assert db_session.async_session_maker is not None
        async with db_session.async_session_maker() as db:
            service = DingmaKnowledgeAdminService(db)

            skus, sku_total = await service.get_sku_list(SkuQueryParams(pageNum=1, pageSize=5))
            assert sku_total >= 86
            print(f"OK SKU list total={sku_total}, sample={len(skus)}")

            comps, comp_total = await service.get_component_list(
                ComponentQueryParams(pageNum=1, pageSize=5)
            )
            assert comp_total >= 15
            print(f"OK Component list total={comp_total}, sample={len(comps)}")

            categories = await service.get_sku_categories()
            print(f"OK categories count={len(categories)}")

            options = await service.list_component_options()
            assert len(options) >= 15
            print(f"OK component options count={len(options)}")

        print("All knowledge admin unit tests passed.")
    finally:
        await close_db()


if __name__ == "__main__":
    asyncio.run(run_tests())
