"""
顶妈（dingma）知识库常量
"""
from enum import Enum


class KnowledgeInjectMode(str, Enum):
    """知识库注入模式"""

    COPYWRITING = "copywriting"
    AFTER_SALES = "after_sales"


# 知识块 appendix 说明（append 在智能体技能之后，作后台护栏）
KNOWLEDGE_APPENDIX_HEADER = """【后台参考·成分护栏】
以下仅供核对，默认不要写进朋友圈/口播正文：
- 不要出现「顶妈」品牌名（除非用户明确要求）
- 不要向用户解释规则、产品事实或母馅等后台信息
- 以学员/店主第一人称写生活场景，智能体技能中的写法优先于本段"""

# 极短护栏（与 appendix 配套，一行）
KNOWLEDGE_GUARDRAIL_LINE = (
    "正文一旦出现具体食材/酱料/配料名称，只能使用下方对应项「含」中已有内容，"
    "禁止编造猪油、鸡蛋、豆芽、火腿肠等未列出项；不写克重配比，其余场景可自由发挥。"
)

# 品类场景补充说明
KNOWLEDGE_CATEGORY_SCENE_HINT = (
    "用户可能在描述品类生活场景（如在家包馄饨、顺便备货），优先写场景与情绪，"
    "不必罗列产品全名或克重；但若正文写到具体食材/酱料，必须来自下方「含」，不可自造。"
)

# 场景模式（未命中品类/SKU）
KNOWLEDGE_SCENE_HINT = (
    "未匹配到具体 SKU，可正常写场景文案；不要编造任何具体产品配料、酱料或功效。"
)

# IP 人设「主要产品」触发的补充护栏说明
KNOWLEDGE_PERSONA_PRODUCT_HINT = (
    "以下为 IP 主营品类护栏（用户未点名但正文可能顺带提到时同样适用，写到具体配料须核对）。"
)

# 人设主营品类最多注入条数
MAX_PERSONA_CATEGORY_GUARD = 2

# 原料/子配方：文案智能体品类模式下不注入（售后模式仍可用）
INGREDIENT_PRODUCT_CODE_PREFIXES = ("sub_",)
INGREDIENT_PRODUCT_CODE_SUFFIXES = ("_muxian",)  # 如 wonton_muxian、jiaozi_muxian
INGREDIENT_NAME_KEYWORDS = ("母馅",)

# 单品匹配默认最多条数
DEFAULT_MAX_MATCHES = 3

# 品类匹配时成品名称列表上限
DEFAULT_CATEGORY_MAX_MATCHES = 12

# 品类合并「含」展示上限（防止 prompt 过长）
MAX_MERGED_CONTAINS_ITEMS = 16

# dingma 租户代码（seed / 查询用）
DINGMA_TENANT_CODE = "dingma"

# 向后兼容：旧代码若仍引用下列名称，映射到新 appendix 语义
KNOWLEDGE_IRON_RULE = KNOWLEDGE_GUARDRAIL_LINE
KNOWLEDGE_IRON_RULE_CATEGORY = KNOWLEDGE_CATEGORY_SCENE_HINT
KNOWLEDGE_IRON_RULE_SCENE = KNOWLEDGE_SCENE_HINT
