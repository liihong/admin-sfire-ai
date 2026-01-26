"""
微信支付服务
用于处理微信支付统一下单、签名验证等
"""
import json
import httpx
import hashlib
import random
import string
import time
from typing import Dict, Any, Optional
from decimal import Decimal
from loguru import logger

from core.config import settings
from utils.payment import generate_wechat_sign, verify_wechat_sign, format_amount
from utils.exceptions import BadRequestException, ServerErrorException
from utils.security import verify_ip_whitelist


class WeChatPayService:
    """
    微信支付服务类
    
    职责说明：
    - 统一下单：创建微信支付订单
    - 签名验证：验证支付回调签名
    - 回调解析：解析支付回调数据
    """
    
    # 微信支付API地址（使用v2 API，与签名算法匹配）
    UNIFIED_ORDER_URL = "https://api.mch.weixin.qq.com/pay/unifiedorder"
    
    def __init__(self):
        """初始化微信支付服务"""
        self.app_id = settings.WECHAT_APP_ID
        self.mch_id = settings.WECHAT_PAY_MCH_ID
        self.api_key = settings.WECHAT_PAY_API_KEY
        self.notify_url = settings.WECHAT_PAY_NOTIFY_URL
        
        # 检查配置
        if not self.mch_id or not self.api_key:
            logger.warning("微信支付配置不完整，支付功能可能不可用")
    
    async def create_unified_order(
        self,
        order_id: str,
        amount: Decimal,
        description: str,
        openid: str,
        client_ip: str = "127.0.0.1"
    ) -> Dict[str, Any]:
        """
        创建微信支付统一下单
        
        Args:
            order_id: 商户订单号
            amount: 支付金额（元）
            description: 商品描述
            openid: 用户openid
            client_ip: 用户IP地址
        
        Returns:
            支付参数字典（用于前端调起支付）
        
        Raises:
            BadRequestException: 配置错误或参数错误
            ServerErrorException: 微信API调用失败
        """
        if not self.mch_id or not self.api_key:
            raise BadRequestException("微信支付配置不完整，请联系管理员")
        
        if not self.notify_url:
            raise BadRequestException("支付回调地址未配置，请联系管理员")
        
        # 构建请求参数
        params = {
            "appid": self.app_id,
            "mch_id": self.mch_id,
            "nonce_str": self._generate_nonce_str(),
            "body": description,
            "out_trade_no": order_id,
            "total_fee": format_amount(float(amount)),  # 转换为分
            "spbill_create_ip": client_ip,
            "notify_url": self.notify_url,
            "trade_type": "JSAPI",
            "openid": openid,
        }
        
        # 生成签名
        sign = generate_wechat_sign(params, self.api_key)
        params["sign"] = sign
        
        try:
            # 调用微信统一下单API（v2 API使用XML格式）
            import xml.etree.ElementTree as ET
            
            # 转换为XML格式
            xml_data = self._dict_to_xml(params)
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    self.UNIFIED_ORDER_URL,
                    content=xml_data.encode('utf-8'),
                    headers={"Content-Type": "application/xml"}
                )
                
                if response.status_code != 200:
                    raise ServerErrorException(
                        f"微信支付API调用失败: HTTP {response.status_code}"
                    )
                
                # 解析XML响应
                data = self._xml_to_dict(response.text)
                
                # 检查返回结果
                if data.get("return_code") != "SUCCESS":
                    return_msg = data.get("return_msg", "未知错误")
                    raise ServerErrorException(f"微信支付下单失败: {return_msg}")
                
                if data.get("result_code") != "SUCCESS":
                    err_code = data.get("err_code", "未知错误码")
                    err_code_des = data.get("err_code_des", "未知错误")
                    raise ServerErrorException(
                        f"微信支付下单失败: {err_code} - {err_code_des}"
                    )
                
                # 获取prepay_id
                prepay_id = data.get("prepay_id")
                if not prepay_id:
                    raise ServerErrorException("微信支付返回数据异常：缺少prepay_id")
                
                # 构建前端支付参数
                payment_params = self._build_payment_params(prepay_id)
                
                logger.info(
                    f"微信支付下单成功: 订单号={order_id}, "
                    f"金额={amount}, prepay_id={prepay_id}"
                )
                
                return payment_params
                
        except httpx.TimeoutException:
            raise ServerErrorException("微信支付API请求超时，请稍后重试")
        except ServerErrorException:
            raise
        except Exception as e:
            logger.error(f"微信支付下单异常: {e}")
            raise ServerErrorException(f"微信支付下单失败: {str(e)}")
    
    def _build_payment_params(self, prepay_id: str) -> Dict[str, Any]:
        """
        构建前端支付参数（小程序调起支付）
        
        Args:
            prepay_id: 预支付交易会话ID
        
        Returns:
            支付参数字典
        """
        params = {
            "appId": self.app_id,
            "timeStamp": str(int(time.time())),
            "nonceStr": self._generate_nonce_str(),
            "package": f"prepay_id={prepay_id}",
            "signType": "MD5",  # v2 API使用MD5签名
        }
        
        # 生成签名（v2 API使用MD5）
        params["paySign"] = self._generate_pay_sign(params)
        
        return params
    
    def _generate_nonce_str(self, length: int = 32) -> str:
        """生成随机字符串"""
        return ''.join(random.choices(string.ascii_letters + string.digits, k=length))
    
    def _generate_pay_sign(self, params: Dict[str, Any]) -> str:
        """
        生成支付签名（小程序调起支付用）
        
        使用MD5签名（v2 API）
        """
        # 过滤空值和paySign字段
        filtered_params = {
            k: v for k, v in params.items()
            if v is not None and v != "" and k != "paySign"
        }
        
        # 按键名排序
        sorted_params = sorted(filtered_params.items())
        
        # 拼接字符串
        string_a = "&".join([f"{k}={v}" for k, v in sorted_params])
        string_sign_temp = f"{string_a}&key={self.api_key}"
        
        # MD5加密并转大写
        sign = hashlib.md5(string_sign_temp.encode("utf-8")).hexdigest().upper()
        
        return sign
    
    def _dict_to_xml(self, params: Dict[str, Any]) -> str:
        """将字典转换为XML格式"""
        xml = "<xml>"
        for k, v in params.items():
            if v is not None:
                xml += f"<{k}><![CDATA[{v}]]></{k}>"
        xml += "</xml>"
        return xml
    
    def _xml_to_dict(self, xml_str: str) -> Dict[str, Any]:
        """将XML格式转换为字典"""
        try:
            root = ET.fromstring(xml_str)
            result = {}
            for child in root:
                result[child.tag] = child.text
            return result
        except Exception as e:
            logger.error(f"解析XML失败: {e}")
            return {}
    
    def verify_callback_signature(
        self,
        params: Dict[str, Any],
        sign: str
    ) -> bool:
        """
        验证支付回调签名
        
        Args:
            params: 回调参数字典
            sign: 回调签名
        
        Returns:
            是否验证通过
        """
        if not self.api_key:
            logger.warning("微信支付API密钥未配置，无法验证签名")
            return False
        
        return verify_wechat_sign(params, self.api_key, sign)
    
    def parse_callback_data(self, callback_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        解析支付回调数据
        
        Args:
            callback_data: 回调数据字典
        
        Returns:
            解析后的订单信息
        """
        # 提取关键信息
        order_id = callback_data.get("out_trade_no")
        transaction_id = callback_data.get("transaction_id")
        total_fee = callback_data.get("total_fee")
        time_end = callback_data.get("time_end")
        
        return {
            "order_id": order_id,
            "transaction_id": transaction_id,
            "amount": total_fee / 100.0 if total_fee else None,  # 分转元
            "payment_time": time_end,
        }

