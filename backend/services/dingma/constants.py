"""
顶妈知识库常量
"""
from enum import Enum


class KnowledgeInjectMode(str, Enum):
    """知识注入模式（与 knowledge.py 保持一致，向后兼容）"""

    COPYWRITING = "copywriting"
    AFTER_SALES = "after_sales"


# 知识块 appendix 说明
KNOWLEDGE_APPENDIX_HEADER = """【后台参考·成分护栏】
以下仅供核对，默认不要写进朋友圈/口播正文：
- 不要出现「顶妈」品牌名（除非用户明确要求）
- 不要向用户解释规则、产品事实或母馅等后台信息
- 以学员/店主第一人称写生活场景，智能体技能中的写法须服从本段事实约束"""

KNOWLEDGE_GUARDRAIL_LINE = (
    "正文一旦出现具体食材/酱料/配料名称，只能使用下方对应项已有内容，"
    "禁止编造未列出项；不写克重配比；制作过程场景须遵循「过程可写/过程禁写」。"
)

KNOWLEDGE_SCENE_HINT = (
    "未匹配到具体 SKU，可正常写场景文案；不要编造任何具体产品配料、酱料或功效。"
)

DEFAULT_MAX_MATCHES = 3
MAX_MERGED_CONTAINS_ITEMS = 16
DINGMA_TENANT_CODE = "dingma"

# 向后兼容旧名称
KNOWLEDGE_IRON_RULE = KNOWLEDGE_GUARDRAIL_LINE
KNOWLEDGE_IRON_RULE_SCENE = KNOWLEDGE_SCENE_HINT
KNOWLEDGE_CATEGORY_SCENE_HINT = (
    "用户可能在描述品类生活场景，写到具体配料时必须来自下方白名单，不可自造。"
)
