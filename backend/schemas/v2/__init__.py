"""
v2版本 Schemas
支持技能组装模式
"""
from .skill import (
    SkillBase,
    SkillCreate,
    SkillUpdate,
    SkillResponse,
    SkillListResponse,
    SkillCategoryResponse,
    SkillQueryParams,
)
from .agent import (
    AgentConfigV2,
    AgentCreateV2,
    AgentUpdateV2,
    AgentResponseV2,
    AgentListResponseV2,
    PromptPreviewRequest,
    PromptPreviewResponse,
    AgentExecuteRequest,
    AgentExecuteResponse,
    AgentQueryParamsV2,
    AgentMode,
)

__all__ = [
    # Skill相关
    "SkillBase",
    "SkillCreate",
    "SkillUpdate",
    "SkillResponse",
    "SkillListResponse",
    "SkillCategoryResponse",
    "SkillQueryParams",
    # Agent相关
    "AgentConfigV2",
    "AgentCreateV2",
    "AgentUpdateV2",
    "AgentResponseV2",
    "AgentListResponseV2",
    "PromptPreviewRequest",
    "PromptPreviewResponse",
    "AgentExecuteRequest",
    "AgentExecuteResponse",
    "AgentQueryParamsV2",
    "AgentMode",
]
