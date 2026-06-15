"""
顶妈（dingma）知识库常量
"""
from enum import Enum


class KnowledgeInjectMode(str, Enum):
    """知识库注入模式"""

    COPYWRITING = "copywriting"
    AFTER_SALES = "after_sales"


# 文案智能体铁律（prepend 到知识块顶部）
KNOWLEDGE_IRON_RULE = """【产品事实铁律 - 最高优先级】
1. 你只能使用下方【产品事实】中列出的配料、组件、卖点与限制。
2. 禁止添加未列出的食材、配料、功效、工艺、价格或对比结论。
3. 文案中不要求写精确克重，但不得编造成分。
4. 若未匹配到具体产品，不要编造产品细节，应引导用户补充产品名称。"""

# 默认最大匹配产品数
DEFAULT_MAX_MATCHES = 3

# dingma 租户代码（seed / 查询用）
DINGMA_TENANT_CODE = "dingma"
