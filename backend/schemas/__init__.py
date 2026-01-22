"""
Pydantic Schemas module
"""
from .common import (
    PageParams,
    Token,
    TokenData,
)
from .user import (
    UserCreate,
    UserUpdate,
    UserResponse,
    UserListResponse,
    ComputePower,
    LoginRequest,
    LoginResponse,
)
from .dashboard import (
    DashboardStats,
    OverviewStats,
    ApiMonitoringStats,
    ChartStats,
    UserTrendItem,
    CallTrendItem,
    AbnormalUserRecord,
    DashboardStatsResponse,
)
from .menu import (
    MenuMeta,
    MenuResponse,
    MenuCreate,
    MenuUpdate,
    MenuListItem,
)
from .conversation import (
    ConversationCreate,
    ConversationUpdate,
    ConversationResponse,
    ConversationDetailResponse,
    ConversationListParams,
    ConversationMessageCreate,
    ConversationMessageResponse,
    ConversationChunkResponse,
)
from .dictionary import (
    DictBase,
    DictCreate,
    DictUpdate,
    DictResponse,
    DictWithItemsResponse,
    DictQueryParams,
    DictItemBase,
    DictItemCreate,
    DictItemUpdate,
    DictItemResponse,
    DictItemSimple,
    DictItemQueryParams,
)
from .agent import v2 as agent_v2  # v2版本Schema命名空间

__all__ = [
    # Common
    "PageParams",
    "Token",
    "TokenData",
    # User
    "UserCreate",
    "UserUpdate",
    "UserResponse",
    "UserListResponse",
    "ComputePower",
    "LoginRequest",
    "LoginResponse",
    # Dashboard
    "DashboardStats",
    "OverviewStats",
    "ApiMonitoringStats",
    "ChartStats",
    "UserTrendItem",
    "CallTrendItem",
    "AbnormalUserRecord",
    "DashboardStatsResponse",
    # Menu
    "MenuMeta",
    "MenuResponse",
    "MenuCreate",
    "MenuUpdate",
    "MenuListItem",
    # Conversation
    "ConversationCreate",
    "ConversationUpdate",
    "ConversationResponse",
    "ConversationDetailResponse",
    "ConversationListParams",
    "ConversationMessageCreate",
    "ConversationMessageResponse",
    "ConversationChunkResponse",
    # Dictionary
    "DictBase",
    "DictCreate",
    "DictUpdate",
    "DictResponse",
    "DictWithItemsResponse",
    "DictQueryParams",
    "DictItemBase",
    "DictItemCreate",
    "DictItemUpdate",
    "DictItemResponse",
    "DictItemSimple",
    "DictItemQueryParams",
    # Agent v2
    "agent_v2",
]


