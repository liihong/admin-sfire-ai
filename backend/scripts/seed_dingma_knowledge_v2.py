"""
顶妈知识库 v2 灌库脚本

从 backend/data/dingma/knowledge_v2.json 幂等写入 MySQL。

执行：
    cd backend && python -m scripts.seed_dingma_knowledge_v2
"""
import asyncio
import json
import sys
from pathlib import Path

from loguru import logger
from sqlalchemy import select

_BACKEND_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_BACKEND_ROOT))

from db.session import init_db, close_db

DATA_FILE = _BACKEND_ROOT / "data" / "dingma" / "knowledge_v2.json"


async def resolve_dingma_tenant_id(session) -> int:
    from models.tenant import Tenant
    from services.dingma.constants import DINGMA_TENANT_CODE

    result = await session.execute(select(Tenant.id).where(Tenant.code == DINGMA_TENANT_CODE))
    tenant_id = result.scalar_one_or_none()
    if tenant_id is None:
        raise RuntimeError(f"未找到 code={DINGMA_TENANT_CODE} 的租户")
    return int(tenant_id)


async def seed():
    from db import session as db_session
    from models.dingma_knowledge import (
        DingmaKnowledgeComponent,
        DingmaKnowledgeSku,
        DingmaSkuComponentLink,
    )

    if not DATA_FILE.exists():
        raise FileNotFoundError(f"数据文件不存在: {DATA_FILE}，请先运行 transform_legacy_knowledge")

    with open(DATA_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    if db_session.async_session_maker is None:
        await db_session.init_db()

    comp_inserted = comp_updated = 0
    sku_inserted = sku_updated = 0
    link_inserted = link_updated = 0

    async with db_session.async_session_maker() as session:
        tenant_id = await resolve_dingma_tenant_id(session)

        # 1. 组件 upsert
        component_id_map: dict[str, int] = {}
        for item in data.get("components") or []:
            code = item.get("component_code")
            if not code:
                continue

            result = await session.execute(
                select(DingmaKnowledgeComponent).where(
                    DingmaKnowledgeComponent.tenant_id == tenant_id,
                    DingmaKnowledgeComponent.component_code == code,
                )
            )
            existing = result.scalar_one_or_none()
            fields = {
                "tenant_id": tenant_id,
                "component_code": code,
                "component_name": item.get("component_name", code),
                "component_type": item.get("component_type", "sauce"),
                "aliases": item.get("aliases") or [],
                "pack_formula": item.get("pack_formula"),
                "recipe_detail": item.get("recipe_detail"),
                "guardrail": item.get("guardrail"),
                "process_copywriting": item.get("process_copywriting"),
                "source_version": item.get("source_version", "2026-01"),
                "status": int(item.get("status", 1)),
                "sort_order": int(item.get("sort_order", 0)),
            }
            if existing:
                for k, v in fields.items():
                    if k in ("tenant_id", "component_code"):
                        continue
                    setattr(existing, k, v)
                component_id_map[code] = existing.id
                comp_updated += 1
            else:
                row = DingmaKnowledgeComponent(**fields)
                session.add(row)
                await session.flush()
                component_id_map[code] = row.id
                comp_inserted += 1

        # 2. SKU upsert
        sku_id_map: dict[str, int] = {}
        for item in data.get("skus") or []:
            code = item.get("sku_code")
            if not code:
                continue

            result = await session.execute(
                select(DingmaKnowledgeSku).where(
                    DingmaKnowledgeSku.tenant_id == tenant_id,
                    DingmaKnowledgeSku.sku_code == code,
                )
            )
            existing = result.scalar_one_or_none()
            fields = {
                "tenant_id": tenant_id,
                "sku_code": code,
                "sku_name": item.get("sku_name", code),
                "category_code": item.get("category_code", "other"),
                "category_name": item.get("category_name", "其他"),
                "aliases": item.get("aliases") or [],
                "pack_formula": item.get("pack_formula"),
                "guardrail": item.get("guardrail"),
                "process_copywriting": item.get("process_copywriting"),
                "source_version": item.get("source_version", "2026-01"),
                "status": int(item.get("status", 1)),
                "sort_order": int(item.get("sort_order", 0)),
            }
            if existing:
                for k, v in fields.items():
                    if k in ("tenant_id", "sku_code"):
                        continue
                    setattr(existing, k, v)
                sku_id_map[code] = existing.id
                sku_updated += 1
            else:
                row = DingmaKnowledgeSku(**fields)
                session.add(row)
                await session.flush()
                sku_id_map[code] = row.id
                sku_inserted += 1

        await session.flush()

        # 3. 关联 upsert（先删旧关联再重建，保证与 JSON 一致）
        for link in data.get("sku_component_links") or []:
            sku_code = link.get("sku_code")
            comp_code = link.get("component_code")
            sku_id = sku_id_map.get(sku_code)
            comp_id = component_id_map.get(comp_code)
            if not sku_id or not comp_id:
                logger.warning(f"跳过无效关联: {sku_code} -> {comp_code}")
                continue

            result = await session.execute(
                select(DingmaSkuComponentLink).where(
                    DingmaSkuComponentLink.sku_id == sku_id,
                    DingmaSkuComponentLink.component_id == comp_id,
                )
            )
            existing = result.scalar_one_or_none()
            fields = {
                "sku_id": sku_id,
                "component_id": comp_id,
                "role": link.get("role", "other"),
                "process_focus": bool(link.get("process_focus", False)),
                "display_label": link.get("display_label"),
                "sort_order": int(link.get("sort_order", 0)),
            }
            if existing:
                for k, v in fields.items():
                    setattr(existing, k, v)
                link_updated += 1
            else:
                session.add(DingmaSkuComponentLink(**fields))
                link_inserted += 1

        await session.commit()

    logger.info(
        f"灌库完成: components +{comp_inserted}/~{comp_updated}, "
        f"skus +{sku_inserted}/~{sku_updated}, links +{link_inserted}/~{link_updated}"
    )


async def main():
    await init_db()
    try:
        await seed()
    finally:
        await close_db()


if __name__ == "__main__":
    asyncio.run(main())
