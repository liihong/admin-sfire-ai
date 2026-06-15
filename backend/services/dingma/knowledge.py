"""
顶妈产品知识库服务：模糊匹配 + Prompt 注入

文案智能体默认 copywriting 模式，仅注入 copywriting_facts。
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from typing import List, Optional, Sequence, Tuple

from loguru import logger
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from models.dingma_product_knowledge import DingmaProductKnowledge
from models.tenant import Tenant
from services.dingma.constants import (
    DEFAULT_MAX_MATCHES,
    DINGMA_TENANT_CODE,
    KNOWLEDGE_IRON_RULE,
    KnowledgeInjectMode,
)


@dataclass
class ProductMatch:
    """产品匹配结果"""

    product: DingmaProductKnowledge
    score: int
    matched_term: str


class DingmaKnowledgeService:
    """顶妈知识库：匹配与 Prompt 块组装"""

    @staticmethod
    async def resolve_tenant_id(db: AsyncSession, scoped_tenant_id: Optional[int] = None) -> int:
        """
        解析 dingma 租户 ID。
        优先使用请求头解析的 scoped_tenant_id，否则按 tenants.code=dingma 查询。
        """
        if scoped_tenant_id is not None:
            return int(scoped_tenant_id)

        result = await db.execute(
            select(Tenant.id).where(Tenant.code == DINGMA_TENANT_CODE)
        )
        tenant_id = result.scalar_one_or_none()
        if tenant_id is None:
            raise ValueError(f"未找到租户 code={DINGMA_TENANT_CODE}，请先配置 tenants 表")
        return int(tenant_id)

    @staticmethod
    async def load_active_products(
        db: AsyncSession,
        tenant_id: int,
    ) -> List[DingmaProductKnowledge]:
        """加载租户下全部启用的产品知识"""
        result = await db.execute(
            select(DingmaProductKnowledge)
            .where(
                and_(
                    DingmaProductKnowledge.tenant_id == tenant_id,
                    DingmaProductKnowledge.status == 1,
                )
            )
            .order_by(DingmaProductKnowledge.sort_order, DingmaProductKnowledge.id)
        )
        return list(result.scalars().all())

    @staticmethod
    def _normalize_aliases(raw: Optional[object]) -> List[str]:
        """解析 aliases 字段"""
        if raw is None:
            return []
        if isinstance(raw, list):
            return [str(x).strip() for x in raw if str(x).strip()]
        if isinstance(raw, str):
            try:
                parsed = json.loads(raw)
                if isinstance(parsed, list):
                    return [str(x).strip() for x in parsed if str(x).strip()]
            except json.JSONDecodeError:
                return [raw.strip()] if raw.strip() else []
        return []

    @staticmethod
    def _match_products(
        user_input: str,
        products: Sequence[DingmaProductKnowledge],
        max_matches: int = DEFAULT_MAX_MATCHES,
    ) -> List[ProductMatch]:
        """
        对用户输入做子串匹配：产品名 + 别名，取最长命中、得分最高者。
        """
        text = (user_input or "").strip()
        if not text or not products:
            return []

        candidates: List[ProductMatch] = []

        for product in products:
            terms: List[str] = [product.product_name]
            terms.extend(DingmaKnowledgeService._normalize_aliases(product.aliases))

            best_score = 0
            best_term = ""
            for term in terms:
                term = term.strip()
                if len(term) < 2:
                    continue
                if term in text:
                    # 越长越优先，品类名误匹配概率更低
                    score = len(term) * 10
                    if score > best_score:
                        best_score = score
                        best_term = term

            if best_score > 0:
                candidates.append(ProductMatch(product=product, score=best_score, matched_term=best_term))

        candidates.sort(key=lambda x: x.score, reverse=True)

        # 去重：同一 product_code 只保留一条
        seen_codes: set[str] = set()
        unique: List[ProductMatch] = []
        for item in candidates:
            if item.product.product_code in seen_codes:
                continue
            seen_codes.add(item.product.product_code)
            unique.append(item)
            if len(unique) >= max_matches:
                break

        return unique

    @staticmethod
    def _format_copywriting_block(matches: Sequence[ProductMatch]) -> str:
        """格式化文案模式产品事实块"""
        parts = [KNOWLEDGE_IRON_RULE, "", "【产品事实】"]
        for item in matches:
            facts = (item.product.copywriting_facts or "").strip()
            if facts:
                parts.append(facts)
            else:
                # 降级：仅有产品名与出货配比摘要
                name = item.product.product_name
                pack = (item.product.pack_formula or "").strip()
                parts.append(f"【{name}】\n含：{pack[:200] if pack else '见产品说明'}")
            parts.append("")
        return "\n".join(parts).strip()

    @staticmethod
    def _format_after_sales_block(matches: Sequence[ProductMatch]) -> str:
        """格式化售后模式产品事实块（预留）"""
        parts = [
            "【产品配方事实 - 可引用克重与步骤，但仍禁止编造未列出信息】",
            "",
        ]
        for item in matches:
            p = item.product
            parts.append(f"## {p.product_name}")
            if p.pack_formula:
                parts.append(f"出货配比：{p.pack_formula}")
            if p.recipe_detail:
                detail = p.recipe_detail
                if isinstance(detail, dict):
                    ingredients = detail.get("ingredients") or []
                    steps = detail.get("steps") or []
                    notes = detail.get("notes") or []
                    if ingredients:
                        ing_text = "、".join(
                            f"{i.get('name', '')}{i.get('amount', '')}"
                            for i in ingredients
                            if isinstance(i, dict)
                        )
                        parts.append(f"配料：{ing_text}")
                    if steps:
                        parts.append("步骤：" + "；".join(str(s) for s in steps[:8]))
                    if notes:
                        parts.append("注意：" + "；".join(str(n) for n in notes[:5]))
            parts.append("")
        return "\n".join(parts).strip()

    @staticmethod
    def _format_product_index(products: Sequence[DingmaProductKnowledge]) -> str:
        """未命中时注入轻量产品索引"""
        by_category: dict[str, List[str]] = {}
        for p in products:
            cat = p.category_name or "其他"
            by_category.setdefault(cat, []).append(p.product_name)

        lines = [KNOWLEDGE_IRON_RULE, "", "【可选产品索引 - 未匹配到具体产品】"]
        for cat, names in sorted(by_category.items()):
            lines.append(f"- {cat}：{'、'.join(names)}")
        lines.append("")
        lines.append("请引导用户在指令中写明具体产品名称后再生成详细文案。")
        return "\n".join(lines)

    @staticmethod
    async def resolve_prompt_block(
        db: AsyncSession,
        user_input: str,
        tenant_id: Optional[int] = None,
        scoped_tenant_id: Optional[int] = None,
        inject_mode: KnowledgeInjectMode = KnowledgeInjectMode.COPYWRITING,
        max_matches: int = DEFAULT_MAX_MATCHES,
    ) -> str:
        """
        根据用户输入解析知识块，供 dingma chat 注入 system prompt 顶部。

        Returns:
            知识块文本；无数据时返回空字符串
        """
        try:
            resolved_tenant_id = tenant_id or await DingmaKnowledgeService.resolve_tenant_id(
                db, scoped_tenant_id
            )
        except ValueError as e:
            logger.warning(f"[DingmaKnowledge] 租户解析失败: {e}")
            return ""

        products = await DingmaKnowledgeService.load_active_products(db, resolved_tenant_id)
        if not products:
            logger.warning(f"[DingmaKnowledge] 租户 {resolved_tenant_id} 无产品知识数据")
            return ""

        matches = DingmaKnowledgeService._match_products(user_input, products, max_matches)

        if matches:
            if inject_mode == KnowledgeInjectMode.AFTER_SALES:
                block = DingmaKnowledgeService._format_after_sales_block(matches)
            else:
                block = DingmaKnowledgeService._format_copywriting_block(matches)
            logger.info(
                f"[DingmaKnowledge] 命中 {len(matches)} 个产品: "
                f"{[m.product.product_name for m in matches]}, mode={inject_mode.value}"
            )
            return block

        # 未命中：注入产品索引
        logger.info("[DingmaKnowledge] 未匹配到产品，注入轻量索引")
        return DingmaKnowledgeService._format_product_index(products)

    @staticmethod
    def prepend_knowledge(base_system_prompt: str, knowledge_block: str) -> str:
        """将知识块 prepend 到 system prompt（知识块优先，不参与截断）"""
        if not knowledge_block:
            return base_system_prompt
        if base_system_prompt:
            return f"{knowledge_block}\n\n{'=' * 40}\n\n{base_system_prompt}"
        return knowledge_block
