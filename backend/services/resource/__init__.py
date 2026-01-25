"""
资源管理领域服务模块
包含项目、横幅、LLM模型、算力统计等服务
"""
from .project import ProjectService
from .banner import BannerService
from .llm_model import LLMModelService
from .compute import ComputeService
from .quick_entry import QuickEntryService

__all__ = [
    "ProjectService",
    "BannerService",
    "LLMModelService",
    "ComputeService",
    "QuickEntryService",
]



