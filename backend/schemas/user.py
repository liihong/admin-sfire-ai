"""
User Pydantic Schemas
兼容前端 User namespace 定义
"""
from datetime import datetime
from decimal import Decimal
from typing import Optional, List, Literal
from pydantic import BaseModel, Field, EmailStr

from .common import PageParams


# 用户等级类型（与前端兼容）
# 注意：已废弃，保留仅为兼容性。实际应使用 level_code 字段（str类型）
# 包含所有可能的等级代码值：normal/vip/svip/max
LevelType = Literal["normal", "vip", "svip", "max"]
LevelIntType = Literal[0, 1, 2]


class ComputePower(BaseModel):
    """算力明细"""
    balance: Decimal = Field(default=Decimal("0"), description="当前剩余可用算力")
    frozen: Decimal = Field(default=Decimal("0"), description="冻结算力")
    totalConsumed: Decimal = Field(default=Decimal("0"), description="历史累计消耗")
    totalRecharged: Decimal = Field(default=Decimal("0"), description="历史累计充值")
    lastRechargeTime: Optional[str] = Field(None, description="最后充值时间")


class UserBase(BaseModel):
    """用户基础信息"""
    username: str = Field(..., min_length=2, max_length=64, description="用户名")
    phone: Optional[str] = Field(None, max_length=20, description="手机号")
    nickname: Optional[str] = Field(None, max_length=64, description="昵称")
    avatar: Optional[str] = Field(None, description="头像URL")
    level: LevelType = Field(default="normal", description="用户等级（已废弃，请使用level_code）")
    level_code: Optional[str] = Field(None, description="用户等级代码（normal/vip/svip/max），对应user_levels表的code字段")
    remark: Optional[str] = Field(None, description="备注")


class UserCreate(UserBase):
    """创建用户请求"""
    password: str = Field(..., min_length=6, max_length=50, description="密码")
    parent_id: Optional[int] = Field(None, description="上级用户ID")
    vip_expire_date: Optional[str] = Field(None, description="VIP到期时间（YYYY-MM-DD格式，可选，仅VIP等级有效）")


class UserUpdate(BaseModel):
    """更新用户请求"""
    username: Optional[str] = Field(None, min_length=2, max_length=64)
    phone: Optional[str] = Field(None, max_length=20)
    nickname: Optional[str] = Field(None, max_length=64)
    avatar: Optional[str] = None
    level: Optional[str] = Field(None, description="用户等级代码（normal/vip/svip/max），已废弃，请使用level_code")
    level_code: Optional[str] = Field(None, description="用户等级代码（normal/vip/svip/max），对应user_levels表的code字段")
    vip_expire_date: Optional[str] = Field(None, description="VIP到期时间（YYYY-MM-DD格式，可选，仅VIP等级有效）")
    is_active: Optional[bool] = None
    remark: Optional[str] = None


class UserResponse(BaseModel):
    """
    用户响应
    对应前端 User.ResUserList
    """
    id: str = Field(..., description="用户ID")
    username: str = Field(..., description="用户名")
    phone: Optional[str] = Field(None, description="手机号")
    nickname: Optional[str] = Field(None, description="昵称")
    avatar: Optional[str] = Field(None, description="头像")
    level: LevelIntType = Field(..., description="用户等级: 0-普通, 1-会员, 2-合伙人")
    levelCode: Optional[str] = Field(None, description="等级代码（normal/vip/svip/max）")
    levelName: Optional[str] = Field(None, description="等级名称（中文）")
    computePower: ComputePower = Field(..., description="算力明细")
    role: str = Field(default="user", description="角色")
    inviteCode: Optional[str] = Field(None, description="邀请码")
    inviterId: Optional[str] = Field(None, description="邀请人ID")
    inviterName: Optional[str] = Field(None, description="邀请人名称")
    createTime: str = Field(..., description="创建时间")
    lastLoginTime: Optional[str] = Field(None, description="最后登录时间（对应数据库 updated_at 字段）")
    status: int = Field(..., description="状态: 1-正常, 0-封禁")

    class Config:
        from_attributes = True


class UserListResponse(BaseModel):
    """用户列表响应"""
    list: List[UserResponse] = Field(..., description="用户列表")
    pageNum: int = Field(..., description="当前页码")
    pageSize: int = Field(..., description="每页数量")
    total: int = Field(..., description="总数量")


class UserQueryParams(PageParams):
    """用户查询参数"""
    username: Optional[str] = Field(None, description="用户名")
    phone: Optional[str] = Field(None, description="手机号")
    level: Optional[str] = Field(None, description="用户等级（支持level_code: normal/vip/svip/max 或旧的level枚举）")
    is_active: Optional[bool] = Field(None, description="是否激活")
    minBalance: Optional[Decimal] = Field(None, description="最小算力余额")
    maxBalance: Optional[Decimal] = Field(None, description="最大算力余额")


class LoginRequest(BaseModel):
    """登录请求"""
    username: str = Field(..., description="用户名")
    password: str = Field(..., description="密码")


class LoginResponse(BaseModel):
    """
    登录响应
    对应前端 Login.ResLogin
    """
    access_token: str = Field(..., description="访问令牌")


class RechargeRequest(BaseModel):
    """充值请求"""
    userId: str = Field(..., description="用户ID")
    amount: Decimal = Field(..., gt=0, description="充值金额")
    remark: Optional[str] = Field(None, description="备注")


class DeductRequest(BaseModel):
    """扣费请求"""
    userId: str = Field(..., description="用户ID")
    amount: Decimal = Field(..., gt=0, description="扣费金额")
    reason: str = Field(..., description="扣费原因")


class ChangeLevelRequest(BaseModel):
    """修改用户等级请求"""
    userId: str = Field(..., description="用户ID")
    level: str = Field(..., description="等级代码：normal/vip/svip/max")
    vip_expire_date: Optional[str] = Field(None, description="VIP到期时间（YYYY-MM-DD格式，可选）")
    remark: Optional[str] = Field(None, description="备注")
