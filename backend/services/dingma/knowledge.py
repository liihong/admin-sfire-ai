"""
顶妈产品知识库 v2：场景化匹配 + Prompt 注入

- 成品 SKU：一般场景注入 guardrail（含/不含/禁）
- 制作过程场景：注入 process_focus 组件的过程文案 + 禁写提示
- 组件直匹配：用户直接说「熬辣油」时注入组件过程文案
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Sequence

from loguru import logger
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from models.dingma_knowledge import (
    DingmaKnowledgeComponent,
    DingmaKnowledgeSku,
    DingmaSkuComponentLink,
)
from models.tenant import Tenant
from services.dingma.constants import (
    DEFAULT_MAX_MATCHES,
    DINGMA_TENANT_CODE,
    KNOWLEDGE_APPENDIX_HEADER,
    KNOWLEDGE_GUARDRAIL_LINE,
    KNOWLEDGE_SCENE_HINT,
    MAX_MERGED_CONTAINS_ITEMS,
    KnowledgeInjectMode,
)


class CopywritingScene(str, Enum):
    GENERAL = "general"
    PROCESS = "process"


# 制作过程场景触发词
PROCESS_SCENE_KEYWORDS = [
    "炒", "熬", "做", "备", "调", "制作", "和馅", "包", "擀", "揉", "腌", "晒过程",
    "酱料", "料头", "制作过程", "今天在家", "备料", "出货前", "现做", "现炒", "现熬",
]

DEFAULT_CATEGORY_MAX_MATCHES = 12


@dataclass
class SkuMatch:
    sku: DingmaKnowledgeSku
    score: int
    matched_term: str


@dataclass
class ComponentMatch:
    component: DingmaKnowledgeComponent
    score: int
    matched_term: str


@dataclass
class CategoryMatch:
    category_name: str
    category_code: str
    matched_term: str
    skus: List[DingmaKnowledgeSku] = field(default_factory=list)


class DingmaKnowledgeService:
    """顶妈知识库 v2"""

    @staticmethod
    async def resolve_tenant_id(db: AsyncSession, scoped_tenant_id: Optional[int] = None) -> int:
        if scoped_tenant_id is not None:
            return int(scoped_tenant_id)
        result = await db.execute(select(Tenant.id).where(Tenant.code == DINGMA_TENANT_CODE))
        tenant_id = result.scalar_one_or_none()
        if tenant_id is None:
            raise ValueError(f"未找到租户 code={DINGMA_TENANT_CODE}")
        return int(tenant_id)

    @staticmethod
    async def load_skus(db: AsyncSession, tenant_id: int) -> List[DingmaKnowledgeSku]:
        result = await db.execute(
            select(DingmaKnowledgeSku)
            .options(
                selectinload(DingmaKnowledgeSku.component_links).selectinload(
                    DingmaSkuComponentLink.component
                )
            )
            .where(
                and_(DingmaKnowledgeSku.tenant_id == tenant_id, DingmaKnowledgeSku.status == 1)
            )
            .order_by(DingmaKnowledgeSku.sort_order, DingmaKnowledgeSku.id)
        )
        return list(result.scalars().all())

    @staticmethod
    async def load_components(db: AsyncSession, tenant_id: int) -> List[DingmaKnowledgeComponent]:
        result = await db.execute(
            select(DingmaKnowledgeComponent).where(
                and_(
                    DingmaKnowledgeComponent.tenant_id == tenant_id,
                    DingmaKnowledgeComponent.status == 1,
                )
            )
            .order_by(DingmaKnowledgeComponent.sort_order, DingmaKnowledgeComponent.id)
        )
        return list(result.scalars().all())

    @staticmethod
    def _normalize_input(text: str) -> str:
        text = (text or "").strip()
        if text.startswith("顶妈"):
            text = text[2:].strip()
        return text

    @staticmethod
    def _normalize_aliases(raw: Optional[object]) -> List[str]:
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
    def detect_scene(user_input: str) -> CopywritingScene:
        text = DingmaKnowledgeService._normalize_input(user_input)
        if any(kw in text for kw in PROCESS_SCENE_KEYWORDS):
            return CopywritingScene.PROCESS
        return CopywritingScene.GENERAL

    @staticmethod
    def _match_by_terms(
        text: str,
        terms: Sequence[str],
    ) -> tuple[int, str]:
        best_score = 0
        best_term = ""
        for term in terms:
            term = term.strip()
            if len(term) < 2 or term not in text:
                continue
            score = len(term) * 10
            if score > best_score:
                best_score = score
                best_term = term
        return best_score, best_term

    @staticmethod
    def _match_skus(
        user_input: str,
        skus: Sequence[DingmaKnowledgeSku],
        max_matches: int = DEFAULT_MAX_MATCHES,
    ) -> List[SkuMatch]:
        text = DingmaKnowledgeService._normalize_input(user_input)
        if not text:
            return []

        candidates: List[SkuMatch] = []
        for sku in skus:
            terms = [sku.sku_name, *DingmaKnowledgeService._normalize_aliases(sku.aliases)]
            score, matched = DingmaKnowledgeService._match_by_terms(text, terms)
            if score > 0:
                candidates.append(SkuMatch(sku=sku, score=score, matched_term=matched))

        candidates.sort(key=lambda x: x.score, reverse=True)
        seen: set[str] = set()
        unique: List[SkuMatch] = []
        for item in candidates:
            if item.sku.sku_code in seen:
                continue
            seen.add(item.sku.sku_code)
            unique.append(item)
            if len(unique) >= max_matches:
                break
        return unique

    @staticmethod
    def _match_components(
        user_input: str,
        components: Sequence[DingmaKnowledgeComponent],
        max_matches: int = DEFAULT_MAX_MATCHES,
    ) -> List[ComponentMatch]:
        text = DingmaKnowledgeService._normalize_input(user_input)
        if not text:
            return []

        candidates: List[ComponentMatch] = []
        for comp in components:
            terms = [comp.component_name, *DingmaKnowledgeService._normalize_aliases(comp.aliases)]
            pc = comp.process_copywriting or {}
            if isinstance(pc, dict):
                terms.extend(pc.get("aliases") or [])
                focus = pc.get("focus_label")
                if focus:
                    terms.append(str(focus))
            score, matched = DingmaKnowledgeService._match_by_terms(text, terms)
            if score > 0:
                candidates.append(ComponentMatch(component=comp, score=score, matched_term=matched))

        candidates.sort(key=lambda x: x.score, reverse=True)
        seen: set[str] = set()
        unique: List[ComponentMatch] = []
        for item in candidates:
            if item.component.component_code in seen:
                continue
            seen.add(item.component.component_code)
            unique.append(item)
            if len(unique) >= max_matches:
                break
        return unique

    @staticmethod
    def _match_categories(
        user_input: str,
        skus: Sequence[DingmaKnowledgeSku],
        max_matches: int = DEFAULT_CATEGORY_MAX_MATCHES,
    ) -> List[CategoryMatch]:
        text = DingmaKnowledgeService._normalize_input(user_input)
        if not text:
            return []

        cat_map: Dict[str, CategoryMatch] = {}
        for sku in skus:
            cat_name = (sku.category_name or "").strip()
            cat_code = (sku.category_code or "").strip()
            if len(cat_name) < 2 or cat_name not in text:
                continue
            key = cat_code or cat_name
            if key not in cat_map:
                cat_map[key] = CategoryMatch(
                    category_name=cat_name,
                    category_code=cat_code,
                    matched_term=cat_name,
                    skus=[],
                )
            cat_map[key].skus.append(sku)

        hits = list(cat_map.values())
        for hit in hits:
            hit.skus.sort(key=lambda s: (s.sort_order, s.id))
            hit.skus = hit.skus[:max_matches]
        hits.sort(key=lambda x: len(x.category_name), reverse=True)
        return hits

    @staticmethod
    def _guardrail_dict(raw: Optional[dict]) -> Dict[str, List[str]]:
        if not raw or not isinstance(raw, dict):
            return {"contains": [], "excludes": [], "forbidden": [], "writable_tags": []}
        return {
            "contains": list(raw.get("contains") or []),
            "excludes": list(raw.get("excludes") or []),
            "forbidden": list(raw.get("forbidden") or []),
            "writable_tags": list(raw.get("writable_tags") or []),
        }

    @staticmethod
    def _format_guardrail_line(name: str, guardrail: Dict[str, List[str]]) -> str:
        parts = [f"- {name}"]
        if guardrail.get("contains"):
            parts.append(f"含：{'、'.join(guardrail['contains'])}")
        if guardrail.get("excludes"):
            parts.append(f"不含：{'、'.join(guardrail['excludes'])}")
        if guardrail.get("forbidden"):
            parts.append(f"禁：{'、'.join(guardrail['forbidden'])}")
        return " | ".join(parts)

    @staticmethod
    def _merge_contains(guardrails: Sequence[Dict[str, List[str]]]) -> str:
        seen: set[str] = set()
        merged: List[str] = []
        for g in guardrails:
            for item in g.get("contains") or []:
                if item and item not in seen:
                    seen.add(item)
                    merged.append(item)
                if len(merged) >= MAX_MERGED_CONTAINS_ITEMS:
                    return "、".join(merged)
        return "、".join(merged)

    @staticmethod
    def _merge_forbidden(guardrails: Sequence[Dict[str, List[str]]]) -> str:
        seen: set[str] = set()
        merged: List[str] = []
        for g in guardrails:
            for item in g.get("forbidden") or []:
                if item and item not in seen:
                    seen.add(item)
                    merged.append(item)
        return "、".join(merged) if merged else "治疗、药用、未列出的食材或功效"

    @staticmethod
    def _get_process_focus_component(sku: DingmaKnowledgeSku) -> Optional[DingmaKnowledgeComponent]:
        links = sorted(
            sku.component_links or [],
            key=lambda x: (not x.process_focus, x.sort_order, x.id),
        )
        for link in links:
            if link.process_focus and link.component:
                return link.component
        return None

    @staticmethod
    def _format_process_block(
        label: str,
        process: dict,
        guardrail: Optional[dict] = None,
    ) -> List[str]:
        if not process or not isinstance(process, dict):
            return []

        parts = [f"【过程场景 · {label}】"]
        if process.get("scene_hint"):
            parts.append(f"场景提示：{process['scene_hint']}")

        writable_ing = process.get("writable_ingredients") or []
        if not writable_ing and guardrail:
            writable_ing = (guardrail or {}).get("contains") or []
        if writable_ing:
            parts.append(f"过程可写配料：{'、'.join(writable_ing[:16])}")

        actions = process.get("writable_actions") or []
        if actions:
            parts.append(f"过程可写动作：{'、'.join(actions[:8])}")

        forbidden = process.get("forbidden_ingredients") or []
        if forbidden:
            parts.append(f"过程禁写：{'、'.join(forbidden[:12])}")

        parts.append("不写具体克重/配比/工业步骤")
        return parts

    @staticmethod
    def _appendix_prefix(extra: str = "") -> List[str]:
        parts = [KNOWLEDGE_APPENDIX_HEADER, KNOWLEDGE_GUARDRAIL_LINE]
        if extra:
            parts.append(extra)
        return parts

    @staticmethod
    def _format_sku_general_block(matches: Sequence[SkuMatch]) -> str:
        parts = DingmaKnowledgeService._appendix_prefix()
        parts.append("")
        parts.append("【核对项 - 成品 SKU】")
        for item in matches:
            g = DingmaKnowledgeService._guardrail_dict(item.sku.guardrail)
            parts.append(DingmaKnowledgeService._format_guardrail_line(item.sku.sku_name, g))
        return "\n".join(parts).strip()

    @staticmethod
    def _format_sku_process_block(matches: Sequence[SkuMatch]) -> str:
        parts = DingmaKnowledgeService._appendix_prefix(
            "当前为「制作过程」场景：优先写 process_focus 组件的过程事实，成品「含」仅作背景核对。"
        )
        parts.append("")

        for item in matches:
            sku = item.sku
            g = DingmaKnowledgeService._guardrail_dict(sku.guardrail)
            parts.append(f"## 成品：{sku.sku_name}")
            parts.append(DingmaKnowledgeService._format_guardrail_line(sku.sku_name, g))

            focus_comp = DingmaKnowledgeService._get_process_focus_component(sku)
            if focus_comp and focus_comp.process_copywriting:
                parts.extend(
                    DingmaKnowledgeService._format_process_block(
                        focus_comp.component_name,
                        focus_comp.process_copywriting,
                        focus_comp.guardrail,
                    )
                )
            elif sku.process_copywriting:
                parts.extend(
                    DingmaKnowledgeService._format_process_block(
                        sku.sku_name,
                        sku.process_copywriting,
                        sku.guardrail,
                    )
                )
            else:
                parts.append(
                    "【过程场景】未配置过程焦点，仅可写成品「含」中已有配料，勿编造具体制作细节。"
                )
            parts.append("")

        return "\n".join(parts).strip()

    @staticmethod
    def _format_component_process_block(matches: Sequence[ComponentMatch]) -> str:
        parts = DingmaKnowledgeService._appendix_prefix("用户直接提及组件/子配方，按组件过程事实写作。")
        parts.append("")
        for item in matches:
            comp = item.component
            g = DingmaKnowledgeService._guardrail_dict(comp.guardrail)
            parts.append(DingmaKnowledgeService._format_guardrail_line(comp.component_name, g))
            if comp.process_copywriting:
                parts.extend(
                    DingmaKnowledgeService._format_process_block(
                        comp.component_name,
                        comp.process_copywriting,
                        comp.guardrail,
                    )
                )
            parts.append("")
        return "\n".join(parts).strip()

    @staticmethod
    def _format_category_block(categories: Sequence[CategoryMatch]) -> str:
        parts = DingmaKnowledgeService._appendix_prefix()
        for idx, cat in enumerate(categories):
            if idx > 0:
                parts.append("")
            parts.append(f"【核对项 - 品类·{cat.category_name}】")
            guardrails = [
                DingmaKnowledgeService._guardrail_dict(s.guardrail) for s in cat.skus
            ]
            merged_contains = DingmaKnowledgeService._merge_contains(guardrails)
            if merged_contains:
                parts.append(
                    f"写到本品类具体配料时，仅可使用：{merged_contains}；禁止编造未列出项。"
                )
            parts.append(f"共性禁止：{DingmaKnowledgeService._merge_forbidden(guardrails)}")
            parts.append("各 SKU 核对：")
            for sku in cat.skus[:10]:
                g = DingmaKnowledgeService._guardrail_dict(sku.guardrail)
                parts.append(DingmaKnowledgeService._format_guardrail_line(sku.sku_name, g))
        return "\n".join(parts).strip()

    @staticmethod
    def _format_sku_index(skus: Sequence[DingmaKnowledgeSku]) -> str:
        by_cat: Dict[str, List[str]] = {}
        for sku in skus:
            cat = sku.category_name or "其他"
            by_cat.setdefault(cat, []).append(sku.sku_name)

        parts = DingmaKnowledgeService._appendix_prefix(KNOWLEDGE_SCENE_HINT)
        parts.extend(["", "【品类索引 - 仅供场景参考】"])
        for cat, names in sorted(by_cat.items()):
            display = "、".join(names[:6])
            if len(names) > 6:
                display += f" 等{len(names)}款"
            parts.append(f"- {cat}：{display}")
        return "\n".join(parts).strip()

    @staticmethod
    def _format_after_sales_block(
        skus: Sequence[DingmaKnowledgeSku],
        components: Sequence[DingmaKnowledgeComponent],
        sku_matches: Sequence[SkuMatch],
        comp_matches: Sequence[ComponentMatch],
    ) -> str:
        parts = ["【产品配方事实 - 可引用克重与步骤，但仍禁止编造未列出信息】", ""]
        seen_sku: set[int] = set()
        seen_comp: set[int] = set()

        for m in sku_matches:
            if m.sku.id in seen_sku:
                continue
            seen_sku.add(m.sku.id)
            sku = m.sku
            parts.append(f"## {sku.sku_name}")
            if sku.pack_formula:
                parts.append(f"出货配比：{sku.pack_formula}")
            parts.append("")

        for m in comp_matches:
            if m.component.id in seen_comp:
                continue
            seen_comp.add(m.component.id)
            comp = m.component
            parts.append(f"## {comp.component_name}")
            if comp.pack_formula:
                parts.append(f"用法：{comp.pack_formula}")
            detail = comp.recipe_detail or {}
            if isinstance(detail, dict):
                ings = detail.get("ingredients") or []
                if ings:
                    ing_text = "、".join(
                        f"{i.get('name', '')}{i.get('amount', '')}"
                        for i in ings
                        if isinstance(i, dict)
                    )
                    parts.append(f"配料：{ing_text}")
                steps = detail.get("steps") or []
                if steps:
                    parts.append("步骤：" + "；".join(str(s) for s in steps[:8]))
            parts.append("")

        if not seen_sku and not seen_comp:
            parts.append("（未命中具体 SKU/组件，请参考后台全量配方库）")
        return "\n".join(parts).strip()

    @staticmethod
    async def resolve_prompt_block(
        db: AsyncSession,
        user_input: str,
        tenant_id: Optional[int] = None,
        scoped_tenant_id: Optional[int] = None,
        inject_mode: KnowledgeInjectMode = KnowledgeInjectMode.COPYWRITING,
        max_matches: int = DEFAULT_MAX_MATCHES,
    ) -> str:
        try:
            resolved_tenant_id = tenant_id or await DingmaKnowledgeService.resolve_tenant_id(
                db, scoped_tenant_id
            )
        except ValueError as e:
            logger.warning(f"[DingmaKnowledge] 租户解析失败: {e}")
            return ""

        skus = await DingmaKnowledgeService.load_skus(db, resolved_tenant_id)
        components = await DingmaKnowledgeService.load_components(db, resolved_tenant_id)
        if not skus and not components:
            logger.warning(f"[DingmaKnowledge] 租户 {resolved_tenant_id} 无知识库数据")
            return ""

        scene = DingmaKnowledgeService.detect_scene(user_input)
        sku_matches = DingmaKnowledgeService._match_skus(user_input, skus, max_matches)
        comp_matches = DingmaKnowledgeService._match_components(user_input, components, max_matches)

        if inject_mode == KnowledgeInjectMode.AFTER_SALES:
            block = DingmaKnowledgeService._format_after_sales_block(
                skus, components, sku_matches, comp_matches
            )
            logger.info(f"[DingmaKnowledge] 售后模式 block len={len(block)}")
            return block

        # 文案模式
        if sku_matches:
            if scene == CopywritingScene.PROCESS:
                block = DingmaKnowledgeService._format_sku_process_block(sku_matches)
            else:
                block = DingmaKnowledgeService._format_sku_general_block(sku_matches)
            logger.info(
                f"[DingmaKnowledge] SKU 命中 {[m.sku.sku_name for m in sku_matches]}, "
                f"scene={scene.value}"
            )
            return block

        # 仅命中组件（如「今天熬辣油」）
        if comp_matches and scene == CopywritingScene.PROCESS:
            block = DingmaKnowledgeService._format_component_process_block(comp_matches)
            logger.info(
                f"[DingmaKnowledge] 组件过程命中 "
                f"{[m.component.component_name for m in comp_matches]}"
            )
            return block

        categories = DingmaKnowledgeService._match_categories(user_input, skus)
        if categories:
            block = DingmaKnowledgeService._format_category_block(categories)
            logger.info(f"[DingmaKnowledge] 品类命中 {[c.category_name for c in categories]}")
            return block

        logger.info("[DingmaKnowledge] 未匹配，注入品类索引")
        return DingmaKnowledgeService._format_sku_index(skus)

    @staticmethod
    def append_knowledge(base_system_prompt: str, knowledge_block: str) -> str:
        if not knowledge_block:
            return base_system_prompt
        if base_system_prompt:
            return f"{base_system_prompt}\n\n{'=' * 40}\n\n{knowledge_block}"
        return knowledge_block

    @staticmethod
    def merge_with_knowledge_guard(
        agent_system_prompt: str,
        knowledge_block: str,
        max_total_length: int,
    ) -> str:
        if not knowledge_block:
            return agent_system_prompt
        merged = DingmaKnowledgeService.append_knowledge(agent_system_prompt, knowledge_block)
        if len(merged) <= max_total_length:
            return merged

        sep_len = len(f"\n\n{'=' * 40}\n\n")
        budget = max_total_length - len(agent_system_prompt) - sep_len - 30
        if budget < 200:
            logger.warning("[DingmaKnowledge] agent prompt 过长，跳过知识块")
            return agent_system_prompt[:max_total_length]
        truncated = knowledge_block[:budget] + "\n…（成分护栏已截断）"
        return DingmaKnowledgeService.append_knowledge(agent_system_prompt, truncated)
