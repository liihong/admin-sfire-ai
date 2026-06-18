"""
将 legacy product_knowledge_2026.json 转换为 v2 结构（components + skus + links）

执行：
    cd backend && python -m scripts.transform_legacy_knowledge
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

_BACKEND_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_BACKEND_ROOT))

LEGACY_FILE = _BACKEND_ROOT / "data" / "dingma" / "product_knowledge_2026.json"
OUTPUT_FILE = _BACKEND_ROOT / "data" / "dingma" / "knowledge_v2.json"

# 组件识别：sub_* + 母馅/皮
COMPONENT_CODE_PREFIXES = ("sub_",)
COMPONENT_EXACT_CODES = {"wonton_muxian", "jiaozi_muxian", "baozi_pi"}

# pack_formula 关键词 → (component_code, role, process_focus)
PACK_COMPONENT_RULES: List[Tuple[str, str, str, bool]] = [
    ("传统鸡丁肉", "sub_chuantong_jiding", "primary_sauce", True),
    ("豆豉酱", "sub_douchi_jiang", "primary_sauce", True),
    ("番茄肉酱", "sub_fanqie_niurou_jiang", "primary_sauce", True),
    ("番茄牛肉酱", "sub_fanqie_niurou_jiang", "primary_sauce", True),
    ("松茸酱", "sub_jisongrong_jiang", "primary_sauce", True),
    ("姬松茸酱料", "sub_jisongrong_jiang", "primary_sauce", True),
    ("咖喱酱", "sub_gali_jiang", "primary_sauce", True),
    ("辣牛肉酱", "sub_la_niurou_jiang", "primary_sauce", True),
    ("藤椒酱", "sub_tengjiao_jiang", "primary_sauce", True),
    ("金汤酱", "sub_jintang_jiang", "primary_sauce", True),
    ("龙虾酱", "sub_longxia_jiang", "primary_sauce", True),
    ("牛油火锅酱", "sub_niuyou_huoguo_suanla_fen", "primary_sauce", True),
    ("泡菜1包", "sub_paocai", "primary_sauce", True),
    ("辣泡菜", "sub_paocai", "primary_sauce", True),
    ("泡菜", "sub_paocai", "primary_sauce", True),
    ("辣油", "sub_layou", "condiment", False),
    ("母馅", "__FILLING_BASE__", "filling_base", True),
    ("包子皮", "baozi_pi", "dough", False),
    ("皮45g", "baozi_pi", "dough", False),
]

DEFAULT_SCENE_KEYWORDS = [
    "炒", "熬", "做", "备", "调", "制作", "酱料", "料头", "炒制", "和馅", "包", "擀", "揉",
]

COMPONENT_TYPE_MAP = {
    "sub_layou": "condiment",
    "sub_paocai": "pickle",
    "wonton_muxian": "filling_base",
    "jiaozi_muxian": "filling_base",
    "baozi_pi": "dough",
}

# 组件级过程禁写（防止 SKU 过程场景串味）
COMPONENT_PROCESS_FORBIDDEN: Dict[str, List[str]] = {
    "sub_chuantong_jiding": ["辣椒面", "二荆条", "子弹头", "小米辣", "三种辣椒", "熬辣油", "淋热油"],
    "sub_douchi_jiang": ["辣椒面", "三种辣椒"],
    "sub_layou": [],  # 辣油本身可写辣椒
}

COMPONENT_SCENE_HINTS: Dict[str, str] = {
    "sub_chuantong_jiding": "制作过程写传统鸡丁肉（鸡胸肉+香菇+豆瓣酱），勿写辣油或辣椒面熬酱",
    "sub_douchi_jiang": "制作过程写豆豉酱炒制，勿混入其他 SKU 的辣油/辣椒面写法",
    "sub_layou": "仅当用户明确说「调辣油/熬辣油」时写本品；若用户说的是某款米线/馄饨的酱料，勿把辣油当主酱",
    "wonton_muxian": "包馄饨场景写母馅调制（挑筋膜、顺一个方向搅），勿写具体克重",
    "jiaozi_muxian": "包饺子场景写母馅调制，勿写具体克重",
    "sub_paocai": "写泡菜腌制过程，强调脆爽酸辣",
}


def is_component_item(item: dict) -> bool:
    code = item.get("product_code", "")
    if code in COMPONENT_EXACT_CODES:
        return True
    return any(code.startswith(p) for p in COMPONENT_CODE_PREFIXES)


def parse_copywriting_facts(text: str) -> dict:
    """解析 legacy copywriting_facts 为结构化 guardrail"""
    guardrail: Dict[str, Any] = {
        "contains": [],
        "excludes": [],
        "forbidden": [],
        "writable_tags": [],
    }
    if not text:
        return guardrail

    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("【"):
            continue
        if line.startswith("含："):
            guardrail["contains"] = _split_items(line[2:])
        elif line.startswith("不含："):
            guardrail["excludes"] = _split_items(line[3:])
        elif line.startswith("不可写："):
            guardrail["forbidden"] = _split_items(line[4:])
        elif line.startswith("可写："):
            guardrail["writable_tags"] = _split_items(line[3:])
    return guardrail


def _split_items(raw: str) -> List[str]:
    return [x.strip() for x in re.split(r"[、，,；;+/]", raw) if x.strip()]


def _ingredient_names(recipe_detail: Optional[dict]) -> List[str]:
    if not recipe_detail or not isinstance(recipe_detail, dict):
        return []
    names: List[str] = []
    for ing in recipe_detail.get("ingredients") or []:
        if not isinstance(ing, dict):
            continue
        name = str(ing.get("name") or "").strip()
        if not name:
            continue
        # 去掉括号内用量说明
        base = re.split(r"[（(]", name)[0].strip()
        if base and base not in names:
            names.append(base)
    return names


def _derive_actions(recipe_detail: Optional[dict]) -> List[str]:
    if not recipe_detail or not isinstance(recipe_detail, dict):
        return ["慢工细活", "私房手工"]
    steps = recipe_detail.get("steps") or []
    actions: List[str] = []
    keywords = ["炒", "熬", "炸", "拌", "腌", "切", "丁", "搅", "包", "擀", "醒", "发酵"]
    for step in steps[:4]:
        step_text = str(step)
        for kw in keywords:
            if kw in step_text and kw not in actions:
                actions.append(kw)
    return actions[:6] or ["慢工细活", "私房手工"]


def build_process_copywriting(
    component_code: str,
    component_name: str,
    guardrail: dict,
    recipe_detail: Optional[dict],
) -> dict:
    """为组件生成过程文案结构"""
    writable = list(guardrail.get("contains") or [])
    for name in _ingredient_names(recipe_detail):
        if name not in writable:
            writable.append(name)

    aliases: List[str] = []
    if "酱" in component_name or "馅" in component_name:
        aliases.extend(["酱料", "料头"])
    if "鸡丁" in component_name:
        aliases.extend(["鸡丁", "鸡丁肉"])
    if "母馅" in component_name:
        aliases.extend(["肉馅", "调馅"])
    if "辣油" in component_name or component_code == "sub_layou":
        aliases.extend(["辣椒油", "红油", "辣油"])

    forbidden = list(COMPONENT_PROCESS_FORBIDDEN.get(component_code, []))
    scene_hint = COMPONENT_SCENE_HINTS.get(
        component_code,
        f"制作过程围绕「{component_name}」，仅使用上方可写配料，勿编造未列出食材",
    )

    return {
        "scene_keywords": DEFAULT_SCENE_KEYWORDS,
        "focus_label": component_name,
        "aliases": list(dict.fromkeys(aliases)),
        "writable_ingredients": writable[:16],
        "writable_actions": _derive_actions(recipe_detail),
        "forbidden_ingredients": forbidden,
        "scene_hint": scene_hint,
    }


def infer_component_type(code: str, name: str) -> str:
    if code in COMPONENT_TYPE_MAP:
        return COMPONENT_TYPE_MAP[code]
    if "母馅" in name or code.endswith("_muxian"):
        return "filling_base"
    if "辣油" in name or code == "sub_layou":
        return "condiment"
    if "泡菜" in name:
        return "pickle"
    if "皮" in name:
        return "dough"
    return "sauce"


def resolve_filling_base_code(category_code: str) -> str:
    if category_code == "jiaozi":
        return "jiaozi_muxian"
    return "wonton_muxian"


def extract_links(pack_formula: str, category_code: str) -> List[dict]:
    """从 pack_formula 解析组件关联"""
    if not pack_formula:
        return []

    links: List[dict] = []
    seen_codes: set[str] = set()
    sort_order = 0

    for keyword, comp_code, role, process_focus in PACK_COMPONENT_RULES:
        if keyword not in pack_formula:
            continue
        resolved_code = comp_code
        if comp_code == "__FILLING_BASE__":
            resolved_code = resolve_filling_base_code(category_code)
        if resolved_code in seen_codes:
            continue
        seen_codes.add(resolved_code)
        links.append(
            {
                "component_code": resolved_code,
                "role": role,
                "process_focus": process_focus,
                "sort_order": sort_order,
            }
        )
        sort_order += 1

    return links


def build_sku_process_copywriting(item: dict, guardrail: dict) -> Optional[dict]:
    """
    对 inline 配方 SKU（如特殊馄饨馅）生成 SKU 级过程文案。
    有 recipe_detail 且未命中标准组件关联时使用。
    """
    recipe = item.get("recipe_detail") or {}
    ingredients = recipe.get("ingredients") or []
    steps = recipe.get("steps") or []
    if not ingredients and not steps:
        return None

    name = item.get("product_name", "")
    writable = list(guardrail.get("contains") or [])
    writable.extend(_ingredient_names(recipe))

    return {
        "scene_keywords": DEFAULT_SCENE_KEYWORDS,
        "focus_label": name,
        "aliases": ["馅料", "料头"],
        "writable_ingredients": list(dict.fromkeys(writable))[:16],
        "writable_actions": _derive_actions(recipe),
        "forbidden_ingredients": [],
        "scene_hint": f"制作过程围绕「{name}」，勿写未列出的配料或克重",
    }


def transform_legacy(items: List[dict]) -> dict:
    components: List[dict] = []
    skus: List[dict] = []
    sku_links: List[dict] = []

    component_items = [i for i in items if is_component_item(i)]
    sku_items = [i for i in items if not is_component_item(i)]

    for item in component_items:
        code = item["product_code"]
        guardrail = parse_copywriting_facts(item.get("copywriting_facts") or "")
        recipe = item.get("recipe_detail")
        components.append(
            {
                "component_code": code,
                "component_name": item.get("product_name", code),
                "component_type": infer_component_type(code, item.get("product_name", "")),
                "aliases": item.get("aliases") or [],
                "pack_formula": item.get("pack_formula"),
                "recipe_detail": recipe,
                "guardrail": guardrail,
                "process_copywriting": build_process_copywriting(
                    code,
                    item.get("product_name", code),
                    guardrail,
                    recipe,
                ),
                "source_version": item.get("source_version", "2026-01"),
                "status": int(item.get("status", 1)),
                "sort_order": int(item.get("sort_order", 0)),
            }
        )

    for item in sku_items:
        code = item["product_code"]
        guardrail = parse_copywriting_facts(item.get("copywriting_facts") or "")
        links = extract_links(item.get("pack_formula") or "", item.get("category_code", ""))

        sku_entry = {
            "sku_code": code,
            "sku_name": item.get("product_name", code),
            "category_code": item.get("category_code", "other"),
            "category_name": item.get("category_name", "其他"),
            "aliases": item.get("aliases") or [],
            "pack_formula": item.get("pack_formula"),
            "guardrail": guardrail,
            "process_copywriting": None,
            "source_version": item.get("source_version", "2026-01"),
            "status": int(item.get("status", 1)),
            "sort_order": int(item.get("sort_order", 0)),
        }

        # inline 配方：无组件关联但有 recipe_detail
        if not links:
            inline_process = build_sku_process_copywriting(item, guardrail)
            if inline_process:
                sku_entry["process_copywriting"] = inline_process

        skus.append(sku_entry)

        for link in links:
            sku_links.append(
                {
                    "sku_code": code,
                    "component_code": link["component_code"],
                    "role": link["role"],
                    "process_focus": link["process_focus"],
                    "sort_order": link["sort_order"],
                }
            )

    return {
        "version": "2026-v2",
        "source_version": "2026-01",
        "components": components,
        "skus": skus,
        "sku_component_links": sku_links,
    }


def main():
    if not LEGACY_FILE.exists():
        raise FileNotFoundError(f"Legacy 文件不存在: {LEGACY_FILE}")

    with open(LEGACY_FILE, "r", encoding="utf-8") as f:
        legacy = json.load(f)

    result = transform_legacy(legacy)
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(
        f"转换完成: components={len(result['components'])}, "
        f"skus={len(result['skus'])}, links={len(result['sku_component_links'])}"
    )
    print(f"输出: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
