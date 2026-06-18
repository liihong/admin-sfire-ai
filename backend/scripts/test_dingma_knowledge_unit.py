"""
顶妈知识库 v2 匹配逻辑单元测试（不依赖数据库）

执行：cd backend && python -m scripts.test_dingma_knowledge_unit
"""
from models.dingma_knowledge import (
    DingmaKnowledgeComponent,
    DingmaKnowledgeSku,
    DingmaSkuComponentLink,
)
from services.dingma.knowledge import (
    CopywritingScene,
    DingmaKnowledgeService,
)


def _make_component(
    code: str,
    name: str,
    aliases=None,
    process_copywriting=None,
    guardrail=None,
):
    c = DingmaKnowledgeComponent()
    c.id = hash(code) % 100000
    c.component_code = code
    c.component_name = name
    c.aliases = aliases or []
    c.guardrail = guardrail or {"contains": ["测试配料"], "forbidden": ["治疗"]}
    c.process_copywriting = process_copywriting or {
        "scene_hint": f"写{name}过程",
        "writable_ingredients": ["测试配料"],
        "forbidden_ingredients": ["辣椒面"],
    }
    c.status = 1
    return c


def _make_sku(code, name, aliases=None, guardrail=None, links=None):
    s = DingmaKnowledgeSku()
    s.id = hash(code) % 100000
    s.sku_code = code
    s.sku_name = name
    s.category_code = "mixian"
    s.category_name = "米线"
    s.aliases = aliases or []
    s.guardrail = guardrail or {
        "contains": ["米线", "传统鸡丁肉", "辣油"],
        "excludes": ["海鲜"],
        "forbidden": ["治疗"],
    }
    s.component_links = links or []
    s.status = 1
    return s


def test_detect_process_scene():
    assert DingmaKnowledgeService.detect_scene("今天在家炒鸡丁米线的酱料") == CopywritingScene.PROCESS
    assert DingmaKnowledgeService.detect_scene("鸡丁米线好评又来啦") == CopywritingScene.GENERAL


def test_match_sku_by_alias():
    skus = [_make_sku("mixian_jiding", "传统鸡丁米线", ["鸡丁米线"])]
    matches = DingmaKnowledgeService._match_skus("鸡丁米线文案", skus)
    assert len(matches) == 1
    assert matches[0].sku.sku_name == "传统鸡丁米线"


def test_process_block_includes_focus_component():
    comp = _make_component(
        "sub_chuantong_jiding",
        "传统鸡丁肉",
        process_copywriting={
            "scene_hint": "写鸡丁香菇炒制，勿写辣油",
            "writable_ingredients": ["鸡胸肉", "香菇丁", "豆瓣酱"],
            "forbidden_ingredients": ["辣椒面", "二荆条"],
        },
    )
    link = DingmaSkuComponentLink()
    link.process_focus = True
    link.role = "primary_sauce"
    link.component = comp
    link.sort_order = 0

    sku = _make_sku("mixian_jiding", "传统鸡丁米线", ["鸡丁米线"], links=[link])
    matches = DingmaKnowledgeService._match_skus("今天在家炒鸡丁米线的酱料", [sku])
    assert len(matches) == 1
    block = DingmaKnowledgeService._format_sku_process_block(matches)
    assert "传统鸡丁肉" in block
    assert "鸡胸肉" in block
    assert "辣椒面" in block
    assert "勿写辣油" in block


def test_general_block_no_process_detail():
    sku = _make_sku("mixian_jiding", "传统鸡丁米线")
    block = DingmaKnowledgeService._format_sku_general_block(
        [DingmaKnowledgeService._match_skus("传统鸡丁米线", [sku])[0]]
    )
    assert "含：" in block
    assert "过程可写配料" not in block


def test_category_match():
    skus = [
        _make_sku("w1", "香菜馄饨", guardrail={"contains": ["馄饨"], "forbidden": ["治疗"]}),
        _make_sku("m1", "泡菜朝鲜面", guardrail={"contains": ["朝鲜面"], "forbidden": ["治疗"]}),
    ]
    skus[0].category_name = "馄饨"
    skus[0].category_code = "wonton"
    cats = DingmaKnowledgeService._match_categories("在家包馄饨", skus)
    assert len(cats) == 1
    assert cats[0].category_name == "馄饨"


def test_append_knowledge_order():
    agent = "你是朋友圈文案助手"
    kb = "【后台参考·成分护栏】测试"
    merged = DingmaKnowledgeService.append_knowledge(agent, kb)
    assert merged.index(agent) < merged.index(kb)


if __name__ == "__main__":
    test_detect_process_scene()
    test_match_sku_by_alias()
    test_process_block_includes_focus_component()
    test_general_block_no_process_detail()
    test_category_match()
    test_append_knowledge_order()
    print("All knowledge v2 unit tests passed.")
