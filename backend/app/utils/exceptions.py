"""
Custom Exceptions and Global Exception Handlers
自定义异常和全局异常处理器
"""
from typing import Any, Optional
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError
from loguru import logger

from .response import ResponseCode, ResponseMsg


class APIException(Exception):
    """
    API 基础异常类
    
    所有自定义 API 异常都应继承此类
    """
    def __init__(
        self,
        code: int = ResponseCode.SERVER_ERROR,
        msg: str = ResponseMsg.SERVER_ERROR,
        data: Any = None
    ):
        self.code = code
        self.msg = msg
        self.data = data
        super().__init__(msg)


class BadRequestException(APIException):
    """请求参数错误异常 (400)"""
    def __init__(
        self,
        msg: str = ResponseMsg.BAD_REQUEST,
        data: Any = None
    ):
        super().__init__(
            code=ResponseCode.BAD_REQUEST,
            msg=msg,
            data=data
        )


class UnauthorizedException(APIException):
    """未授权异常 (401)"""
    def __init__(
        self,
        msg: str = ResponseMsg.UNAUTHORIZED,
        data: Any = None
    ):
        super().__init__(
            code=ResponseCode.UNAUTHORIZED,
            msg=msg,
            data=data
        )


class ForbiddenException(APIException):
    """禁止访问异常 (403)"""
    def __init__(
        self,
        msg: str = ResponseMsg.FORBIDDEN,
        data: Any = None
    ):
        super().__init__(
            code=ResponseCode.FORBIDDEN,
            msg=msg,
            data=data
        )


class NotFoundException(APIException):
    """资源不存在异常 (404)"""
    def __init__(
        self,
        msg: str = ResponseMsg.NOT_FOUND,
        data: Any = None
    ):
        super().__init__(
            code=ResponseCode.NOT_FOUND,
            msg=msg,
            data=data
        )


class ServerErrorException(APIException):
    """服务器错误异常 (500)"""
    def __init__(
        self,
        msg: str = ResponseMsg.SERVER_ERROR,
        data: Any = None
    ):
        super().__init__(
            code=ResponseCode.SERVER_ERROR,
            msg=msg,
            data=data
        )


def _create_error_response(
    code: int,
    msg: str,
    data: Any = None,
    http_status: int = status.HTTP_200_OK
) -> JSONResponse:
    """
    创建统一格式的错误响应
    
    注意：HTTP 状态码始终为 200，业务错误通过 code 字段区分
    这是为了兼容 Geeker-Admin 前端的处理逻辑
    """
    return JSONResponse(
        status_code=http_status,
        content={
            "code": code,
            "data": data,
            "msg": msg
        }
    )


async def api_exception_handler(
    request: Request,
    exc: APIException
) -> JSONResponse:
    """处理自定义 API 异常"""
    logger.warning(
        f"API Exception: {exc.code} - {exc.msg} | "
        f"Path: {request.url.path} | "
        f"Method: {request.method}"
    )
    return _create_error_response(
        code=exc.code,
        msg=exc.msg,
        data=exc.data
    )


async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError
) -> JSONResponse:
    """处理请求参数验证异常"""
    errors = exc.errors()
    error_messages = []
    
    for error in errors:
        field = ".".join(str(loc) for loc in error["loc"])
        message = error["msg"]
        error_messages.append(f"{field}: {message}")
    
    error_detail = "; ".join(error_messages)
    
    logger.warning(
        f"Validation Error: {error_detail} | "
        f"Path: {request.url.path} | "
        f"Method: {request.method}"
    )
    
    return _create_error_response(
        code=ResponseCode.BAD_REQUEST,
        msg=f"参数验证失败: {error_detail}",
        data=None
    )


async def pydantic_exception_handler(
    request: Request,
    exc: ValidationError
) -> JSONResponse:
    """处理 Pydantic 验证异常"""
    logger.warning(
        f"Pydantic Validation Error: {exc} | "
        f"Path: {request.url.path}"
    )
    return _create_error_response(
        code=ResponseCode.BAD_REQUEST,
        msg="数据验证失败",
        data=None
    )


async def http_exception_handler(
    request: Request,
    exc: Exception
) -> JSONResponse:
    """处理 HTTP 异常"""
    from starlette.exceptions import HTTPException as StarletteHTTPException
    
    if isinstance(exc, StarletteHTTPException):
        code_map = {
            400: ResponseCode.BAD_REQUEST,
            401: ResponseCode.UNAUTHORIZED,
            403: ResponseCode.FORBIDDEN,
            404: ResponseCode.NOT_FOUND,
            500: ResponseCode.SERVER_ERROR,
        }
        msg_map = {
            400: ResponseMsg.BAD_REQUEST,
            401: ResponseMsg.UNAUTHORIZED,
            403: ResponseMsg.FORBIDDEN,
            404: ResponseMsg.NOT_FOUND,
            500: ResponseMsg.SERVER_ERROR,
        }
        
        code = code_map.get(exc.status_code, ResponseCode.SERVER_ERROR)
        msg = exc.detail if exc.detail else msg_map.get(
            exc.status_code,
            ResponseMsg.SERVER_ERROR
        )
        
        logger.warning(
            f"HTTP Exception: {exc.status_code} - {msg} | "
            f"Path: {request.url.path}"
        )
        
        return _create_error_response(code=code, msg=msg)
    
    return await global_exception_handler(request, exc)


async def global_exception_handler(
    request: Request,
    exc: Exception
) -> JSONResponse:
    """处理未捕获的全局异常"""
    logger.error(
        f"Unhandled Exception: {type(exc).__name__}: {str(exc)} | "
        f"Path: {request.url.path} | "
        f"Method: {request.method}",
        exc_info=True
    )
    
    return _create_error_response(
        code=ResponseCode.SERVER_ERROR,
        msg=ResponseMsg.SERVER_ERROR,
        data=None
    )


def register_exception_handlers(app: FastAPI) -> None:
    """
    注册全局异常处理器
    
    Args:
        app: FastAPI 应用实例
    """
    from starlette.exceptions import HTTPException as StarletteHTTPException
    
    # 自定义 API 异常
    app.add_exception_handler(APIException, api_exception_handler)
    
    # 请求参数验证异常
    app.add_exception_handler(
        RequestValidationError,
        validation_exception_handler
    )
    
    # Pydantic 验证异常
    app.add_exception_handler(ValidationError, pydantic_exception_handler)
    
    # HTTP 异常
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    
    # 全局未捕获异常
    app.add_exception_handler(Exception, global_exception_handler)
    
    logger.info("Exception handlers registered successfully")


