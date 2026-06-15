"""
顶妈产品知识库服务：模糊匹配 + Prompt 注入

文案模式：append 轻量成分护栏（非主 prompt），智能体技能优先。
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence

from loguru import logger
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from models.dingma_product_knowledge import DingmaProductKnowledge
from models.tenant import Tenant
from services.dingma.constants import (
    DEFAULT_CATEGORY_MAX_MATCHES,
    DEFAULT_MAX_MATCHES,
    DINGMA_TENANT_CODE,
    INGREDIENT_NAME_KEYWORDS,
    INGREDIENT_PRODUCT_CODE_PREFIXES,
    INGREDIENT_PRODUCT_CODE_SUFFIXES,
    KNOWLEDGE_APPENDIX_HEADER,
    KNOWLEDGE_CATEGORY_SCENE_HINT,
    KNOWLEDGE_GUARDRAIL_LINE,
    KNOWLEDGE_PERSONA_PRODUCT_HINT,
    KNOWLEDGE_SCENE_HINT,
    MAX_MERGED_CONTAINS_ITEMS,
    MAX_PERSONA_CATEGORY_GUARD,
    KnowledgeInjectMode,
)


@dataclass
class ProductMatch:
    """产品匹配结果"""

    product: DingmaProductKnowledge
    score: int
    matched_term: str


@dataclass
class CategoryMatch:
    """品类匹配结果"""

    category_name: str
    category_code: str
    matched_term: str
    products: List[DingmaProductKnowledge]


class DingmaKnowledgeService:
    """顶妈知识库：匹配与 Prompt 块组装"""

    @staticmethod
    async def resolve_tenant_id(db: AsyncSession, scoped_tenant_id: Optional[int] = None) -> int:
        """解析 dingma 租户 ID"""
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
    def is_ingredient_product(product: DingmaProductKnowledge) -> bool:
        """原料/子配方：学员对外文案默认不注入（如母馅、sub_ 子配方）"""
        code = (product.product_code or "").strip()
        name = (product.product_name or "").strip()
        if any(code.startswith(p) for p in INGREDIENT_PRODUCT_CODE_PREFIXES):
            return True
        if any(code.endswith(s) for s in INGREDIENT_PRODUCT_CODE_SUFFIXES):
            return True
        if any(kw in name for kw in INGREDIENT_NAME_KEYWORDS):
            return True
        return False

    @staticmethod
    def filter_consumer_products(
        products: Sequence[DingmaProductKnowledge],
    ) -> List[DingmaProductKnowledge]:
        """文案模式：仅保留对外成品 SKU"""
        return [p for p in products if not DingmaKnowledgeService.is_ingredient_product(p)]

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
    def _normalize_input_for_match(user_input: str) -> str:
        """匹配前规范化用户输入：去空白、去品牌前缀「顶妈」"""
        text = (user_input or "").strip()
        if text.startswith("顶妈"):
            text = text[2:].strip()
        return text

    @staticmethod
    def _extract_guardrails(copywriting_facts: str) -> Dict[str, str]:
        """
        从 copywriting_facts 提取含/不含/不可写，忽略「可写」与标题行。
        """
        result: Dict[str, str] = {}
        if not copywriting_facts:
            return result
        for line in copywriting_facts.splitlines():
            line = line.strip()
            if not line or line.startswith("【"):
                continue
            if line.startswith("含："):
                result["含"] = line[2:].strip()
            elif line.startswith("不含："):
                result["不含"] = line[3:].strip()
            elif line.startswith("不可写："):
                result["禁"] = line[4:].strip()
        return result

    @staticmethod
    def _format_slim_guardrail_line(product_name: str, guardrails: Dict[str, str]) -> str:
        """单品一行护栏"""
        parts = [f"- {product_name}"]
        if guardrails.get("含"):
            parts.append(f"含：{guardrails['含']}")
        if guardrails.get("不含"):
            parts.append(f"不含：{guardrails['不含']}")
        if guardrails.get("禁"):
            parts.append(f"禁：{guardrails['禁']}")
        return " | ".join(parts)

    @staticmethod
    def _merge_allowed_contains(guardrails_list: Sequence[Dict[str, str]]) -> str:
        """合并多条「含」为品类可写配料白名单（去重，不写克重）"""
        seen: set[str] = set()
        merged: List[str] = []
        for g in guardrails_list:
            raw = (g.get("含") or "").strip()
            if not raw:
                continue
            for item in re.split(r"[、，,；;+/]", raw):
                item = item.strip()
                if not item or item in seen:
                    continue
                seen.add(item)
                merged.append(item)
                if len(merged) >= MAX_MERGED_CONTAINS_ITEMS:
                    return "、".join(merged)
        return "、".join(merged)

    @staticmethod
    def _merge_forbidden(guardrails_list: Sequence[Dict[str, str]]) -> str:
        """合并多条「不可写」为品类共性禁止项"""
        chunks: List[str] = []
        for g in guardrails_list:
            if g.get("禁"):
                chunks.append(g["禁"])
        if not chunks:
            return "治疗、药用、未列出的食材或功效"
        # 去重并保持顺序
        seen: set[str] = set()
        merged: List[str] = []
        for chunk in chunks:
            for item in re.split(r"[、，,；;]", chunk):
                item = item.strip()
                if item and item not in seen:
                    seen.add(item)
                    merged.append(item)
        return "、".join(merged[:12])

    @staticmethod
    def _appendix_prefix(extra_hint: str = "") -> List[str]:
        parts = [KNOWLEDGE_APPENDIX_HEADER, KNOWLEDGE_GUARDRAIL_LINE]
        if extra_hint:
            parts.append(extra_hint)
        return parts

    @staticmethod
    def _match_products(
        user_input: str,
        products: Sequence[DingmaProductKnowledge],
        max_matches: int = DEFAULT_MAX_MATCHES,
    ) -> List[ProductMatch]:
        """对用户输入做子串匹配：产品名 + 别名"""
        text = DingmaKnowledgeService._normalize_input_for_match(user_input)
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
                    score = len(term) * 10
                    if score > best_score:
                        best_score = score
                        best_term = term

            if best_score > 0:
                candidates.append(ProductMatch(product=product, score=best_score, matched_term=best_term))

        candidates.sort(key=lambda x: x.score, reverse=True)

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
    def _match_category(
        user_input: str,
        products: Sequence[DingmaProductKnowledge],
        max_matches: int = DEFAULT_CATEGORY_MAX_MATCHES,
    ) -> Optional[CategoryMatch]:
        """品类级匹配：输入含 category_name 时返回最长命中的品类"""
        hits = DingmaKnowledgeService._match_all_categories(
            user_input,
            products,
            max_matches,
        )
        return hits[0] if hits else None

    @staticmethod
    def _match_all_categories(
        text: str,
        products: Sequence[DingmaProductKnowledge],
        max_matches: int = DEFAULT_CATEGORY_MAX_MATCHES,
    ) -> List[CategoryMatch]:
        """输入中命中多个品类时，按品类名长度降序返回"""
        text = DingmaKnowledgeService._normalize_input_for_match(text)
        if not text or not products:
            return []

        category_map: dict[str, dict] = {}
        for product in products:
            cat_name = (product.category_name or "").strip()
            cat_code = (product.category_code or "").strip()
            if not cat_name or len(cat_name) < 2:
                continue
            key = cat_code or cat_name
            if key not in category_map:
                category_map[key] = {
                    "category_name": cat_name,
                    "category_code": cat_code,
                    "products": [],
                }
            category_map[key]["products"].append(product)

        hits: List[CategoryMatch] = []
        for item in category_map.values():
            cat_name = item["category_name"]
            if cat_name not in text:
                continue
            consumer_products = DingmaKnowledgeService.filter_consumer_products(item["products"])
            cat_products = consumer_products[:max_matches]
            if not cat_products:
                continue
            hits.append(
                CategoryMatch(
                    category_name=cat_name,
                    category_code=item["category_code"],
                    matched_term=cat_name,
                    products=cat_products,
                )
            )

        hits.sort(key=lambda x: len(x.category_name), reverse=True)
        return hits

    @staticmethod
    def _extract_main_product_terms(ip_persona_prompt: str) -> List[str]:
        """从 IP 人设「主要产品」提取品类关键词"""
        text = (ip_persona_prompt or "").strip()
        if not text:
            return []

        main_line = ""
        lines = text.splitlines()
        for idx, line in enumerate(lines):
            if line.strip() in ("## 主要产品", "主要产品", "##主要产品"):
                for follow in lines[idx + 1 :]:
                    follow = follow.strip()
                    if not follow or follow.startswith("##"):
                        break
                    main_line = follow
                    break
                break

        if not main_line:
            return []

        terms: List[str] = []
        for chunk in re.split(r"[、，,；;/\s]+", main_line):
            chunk = chunk.strip()
            if len(chunk) >= 2:
                terms.append(chunk)
        return terms

    @staticmethod
    def _resolve_persona_categories(
        ip_persona_prompt: str,
        products: Sequence[DingmaProductKnowledge],
        exclude_names: Optional[Sequence[str]] = None,
    ) -> List[CategoryMatch]:
        """根据 IP 主营产品补充品类护栏（排除已在用户输入命中的品类）"""
        exclude = set(exclude_names or [])
        terms = DingmaKnowledgeService._extract_main_product_terms(ip_persona_prompt)
        if not terms:
            return []

        # 用主营词拼接成检索文本，复用品类匹配
        probe_text = " ".join(terms)
        all_hits = DingmaKnowledgeService._match_all_categories(probe_text, products)
        result: List[CategoryMatch] = []
        seen: set[str] = set()
        for cat in all_hits:
            if cat.category_name in exclude or cat.category_name in seen:
                continue
            seen.add(cat.category_name)
            result.append(cat)
            if len(result) >= MAX_PERSONA_CATEGORY_GUARD:
                break
        return result

    @staticmethod
    def _should_prefer_category_over_ingredient_matches(
        user_input: str,
        matches: Sequence[ProductMatch],
        match_pool: Sequence[DingmaProductKnowledge],
    ) -> bool:
        """用户输入命中品类词、但 SKU 仅命中原料/母馅时，改走品类护栏"""
        if not matches:
            return False
        if any(not DingmaKnowledgeService.is_ingredient_product(m.product) for m in matches):
            return False
        text = DingmaKnowledgeService._normalize_input_for_match(user_input)
        return bool(DingmaKnowledgeService._match_all_categories(text, match_pool))

    @staticmethod
    def _format_category_section(
        category: CategoryMatch,
        *,
        section_title: Optional[str] = None,
        scene_hint: str = KNOWLEDGE_CATEGORY_SCENE_HINT,
    ) -> List[str]:
        """单个品类的精简护栏段落（可组合进多块）"""
        guardrails_list = [
            DingmaKnowledgeService._extract_guardrails(p.copywriting_facts or "")
            for p in category.products
        ]
        names = [p.product_name for p in category.products]
        merged_forbidden = DingmaKnowledgeService._merge_forbidden(guardrails_list)
        merged_contains = DingmaKnowledgeService._merge_allowed_contains(guardrails_list)

        parts: List[str] = []
        if section_title:
            parts.append(section_title)
        if scene_hint:
            parts.append(scene_hint)
        parts.extend([
            f"品类：{category.category_name}",
            f"可选成品（仅名称参考，正文不必全写）：{'、'.join(names)}",
        ])
        if merged_contains:
            parts.append(
                f"写到本品类具体配料/酱料时，仅可使用：{merged_contains}；"
                "禁止编造未列出项（如猪油、鸡蛋、豆芽、火腿肠等）。"
            )
        parts.append(f"共性禁止：{merged_forbidden}")
        parts.append("若正文写到某一具体口味，再核对：")

        for product in category.products[:8]:
            guardrails = DingmaKnowledgeService._extract_guardrails(
                product.copywriting_facts or ""
            )
            parts.append(
                DingmaKnowledgeService._format_slim_guardrail_line(
                    product.product_name, guardrails
                )
            )
        if len(category.products) > 8:
            parts.append(f"… 另有 {len(category.products) - 8} 款，未写具体口味则无需展开")
        return parts

    @staticmethod
    def _format_copywriting_block(matches: Sequence[ProductMatch]) -> str:
        """SKU 命中：仅注入精简含/不含/禁"""
        parts = DingmaKnowledgeService._appendix_prefix()
        parts.append("")
        parts.append("【核对项 - 仅当正文写到该 SKU 时适用】")

        for item in matches:
            product = item.product
            if DingmaKnowledgeService.is_ingredient_product(product):
                # 用户明确提到母馅等原料：只给场景提示，不罗列工业配料
                parts.append(
                    f"- {product.product_name}：写自制/包制场景即可，"
                    "勿把原料配比写进朋友圈，勿出现品牌名。"
                )
                continue
            guardrails = DingmaKnowledgeService._extract_guardrails(
                product.copywriting_facts or ""
            )
            parts.append(DingmaKnowledgeService._format_slim_guardrail_line(
                product.product_name, guardrails
            ))

        return "\n".join(parts).strip()

    @staticmethod
    def _format_category_copywriting_block(
        category: CategoryMatch,
        extra_categories: Optional[Sequence[CategoryMatch]] = None,
    ) -> str:
        """品类命中：成品名列表 + 可写配料白名单 + 各行护栏"""
        parts = DingmaKnowledgeService._appendix_prefix()
        parts.extend(
            DingmaKnowledgeService._format_category_section(
                category,
                section_title="【核对项 - 用户提及或场景相关的品类】",
            )
        )

        for extra in extra_categories or []:
            parts.append("")
            parts.extend(
                DingmaKnowledgeService._format_category_section(
                    extra,
                    section_title=f"【核对项 - IP 主营·{extra.category_name}（正文顺带提到时适用）】",
                    scene_hint=KNOWLEDGE_PERSONA_PRODUCT_HINT,
                )
            )

        return "\n".join(parts).strip()

    @staticmethod
    def _format_after_sales_block(matches: Sequence[ProductMatch]) -> str:
        """售后模式：保留全量配方信息"""
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
        """未命中：极轻量品类索引"""
        by_category: dict[str, List[str]] = {}
        for p in DingmaKnowledgeService.filter_consumer_products(products):
            cat = p.category_name or "其他"
            by_category.setdefault(cat, []).append(p.product_name)

        parts = DingmaKnowledgeService._appendix_prefix(KNOWLEDGE_SCENE_HINT)
        parts.extend(["", "【品类索引 - 仅供场景参考】"])
        for cat, names in sorted(by_category.items()):
            display = "、".join(names[:6])
            if len(names) > 6:
                display += f" 等{len(names)}款"
            parts.append(f"- {cat}：{display}")

        return "\n".join(parts).strip()

    @staticmethod
    async def resolve_prompt_block(
        db: AsyncSession,
        user_input: str,
        tenant_id: Optional[int] = None,
        scoped_tenant_id: Optional[int] = None,
        inject_mode: KnowledgeInjectMode = KnowledgeInjectMode.COPYWRITING,
        max_matches: int = DEFAULT_MAX_MATCHES,
        ip_persona_prompt: Optional[str] = None,
    ) -> str:
        """解析知识护栏块，供 dingma append 到 system prompt 末尾"""
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

        if inject_mode == KnowledgeInjectMode.COPYWRITING:
            match_pool = DingmaKnowledgeService.filter_consumer_products(products)
        else:
            match_pool = list(products)

        matches = DingmaKnowledgeService._match_products(user_input, match_pool, max_matches)

        # 文案模式：若成品未命中，允许在全量库中匹配（含用户明确点名的母馅）
        if inject_mode == KnowledgeInjectMode.COPYWRITING and not matches:
            all_matches = DingmaKnowledgeService._match_products(
                user_input, products, max_matches
            )
            matches = all_matches

        # 仅命中原料/母馅且用户输入含品类词 → 改走品类护栏（避免「包馄饨」只给母馅提示）
        if (
            inject_mode == KnowledgeInjectMode.COPYWRITING
            and matches
            and DingmaKnowledgeService._should_prefer_category_over_ingredient_matches(
                user_input, matches, match_pool
            )
        ):
            logger.info(
                "[DingmaKnowledge] SKU 仅命中原料，改用品类护栏: "
                f"{[m.product.product_name for m in matches]}"
            )
            matches = []

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

        user_categories = DingmaKnowledgeService._match_all_categories(user_input, match_pool)
        if user_categories:
            primary = user_categories[0]
            extra = DingmaKnowledgeService._resolve_persona_categories(
                ip_persona_prompt or "",
                match_pool,
                exclude_names=[c.category_name for c in user_categories],
            )
            if inject_mode == KnowledgeInjectMode.AFTER_SALES:
                product_matches = [
                    ProductMatch(product=p, score=0, matched_term=p.product_name)
                    for p in primary.products
                ]
                block = DingmaKnowledgeService._format_after_sales_block(product_matches)
            else:
                block = DingmaKnowledgeService._format_category_copywriting_block(
                    primary, extra_categories=extra
                )
            logger.info(
                f"[DingmaKnowledge] 品类命中: {primary.category_name}, "
                f"成品数={len(primary.products)}, "
                f"人设补充={[c.category_name for c in extra]}, mode={inject_mode.value}"
            )
            return block

        logger.info("[DingmaKnowledge] 未匹配，注入场景索引")
        return DingmaKnowledgeService._format_product_index(products)

    @staticmethod
    def append_knowledge(base_system_prompt: str, knowledge_block: str) -> str:
        """将知识护栏 append 到 system prompt 末尾（智能体技能优先）"""
        if not knowledge_block:
            return base_system_prompt
        if base_system_prompt:
            return f"{base_system_prompt}\n\n{'=' * 40}\n\n{knowledge_block}"
        return knowledge_block

    @staticmethod
    def prepend_knowledge(base_system_prompt: str, knowledge_block: str) -> str:
        """已废弃：请使用 append_knowledge"""
        return DingmaKnowledgeService.append_knowledge(base_system_prompt, knowledge_block)

    @staticmethod
    def merge_with_knowledge_guard(
        agent_system_prompt: str,
        knowledge_block: str,
        max_total_length: int,
    ) -> str:
        """
        合并 prompt：优先保留 agent 技能，超出长度时截断知识块。
        """
        if not knowledge_block:
            return agent_system_prompt
        merged = DingmaKnowledgeService.append_knowledge(agent_system_prompt, knowledge_block)
        if len(merged) <= max_total_length:
            return merged

        separator = f"\n\n{'=' * 40}\n\n"
        sep_len = len(separator)
        agent_len = len(agent_system_prompt)
        budget = max_total_length - agent_len - sep_len - 30
        if budget < 200:
            # agent 本身过长，仅保留 agent
            logger.warning("[DingmaKnowledge] agent prompt 过长，跳过知识块注入")
            return agent_system_prompt[:max_total_length]

        truncated_kb = knowledge_block[:budget] + "\n…（成分护栏已截断）"
        return DingmaKnowledgeService.append_knowledge(agent_system_prompt, truncated_kb)
