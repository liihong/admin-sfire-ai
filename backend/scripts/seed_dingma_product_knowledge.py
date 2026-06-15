"""
顶妈产品知识库一次性灌库脚本

从 backend/data/dingma/product_knowledge_2026.json 幂等写入 MySQL。
按 tenant_id + product_code upsert。

执行方式：
    cd backend && python -m scripts.seed_dingma_product_knowledge
"""
import asyncio
import json
import sys
from pathlib import Path

from loguru import logger
from sqlalchemy import select

# 将 backend 根目录加入 path
_BACKEND_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_BACKEND_ROOT))

from db.session import init_db, close_db


DATA_FILE = _BACKEND_ROOT / "data" / "dingma" / "product_knowledge_2026.json"


async def resolve_dingma_tenant_id(session) -> int:
    """解析 dingma 租户 ID"""
    from models.tenant import Tenant
    from services.dingma.constants import DINGMA_TENANT_CODE

    result = await session.execute(
        select(Tenant.id).where(Tenant.code == DINGMA_TENANT_CODE)
    )
    tenant_id = result.scalar_one_or_none()
    if tenant_id is None:
        raise RuntimeError(
            f"未找到 code={DINGMA_TENANT_CODE} 的租户，请先在 tenants 表创建 dingma 租户"
        )
    return int(tenant_id)


async def seed():
    """灌库主流程"""
    from db import session as db_session
    from models.dingma_product_knowledge import DingmaProductKnowledge

    if not DATA_FILE.exists():
        raise FileNotFoundError(f"数据文件不存在: {DATA_FILE}")

    with open(DATA_FILE, "r", encoding="utf-8") as f:
        items = json.load(f)

    if not isinstance(items, list):
        raise ValueError("JSON 根节点必须是数组")

    if db_session.async_session_maker is None:
        await db_session.init_db()

    inserted = 0
    updated = 0

    async with db_session.async_session_maker() as session:
        tenant_id = await resolve_dingma_tenant_id(session)

        for idx, item in enumerate(items):
            product_code = item.get("product_code")
            if not product_code:
                logger.warning(f"跳过第 {idx} 条：缺少 product_code")
                continue

            result = await session.execute(
                select(DingmaProductKnowledge).where(
                    DingmaProductKnowledge.tenant_id == tenant_id,
                    DingmaProductKnowledge.product_code == product_code,
                )
            )
            existing = result.scalar_one_or_none()

            fields = {
                "tenant_id": tenant_id,
                "category_code": item.get("category_code", "other"),
                "category_name": item.get("category_name", "其他"),
                "product_code": product_code,
                "product_name": item.get("product_name", product_code),
                "aliases": item.get("aliases") or [],
                "pack_formula": item.get("pack_formula"),
                "recipe_detail": item.get("recipe_detail"),
                "copywriting_facts": item.get("copywriting_facts"),
                "source_version": item.get("source_version", "2026-01"),
                "status": int(item.get("status", 1)),
                "sort_order": int(item.get("sort_order", idx)),
            }

            if existing:
                for key, value in fields.items():
                    if key in ("tenant_id", "product_code"):
                        continue
                    setattr(existing, key, value)
                updated += 1
            else:
                session.add(DingmaProductKnowledge(**fields))
                inserted += 1

        await session.commit()

    logger.info(
        f"灌库完成: 新增 {inserted} 条, 更新 {updated} 条, 合计 {inserted + updated} 条"
    )


async def main():
    await init_db()
    try:
        await seed()
    finally:
        await close_db()


if __name__ == "__main__":
    asyncio.run(main())
