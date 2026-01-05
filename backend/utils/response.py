"""
Unified Response Format for Geeker-Admin Compatibility
统一响应格式，确保与 Geeker-Admin 前端兼容
"""
from typing import Any, Generic, TypeVar, Optional, List
from pydantic import BaseModel

T = TypeVar("T")


class Response(BaseModel, Generic[T]):
    """
    统一响应格式
    
    格式: {"code": 200, "data": ..., "msg": "..."}
    
    Attributes:
        code: 状态码 (200=成功, 400=参数错误, 401=未授权, 403=禁止, 404=不存在, 500=服务器错误)
        data: 响应数据
        msg: 响应消息
    """
    code: int = 200
    data: Optional[T] = None
    msg: str = "操作成功"

    class Config:
        json_schema_extra = {
            "example": {
                "code": 200,
                "data": None,
                "msg": "操作成功"
            }
        }


class PageData(BaseModel, Generic[T]):
    """
    分页数据结构
    
    Attributes:
        list: 数据列表
        pageNum: 当前页码
        pageSize: 每页数量
        total: 总数量
    """
    list: List[T] = []
    pageNum: int = 1
    pageSize: int = 10
    total: int = 0


class PageResponse(BaseModel, Generic[T]):
    """
    分页响应格式
    
    Attributes:
        code: 状态码
        data: 分页数据
        msg: 响应消息
    """
    code: int = 200
    data: PageData[T]
    msg: str = "操作成功"


def success(
    data: Any = None,
    msg: str = "操作成功",
    code: int = 200
) -> dict:
    """
    返回成功响应
    
    Args:
        data: 响应数据
        msg: 响应消息
        code: 状态码
    
    Returns:
        统一格式的响应字典
    """
    return {
        "code": code,
        "data": data,
        "msg": msg
    }


def fail(
    msg: str = "操作失败",
    code: int = 400,
    data: Any = None
) -> dict:
    """
    返回失败响应
    
    Args:
        msg: 错误消息
        code: 状态码
        data: 附加数据
    
    Returns:
        统一格式的响应字典
    """
    return {
        "code": code,
        "data": data,
        "msg": msg
    }


def page_response(
    items: List[Any],
    total: int,
    page_num: int = 1,
    page_size: int = 10,
    msg: str = "操作成功"
) -> dict:
    """
    返回分页响应
    
    Args:
        items: 数据列表
        total: 总数量
        page_num: 当前页码
        page_size: 每页数量
        msg: 响应消息
    
    Returns:
        统一格式的分页响应字典
    """
    return {
        "code": 200,
        "data": {
            "list": items,
            "pageNum": page_num,
            "pageSize": page_size,
            "total": total
        },
        "msg": msg
    }


# 常用响应状态码
class ResponseCode:
    """响应状态码常量"""
    SUCCESS = 200           # 成功
    BAD_REQUEST = 400       # 请求参数错误
    UNAUTHORIZED = 401      # 未授权
    FORBIDDEN = 403         # 禁止访问
    NOT_FOUND = 404         # 资源不存在
    SERVER_ERROR = 500      # 服务器错误


# 常用响应消息
class ResponseMsg:
    """响应消息常量"""
    SUCCESS = "操作成功"
    CREATED = "创建成功"
    UPDATED = "更新成功"
    DELETED = "删除成功"
    BAD_REQUEST = "请求参数错误"
    UNAUTHORIZED = "未授权，请先登录"
    FORBIDDEN = "无权限访问"
    NOT_FOUND = "资源不存在"
    SERVER_ERROR = "服务器内部错误"
    LOGIN_SUCCESS = "登录成功"
    LOGOUT_SUCCESS = "退出成功"
    TOKEN_EXPIRED = "令牌已过期"
    TOKEN_INVALID = "令牌无效"






