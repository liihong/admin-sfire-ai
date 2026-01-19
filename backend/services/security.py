"""
Security Service
安全检测服务
封装微信内容安全检测接口，供多个业务场景复用
"""
import httpx
from typing import Optional
from loguru import logger

from core.config import settings
from utils.exceptions import ServerErrorException, BadRequestException


class SecurityService:
    """安全检测服务类"""
    
    @staticmethod
    async def get_wechat_access_token() -> str:
        """
        获取微信小程序 access_token
        
        Returns:
            access_token 字符串
        
        Raises:
            ServerErrorException: 获取 access_token 失败
        """
        if not settings.WECHAT_APP_ID or not settings.WECHAT_APP_SECRET:
            raise ServerErrorException("微信小程序配置未设置")
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    "https://api.weixin.qq.com/cgi-bin/token",
                    params={
                        "grant_type": "client_credential",
                        "appid": settings.WECHAT_APP_ID,
                        "secret": settings.WECHAT_APP_SECRET
                    }
                )
                
                data = response.json()
                
                if "errcode" in data:
                    errcode = data.get("errcode")
                    errmsg = data.get("errmsg", "未知错误")
                    raise ServerErrorException(f"获取 access_token 失败: {errmsg} (错误码: {errcode})")
                
                access_token = data.get("access_token")
                if not access_token:
                    raise ServerErrorException("获取 access_token 失败: 未返回 token")
                
                return access_token
                
        except httpx.TimeoutException:
            raise ServerErrorException("微信 API 请求超时，请稍后重试")
        except Exception as e:
            if isinstance(e, ServerErrorException):
                raise
            raise ServerErrorException(f"获取 access_token 失败: {str(e)}")
    
    @staticmethod
    async def msg_sec_check(
        content: str,
        openid: Optional[str] = None,
        scene: Optional[int] = None
    ) -> dict:
        """
        调用微信 msgSecCheck 接口检测文本内容是否违规
        
        Args:
            content: 要检测的文本内容
            openid: 用户 openid（可选）
            scene: 场景值（可选，如 1=资料，2=评论，3=论坛，4=社交日志）
        
        Returns:
            检测结果字典，格式: {
                "pass": bool,  # 是否通过检测
                "message": str,  # 提示消息
                "errCode": int  # 错误码（如果有）
            }
        
        Raises:
            BadRequestException: 参数错误
            ServerErrorException: 微信 API 调用失败
        """
        # 参数验证
        if not content or not content.strip():
            raise BadRequestException("内容不能为空")
        
        # 内容长度限制（微信限制为 500KB，这里限制为 500000 字符）
        if len(content) > 500000:
            raise BadRequestException("内容长度不能超过 500000 字符")
        
        try:
            # 1. 获取 access_token
            access_token = await SecurityService.get_wechat_access_token()
            
            # 2. 调用微信 msgSecCheck 接口
            async with httpx.AsyncClient(timeout=10.0) as client:
                # 构建请求体
                request_body = {"content": content.strip()}
                if openid:
                    request_body["openid"] = openid
                if scene is not None:
                    request_body["scene"] = scene
                
                # 调用接口
                response = await client.post(
                    f"https://api.weixin.qq.com/wxa/msg_sec_check?access_token={access_token}",
                    json=request_body,
                    headers={"Content-Type": "application/json"}
                )
                
                data = response.json()
                
                # 3. 解析响应
                errcode = data.get("errcode", -1)
                errmsg = data.get("errmsg", "未知错误")
                
                # errcode = 0 表示内容正常
                if errcode == 0:
                    return {
                        "pass": True,
                        "message": "内容检测通过",
                        "errCode": 0
                    }
                
                # errcode = 87014 表示内容违规
                elif errcode == 87014:
                    return {
                        "pass": False,
                        "message": "内容包含违规信息，请修改后重试",
                        "errCode": 87014
                    }
                
                # 其他错误码（如 40001=access_token 无效，40013=appid 无效等）
                else:
                    logger.warning(f"微信 msgSecCheck 接口返回错误: errcode={errcode}, errmsg={errmsg}")
                    # 对于非内容违规的错误，可以选择：
                    # 1. 抛出异常（严格模式）
                    # 2. 返回通过（宽松模式，避免因服务异常影响正常使用）
                    # 这里采用宽松模式，记录警告日志但返回通过
                    return {
                        "pass": True,
                        "message": f"安全检测服务异常: {errmsg}，已跳过检测",
                        "errCode": errcode
                    }
                    
        except httpx.TimeoutException:
            logger.error("微信 msgSecCheck 接口请求超时")
            raise ServerErrorException("安全检测服务请求超时，请稍后重试")
        except BadRequestException:
            raise
        except ServerErrorException:
            raise
        except Exception as e:
            logger.error(f"调用微信 msgSecCheck 接口失败: {str(e)}", exc_info=True)
            raise ServerErrorException(f"安全检测服务异常: {str(e)}")

