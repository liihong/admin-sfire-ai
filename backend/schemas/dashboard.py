"""
Dashboard Statistics Schema
Dashboard 统计数据结构定义
"""
from typing import List, Optional
from pydantic import BaseModel, Field
from decimal import Decimal


class OverviewStats(BaseModel):
    """
    概览统计数据
    
    Attributes:
        total_users: 总用户数
        new_users_today: 今日新增用户
        active_users_today: 今日活跃用户（根据最后登录时间）
        total_balance: 平台总算力余额
    """
    total_users: int = Field(0, description="总用户数")
    new_users_today: int = Field(0, description="今日新增用户")
    active_users_today: int = Field(0, description="今日活跃用户")
    total_balance: Decimal = Field(Decimal("0.0000"), description="平台总算力余额")


class ApiMonitoringStats(BaseModel):
    """
    API 监控统计数据
    
    Attributes:
        tikhub_balance: Tikhub 账户余额
        openai_balance: OpenAI 账户余额
        today_cost: 今日已消耗成本
        today_api_calls: 今日 API 调用次数
    """
    tikhub_balance: Optional[Decimal] = Field(None, description="Tikhub 账户余额")
    openai_balance: Optional[Decimal] = Field(None, description="OpenAI 账户余额")
    today_cost: Decimal = Field(Decimal("0.0000"), description="今日已消耗成本")
    today_api_calls: int = Field(0, description="今日 API 调用次数")


class UserTrendItem(BaseModel):
    """
    用户趋势数据项
    
    Attributes:
        date: 日期 (YYYY-MM-DD)
        count: 新增用户数
    """
    date: str = Field(..., description="日期")
    count: int = Field(0, description="新增用户数")


class CallTrendItem(BaseModel):
    """
    API 调用趋势数据项
    
    Attributes:
        hour: 时间点 (HH:00)
        count: 调用次数
    """
    hour: str = Field(..., description="时间点")
    count: int = Field(0, description="调用次数")


class ChartStats(BaseModel):
    """
    图表统计数据
    
    Attributes:
        user_trend: 过去 7 天每天的新增用户数
        call_trend: 过去 24 小时每小时的 API 请求数
    """
    user_trend: List[UserTrendItem] = Field(default_factory=list, description="用户趋势")
    call_trend: List[CallTrendItem] = Field(default_factory=list, description="调用趋势")


class AbnormalUserRecord(BaseModel):
    """
    异常用户记录
    
    Attributes:
        user_id: 用户 ID
        call_count: 调用次数
        endpoint: 触发异常的接口路径
        ip_address: 客户端 IP 地址
        reason: 异常原因
        detected_at: 检测时间
    """
    user_id: int = Field(..., description="用户 ID")
    call_count: int = Field(..., description="调用次数")
    endpoint: str = Field("", description="触发异常的接口路径")
    ip_address: str = Field("", description="客户端 IP 地址")
    reason: str = Field("", description="异常原因")
    detected_at: str = Field("", description="检测时间")
    timestamp: Optional[int] = Field(None, description="时间戳")


class DashboardStats(BaseModel):
    """
    Dashboard 完整统计数据
    
    Attributes:
        overview: 概览统计
        api_monitoring: API 监控
        charts: 图表数据
        abnormal_users: 最近异常用户列表
    """
    overview: OverviewStats = Field(default_factory=OverviewStats, description="概览统计")
    api_monitoring: ApiMonitoringStats = Field(default_factory=ApiMonitoringStats, description="API 监控")
    charts: ChartStats = Field(default_factory=ChartStats, description="图表数据")
    abnormal_users: List[AbnormalUserRecord] = Field(default_factory=list, description="最近异常用户列表")


class AgentRankItem(BaseModel):
    """
    智能体调用排行数据项

    Attributes:
        id: 智能体 ID
        name: 智能体名���
        icon: 智能体图标
        call_count: 调用次数
    """
    id: str = Field(..., description="智能体 ID")
    name: str = Field(..., description="智能体名称")
    icon: str = Field(..., description="智能体图标")
    call_count: int = Field(..., description="调用次数")


class DashboardStatsResponse(BaseModel):
    """Dashboard 统计响应"""
    code: int = 200
    data: DashboardStats
    msg: str = "获取成功"

