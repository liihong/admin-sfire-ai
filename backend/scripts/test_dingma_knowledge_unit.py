"""
顶妈知识库匹配逻辑单元测试（不依赖数据库）

执行：cd backend && python -m scripts.test_dingma_knowledge_unit
"""
from models.dingma_product_knowledge import DingmaProductKnowledge
from services.dingma.knowledge import DingmaKnowledgeService


def _make_product(code: str, name: str, aliases=None, facts: str = ""):
    p = DingmaProductKnowledge()
    p.product_code = code
    p.product_name = name
    p.aliases = aliases or []
    p.copywriting_facts = facts or f"【{name}】\n含：测试配料"
    p.category_name = "米线"
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
    assert "番茄牛肉米线" in block
    assert "产品事实铁律" in block
    print("OK test_no_match_index_format")


if __name__ == "__main__":
    test_match_single_product()
    test_match_alias()
    test_no_match_index_format()
    print("All knowledge unit tests passed.")
