"""
顶妈产品知识库后台管理单元测试（不依赖 HTTP）

执行：cd backend && python -m scripts.test_dingma_product_knowledge_admin_unit
"""
import asyncio
import sys
from pathlib import Path

_BACKEND_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_BACKEND_ROOT))

from db.session import init_db, close_db


async def run_tests():
    from db import session as db_session
    from schemas.dingma.product_knowledge import (
        ProductKnowledgeCreate,
        ProductKnowledgeQueryParams,
        ProductKnowledgeUpdate,
    )
    from services.dingma.product_knowledge_admin import DingmaProductKnowledgeAdminService

    if db_session.async_session_maker is None:
        await db_session.init_db()

    test_code = "unit_test_admin_product"
    created_id = None

    async with db_session.async_session_maker() as db:
        service = DingmaProductKnowledgeAdminService(db)

        # 清理历史测试数据
        try:
            items, _ = await service.get_list(
                ProductKnowledgeQueryParams(pageNum=1, pageSize=10, product_code=test_code)
            )
            for item in items:
                await service.delete_item(item["id"])
            await db.commit()
        except Exception:
            await db.rollback()

        # 创建
        created = await service.create_item(
            ProductKnowledgeCreate(
                category_code="test",
                category_name="测试品类",
                product_code=test_code,
                product_name="单元测试产品",
                aliases=["单测产品"],
                pack_formula="测试配比",
                recipe_detail={"steps": ["步骤1"]},
                copywriting_facts="含：测试\n不含：无",
                source_version="2026-01",
            )
        )
        created_id = created["id"]
        assert created["product_code"] == test_code
        print(f"[OK] 创建成功 id={created_id}")

        # 列表
        items, total = await service.get_list(
            ProductKnowledgeQueryParams(pageNum=1, pageSize=5, keyword="单元测试")
        )
        assert total >= 1
        print(f"[OK] 列表查询 total={total}")

        # 品类
        categories = await service.get_categories()
        assert isinstance(categories, list)
        print(f"[OK] 品类数量={len(categories)}")

        # 更新
        updated = await service.update_item(
            created_id,
            ProductKnowledgeUpdate(product_name="单元测试产品-已更新"),
        )
        assert updated["product_name"] == "单元测试产品-已更新"
        print("[OK] 更新成功")

        # 禁用
        disabled = await service.update_status(created_id, 0)
        assert disabled["status"] == 0
        print("[OK] 禁用成功")

        # 删除
        await service.delete_item(created_id)
        print("[OK] 删除成功")

        await db.commit()

    print("全部单元测试通过")


async def main():
    await init_db()
    try:
        await run_tests()
    finally:
        await close_db()


if __name__ == "__main__":
    asyncio.run(main())
