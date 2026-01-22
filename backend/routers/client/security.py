"""
Client Security Endpoints
C端安全检测接口（小程序 & PC官网）
提供内容安全检测功能，调用微信官方接口进行内容审核
"""
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from db import get_db
from services.system import SecurityService
from utils.response import success
from utils.exceptions import BadRequestException, ServerErrorException

router = APIRouter()


# ============== Request/Response Models ==============

class MsgSecCheckRequest(BaseModel):
    """内容安全检测请求"""
    content: str = Field(..., description="要检测的文本内容", min_length=1, max_length=500000)


class MsgSecCheckResponse(BaseModel):
    """内容安全检测响应"""
    # 注意：Python 关键字不能作为字段名，这里使用 is_pass 作为内部字段名，alias 映射为前端需要的 pass
    is_pass: bool = Field(..., alias="pass", description="是否通过检测")
    message: str = Field(..., description="提示消息")
    errCode: int = Field(None, description="错误码（如果有）")


# ============== API Endpoints ==============

@router.post("/msg-sec-check", response_model=dict)
async def msg_sec_check(
    request: MsgSecCheckRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    内容安全检测接口
    
    调用微信官方的 msgSecCheck 接口检测文本内容是否包含违规信息
    
    - **content**: 要检测的文本内容（必填，长度限制 1-500000 字符）
    
    返回格式:
    ```json
    {
        "code": 200,
        "data": {
            "pass": true,  // 是否通过检测
            "message": "内容检测通过",  // 提示消息
            "errCode": 0  // 错误码（0表示通过，87014表示违规）
        },
        "msg": "操作成功"
    }
    ```
    
    错误码说明:
    - 0: 内容正常
    - 87014: 内容包含违规信息
    - 其他: 服务异常（会记录日志，但默认返回通过，避免影响正常使用）
    """
    try:
        # 调用安全检测服务
        result = await SecurityService.msg_sec_check(content=request.content)
        
        # 返回统一格式的响应
        return success(
            data=result,
            msg="检测完成"
        )
        
    except BadRequestException as e:
        # 参数错误，直接抛出异常（会被全局异常处理器捕获并转换为统一格式）
        raise
    except ServerErrorException as e:
        # 服务器错误，直接抛出异常
        raise
    except Exception as e:
        # 其他未预期的错误
        logger.error(f"内容安全检测失败: {str(e)}", exc_info=True)
        raise ServerErrorException(f"内容安全检测失败: {str(e)}")

