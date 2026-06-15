"""
顶妈知识库匹配逻辑单元测试（不依赖数据库）

执行：cd backend && python -m scripts.test_dingma_knowledge_unit
"""
from models.dingma_product_knowledge import DingmaProductKnowledge
from services.dingma.knowledge import DingmaKnowledgeService


def _make_product(
    code: str,
    name: str,
    aliases=None,
    facts: str = "",
    category_name: str = "米线",
    category_code: str = "mixian",
):
    p = DingmaProductKnowledge()
    p.product_code = code
    p.product_name = name
    p.aliases = aliases or []
    p.copywriting_facts = facts or f"【{name}】\n含：测试配料\n不可写：治疗、药用"
    p.category_name = category_name
    p.category_code = category_code
    p.status = 1
    return p


def test_match_single_product():
    products = [
        _make_product("mixian_paocai", "泡菜朝鲜面", ["朝鲜面", "泡菜面"]),
        _make_product("mixian_fanqie", "番茄牛肉米线", ["番茄米线"]),
    ]
    matches = DingmaKnowledgeService._match_products(
        "帮我写泡菜朝鲜面的朋友圈", products, max_matches=3
    )
    assert len(matches) == 1
    assert matches[0].product.product_name == "泡菜朝鲜面"
    print("OK test_match_single_product")


def test_match_alias():
    products = [_make_product("mixian_paocai", "泡菜朝鲜面", ["朝鲜面"])]
    matches = DingmaKnowledgeService._match_products("朝鲜面文案", products)
    assert matches[0].product.product_name == "泡菜朝鲜面"
    print("OK test_match_alias")


def test_no_match_index_format():
    products = [
        _make_product("a", "泡菜朝鲜面"),
        _make_product("b", "番茄牛肉米线"),
    ]
    block = DingmaKnowledgeService._format_product_index(products)
    assert "泡菜朝鲜面" in block
    assert "后台参考" in block
    assert "顶妈" in block  # 要求不要出现品牌名
    print("OK test_no_match_index_format")


def test_match_category_wonton_excludes_muxian():
    """「在家包馄饨」命中品类，且排除母馅"""
    products = [
        _make_product(
            "wonton_muxian",
            "馄饨馅（母馅）",
            category_name="馄饨",
            category_code="wonton",
        ),
        _make_product("wonton_xiangcai", "香菜馄饨", category_name="馄饨", category_code="wonton"),
        _make_product("wonton_xianggu", "香菇馄饨", category_name="馄饨", category_code="wonton"),
        _make_product("m1", "泡菜朝鲜面", category_name="米线", category_code="mixian"),
    ]
    cat = DingmaKnowledgeService._match_category("我在家包馄饨给我3条朋友圈文案", products)
    assert cat is not None
    assert cat.category_name == "馄饨"
    assert len(cat.products) == 2
    assert all(not DingmaKnowledgeService.is_ingredient_product(p) for p in cat.products)

    block = DingmaKnowledgeService._format_category_copywriting_block(cat)
    assert "品类" in block
    assert "香菜馄饨" in block
    assert "馄饨馅（母馅）" not in block
    assert "仅可使用" in block
    assert "可写：" not in block  # 不再注入全文 copywriting_facts
    assert "后台参考" in block
    print("OK test_match_category_wonton_excludes_muxian")


def test_prefer_category_over_ingredient_sku():
    """原料 SKU 名含「馄饨」时，应改走品类护栏而非母馅提示"""
    products = [
        _make_product("wonton_muxian", "馄饨", category_name="馄饨", category_code="wonton"),
        _make_product("wonton_xiangcai", "香菜馄饨", category_name="馄饨", category_code="wonton"),
        _make_product(
            "mixian_paocai",
            "泡菜朝鲜面",
            category_name="米线",
            category_code="mixian",
            facts="【泡菜朝鲜面】\n含：朝鲜面、泡菜\n不含：海鲜\n不可写：治疗、药用",
        ),
    ]
    user_input = "今天我在家包馄饨，给我2条朋友圈文案"
    all_matches = DingmaKnowledgeService._match_products(user_input, products)
    assert len(all_matches) == 1
    assert DingmaKnowledgeService.is_ingredient_product(all_matches[0].product)

    match_pool = DingmaKnowledgeService.filter_consumer_products(products)
    assert DingmaKnowledgeService._should_prefer_category_over_ingredient_matches(
        user_input, all_matches, match_pool
    )

    cat = DingmaKnowledgeService._match_category(user_input, match_pool)
    block = DingmaKnowledgeService._format_category_copywriting_block(cat)
    assert "香菜馄饨" in block
    assert "勿把原料配比写进朋友圈" not in block
    assert "仅可使用" in block
    print("OK test_prefer_category_over_ingredient_sku")


def test_persona_injects_mixian_guard_when_user_says_wonton():
    """用户只提馄饨，IP 主营含米线时，补充米线品类护栏"""
    products = [
        _make_product("wonton_xiangcai", "香菜馄饨", category_name="馄饨", category_code="wonton"),
        _make_product(
            "mixian_paocai",
            "泡菜朝鲜面",
            category_name="米线",
            category_code="mixian",
            facts="【泡菜朝鲜面】\n含：朝鲜面、泡菜、豆皮\n不含：海鲜\n不可写：治疗、药用",
        ),
        _make_product(
            "mixian_fanqie",
            "番茄牛肉米线",
            category_name="米线",
            category_code="mixian",
            facts="【番茄牛肉米线】\n含：米线、豆皮、番茄牛肉酱\n不含：泡菜\n不可写：治疗、药用",
        ),
    ]
    persona = "## 主要产品\n主打鲜肉馄饨，米线，新中式馒头\n"
    wonton_cat = DingmaKnowledgeService._match_category("在家包馄饨", products)
    extra = DingmaKnowledgeService._resolve_persona_categories(
        persona, products, exclude_names=[wonton_cat.category_name]
    )
    assert len(extra) == 1
    assert extra[0].category_name == "米线"

    block = DingmaKnowledgeService._format_category_copywriting_block(
        wonton_cat, extra_categories=extra
    )
    assert "IP 主营·米线" in block
    assert "豆皮" in block
    assert "禁止编造未列出项" in block
    print("OK test_persona_injects_mixian_guard_when_user_says_wonton")


def test_extract_main_product_terms():
    persona = "## 主要产品\n主打鲜肉馄饨，米线，新中式馒头\n\n## 语气风格\n专业亲和"
    terms = DingmaKnowledgeService._extract_main_product_terms(persona)
    assert "米线" in terms
    assert "主打鲜肉馄饨" in terms
    print("OK test_extract_main_product_terms")


def test_strip_dingma_prefix_for_sku():
    products = [
        _make_product("wonton_xianggu", "香菇馄饨", category_name="馄饨", category_code="wonton"),
    ]
    matches = DingmaKnowledgeService._match_products("顶妈香菇馄饨", products)
    assert len(matches) == 1
    assert matches[0].product.product_name == "香菇馄饨"
    print("OK test_strip_dingma_prefix_for_sku")


def test_append_knowledge_order():
    agent = "你是朋友圈文案助手，用第一人称。"
    kb = "【后台参考·成分护栏】测试"
    merged = DingmaKnowledgeService.append_knowledge(agent, kb)
    assert merged.index(agent) < merged.index(kb)
    print("OK test_append_knowledge_order")


def test_merge_prioritizes_agent():
    agent = "A" * 5000
    kb = "B" * 8000
    merged = DingmaKnowledgeService.merge_with_knowledge_guard(agent, kb, max_total_length=6000)
    assert merged.startswith("A" * 100)
    assert "B" in merged
    assert len(merged) <= 6000
    print("OK test_merge_prioritizes_agent")


if __name__ == "__main__":
    test_match_single_product()
    test_match_alias()
    test_no_match_index_format()
    test_match_category_wonton_excludes_muxian()
    test_prefer_category_over_ingredient_sku()
    test_persona_injects_mixian_guard_when_user_says_wonton()
    test_extract_main_product_terms()
    test_strip_dingma_prefix_for_sku()
    test_append_knowledge_order()
    test_merge_prioritizes_agent()
    print("All knowledge unit tests passed.")
