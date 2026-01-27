"""
火源币算力相关API路由
提供算力余额查询、算力计算、流水查询、充值等接口
"""
from typing import Optional, Dict, Any
from fastapi import APIRouter, Depends, Query, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession

from db import get_db
from models.user import User
from core.deps import get_current_miniprogram_user
from services.coin import CoinServiceFactory
from services.coin.package import RechargePackageService
from services.coin.recharge_order import RechargeOrderService
from services.resource import ComputeService
from schemas.coin import (
    CoinBalanceResponse,
    CoinCostRequest,
    CoinEstimateRequest,
    CoinCostResponse,
)
from schemas.recharge import (
    RechargePackageResponse,
    RechargeOrderRequest,
    RechargeOrderResponse,
    PaymentCallbackRequest,
    OrderStatusResponse,
)
from utils.response import success, page_response, fail
from utils.exceptions import BadRequestException
from loguru import logger

router = APIRouter()


@router.get("/coin/balance", summary="查询算力余额")
async def get_balance(
    current_user: User = Depends(get_current_miniprogram_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取当前用户算力余额

    Returns:
        {
            "code": 200,
            "data": {
                "balance": 1000.00,
                "frozen_balance": 50.00,
                "available_balance": 950.00
            },
            "msg": "查询成功"
        }
    """
    try:
        coin_service = CoinServiceFactory(db)
        balance_info = await coin_service.get_balance(current_user.id)

        return success(data=balance_info, msg="查询成功")
    except Exception as e:
        return fail(msg=f"查询失败: {str(e)}", code=500)


@router.get("/coin/transactions", summary="查询算力流水")
async def get_transactions(
    page_num: int = Query(default=1, ge=1, description="页码"),
    page_size: int = Query(default=10, ge=1, le=1000, description="每页数量"),
    log_type: Optional[str] = Query(default=None, description="流水类型"),
    current_user: User = Depends(get_current_miniprogram_user),
    db: AsyncSession = Depends(get_db)
):
    """
    分页查询算力流水

    Returns:
        {
            "code": 200,
            "data": {
                "list": [...],
                "pageNum": 1,
                "pageSize": 10,
                "total": 100
            },
            "msg": "查询成功"
        }
    """
    try:
        service = ComputeService(db)
        result = await service.get_user_compute_logs(
            user_id=current_user.id,
            page_num=page_num,
            page_size=page_size,
            log_type=log_type
        )

        return page_response(
            items=result.list,
            total=result.total,
            page_num=result.pageNum,
            page_size=result.pageSize,
            msg="查询成功"
        )
    except Exception as e:
        return fail(msg=f"查询失败: {str(e)}", code=500)


@router.post("/coin/calculate", summary="计算算力消耗")
async def calculate_cost(
    request: CoinCostRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    计算指定输入输出的算力消耗

    Body:
        {
            "input_tokens": 1000,
            "output_tokens": 500,
            "model_id": 1
        }

    Returns:
        {
            "code": 200,
            "data": {
                "estimated_cost": 15.5,
                "breakdown": {...}
            },
            "msg": "计算成功"
        }
    """
    try:
        coin_service = CoinServiceFactory(db)

        # 计算费用
        cost = await coin_service.calculate_cost(
            input_tokens=request.input_tokens,
            output_tokens=request.output_tokens,
            model_id=request.model_id
        )

        # 获取费用明细
        breakdown = coin_service.get_cost_breakdown(
            input_tokens=request.input_tokens,
            output_tokens=request.output_tokens,
            model_id=request.model_id
        )

        return success(
            data={
                "estimated_cost": cost,
                "breakdown": breakdown
            },
            msg="计算成功"
        )
    except Exception as e:
        return fail(msg=f"计算失败: {str(e)}", code=500)


@router.post("/coin/estimate", summary="估算算力消耗")
async def estimate_cost(
    request: CoinEstimateRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    根据输入文本估算算力消耗

    Body:
        {
            "input_text": "你好,请介绍一下Python",
            "model_id": 1,
            "estimated_output_tokens": 1000  # 可选
        }

    Returns:
        {
            "code": 200,
            "data": {
                "estimated_cost": 25.5,
                "breakdown": {...}
            },
            "msg": "估算成功"
        }
    """
    try:
        coin_service = CoinServiceFactory(db)

        # 估算最大消耗
        cost = await coin_service.estimate_max_cost(
            model_id=request.model_id,
            input_text=request.input_text,
            estimated_output_tokens=request.estimated_output_tokens
        )

        # 估算Token数
        input_tokens = coin_service.estimate_tokens_from_text(request.input_text)
        output_tokens = request.estimated_output_tokens or 4096

        # 获取费用明细
        breakdown = coin_service.get_cost_breakdown(
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            model_id=request.model_id
        )

        return success(
            data={
                "estimated_cost": cost,
                "breakdown": breakdown
            },
            msg="估算成功"
        )
    except Exception as e:
        return fail(msg=f"估算失败: {str(e)}", code=500)


@router.get("/coin/statistics", summary="获取算力统计")
async def get_statistics(
    current_user: User = Depends(get_current_miniprogram_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取用户算力统计信息

    Returns:
        {
            "code": 200,
            "data": {
                "totalRecharge": 1000.00,
                "totalConsume": 500.00,
                "totalRefund": 50.00,
                ...
            },
            "msg": "查询成功"
        }
    """
    try:
        service = ComputeService(db)
        statistics = await service.get_user_statistics(current_user.id)

        return success(data=statistics, msg="查询成功")
    except Exception as e:
        return fail(msg=f"查询失败: {str(e)}", code=500)


@router.get("/coin/packages", summary="获取套餐列表")
async def get_packages(
    db: AsyncSession = Depends(get_db)
):
    """
    获取充值套餐列表（只返回启用的套餐）

    Returns:
        {
            "code": 200,
            "data": [
                {
                    "id": 1,
                    "name": "爆款合伙人",
                    "price": 99.00,
                    "power_amount": 15000,
                    ...
                }
            ],
            "msg": "查询成功"
        }
    """
    try:
        package_service = RechargePackageService(db)
        packages = await package_service.get_packages(enabled_only=True)
        
        # 转换为响应格式
        package_list = []
        for pkg in packages:
            package_list.append({
                "id": pkg.id,
                "name": pkg.name,
                "price": float(pkg.price),
                "power_amount": float(pkg.power_amount),
                "unit_price": pkg.unit_price,
                "tag": pkg.tag if pkg.tag else [],
                "description": pkg.description,
                "article_count": pkg.article_count,
                "sort_order": pkg.sort_order,
                "status": pkg.status,
                "is_popular": pkg.is_popular,
            })
        
        return success(data=package_list, msg="查询成功")
    except Exception as e:
        return fail(msg=f"查询失败: {str(e)}", code=500)


@router.post("/coin/recharge/order", summary="创建充值订单")
async def create_recharge_order(
    request: RechargeOrderRequest,
    http_request: Request,
    current_user: User = Depends(get_current_miniprogram_user),
    db: AsyncSession = Depends(get_db)
):
    """
    创建充值订单

    Body:
        {
            "package_id": 1
        }

    Returns:
        {
            "code": 200,
            "data": {
                "order_id": "R202401011234567890",
                "package_id": 1,
                "package_name": "爆款合伙人",
                "price": 99.00,
                "power_amount": 15000,
                "payment_status": "pending",
                "payment_params": {...}
            },
            "msg": "订单创建成功"
        }
    """
    try:
        # 获取用户openid（从用户信息中获取）
        openid = current_user.openid
        if not openid:
            return fail(msg="用户openid不存在，无法创建支付订单", code=400)
        
        # 获取客户端IP
        client_ip = http_request.client.host if http_request.client else "127.0.0.1"
        
        order_service = RechargeOrderService(db)
        order_info = await order_service.create_order(
            user_id=current_user.id,
            package_id=request.package_id,
            openid=openid,
            client_ip=client_ip
        )
        
        return success(data=order_info, msg="订单创建成功")
    except BadRequestException as e:
        return fail(msg=str(e), code=400)
    except Exception as e:
        return fail(msg=f"创建订单失败: {str(e)}", code=500)


@router.post("/coin/recharge/callback", summary="支付回调接口")
async def payment_callback(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    微信支付回调接口
    
    注意：此接口由微信支付平台调用，不需要用户认证
    
    Returns:
        XML格式响应（微信支付要求）
    """
    from utils.security import verify_ip_whitelist
    from core.config import settings
    
    # 初始化变量
    client_ip = "未知"
    order_id_hint = "未知"
    
    try:
        # 1. 验证IP白名单
        client_ip = request.client.host if request.client else None
        if not client_ip:
            # 尝试从X-Forwarded-For获取真实IP
            forwarded_for = request.headers.get("X-Forwarded-For")
            if forwarded_for:
                client_ip = forwarded_for.split(",")[0].strip()
            else:
                client_ip = "127.0.0.1"
        
        if not verify_ip_whitelist(client_ip, settings.WECHAT_PAY_IP_WHITELIST):
            logger.warning(
                f"支付回调IP不在白名单: IP={client_ip}, "
                f"白名单={settings.WECHAT_PAY_IP_WHITELIST}"
            )
            xml_response = _build_xml_response("FAIL", "IP验证失败")
            return Response(content=xml_response, media_type="application/xml")
        
        # 2. 获取回调数据（微信支付v2使用XML格式）
        xml_data = await request.body()
        callback_data = _parse_xml_callback(xml_data.decode('utf-8'))
        
        # 提取订单号用于错误日志
        order_id_hint = callback_data.get("out_trade_no", "未知")
        
        # 2.5. 验证微信支付返回状态码（必须验证）
        return_code = callback_data.get("return_code")
        result_code = callback_data.get("result_code")
        
        # 如果通信失败，直接返回失败
        if return_code != "SUCCESS":
            return_msg = callback_data.get("return_msg", "未知错误")
            logger.warning(
                f"微信支付回调通信失败: 订单号={order_id_hint}, "
                f"return_code={return_code}, return_msg={return_msg}, IP={client_ip}"
            )
            xml_response = _build_xml_response("FAIL", f"通信失败: {return_msg}")
            return Response(content=xml_response, media_type="application/xml")
        
        # 如果业务失败，记录日志但返回成功（避免微信重复回调）
        if result_code != "SUCCESS":
            err_code = callback_data.get("err_code", "未知错误码")
            err_code_des = callback_data.get("err_code_des", "未知错误")
            logger.warning(
                f"微信支付回调业务失败: 订单号={order_id_hint}, "
                f"err_code={err_code}, err_code_des={err_code_des}, IP={client_ip}"
            )
            # 返回SUCCESS避免微信重复回调，但不会处理订单
            xml_response = _build_xml_response("SUCCESS", "OK")
            return Response(content=xml_response, media_type="application/xml")
        
        # 3. 获取签名
        sign = callback_data.get("sign")
        if not sign:
            logger.warning(f"支付回调缺少签名: 订单号={order_id_hint}, IP={client_ip}")
            xml_response = _build_xml_response("FAIL", "缺少签名")
            return Response(content=xml_response, media_type="application/xml")
        
        # 4. 处理回调
        order_service = RechargeOrderService(db)
        result = await order_service.handle_payment_callback(callback_data, sign)
        
        xml_response = _build_xml_response("SUCCESS", "OK")
        return Response(content=xml_response, media_type="application/xml")
        
    except Exception as e:
        # 记录详细的错误信息（包含订单号、IP等，便于排查）
        logger.error(
            f"支付回调处理失败: 订单号={order_id_hint}, "
            f"IP={client_ip}, 错误={e}",
            exc_info=True  # 记录完整堆栈信息
        )
        xml_response = _build_xml_response("FAIL", f"处理失败: {str(e)}")
        return Response(content=xml_response, media_type="application/xml")


def _parse_xml_callback(xml_str: str) -> Dict[str, Any]:
    """
    解析XML回调数据（安全解析，防止XXE攻击）
    
    Args:
        xml_str: XML字符串
    
    Returns:
        解析后的字典
    """
    # 使用安全的XML解析库，防止XXE攻击
    try:
        from defusedxml import ElementTree as SafeET
        root = SafeET.fromstring(xml_str)
    except ImportError:
        # Fallback: 使用标准库但禁用实体
        import xml.etree.ElementTree as ET
        from xml.etree.ElementTree import XMLParser
        parser = XMLParser()
        parser.entity = {}  # 禁用实体引用
        root = ET.fromstring(xml_str, parser=parser)
    
    try:
        result = {}
        for child in root:
            result[child.tag] = child.text
        return result
    except Exception as e:
        logger.error(f"解析XML回调失败: {e}")
        return {}


def _build_xml_response(return_code: str, return_msg: str) -> str:
    """构建XML响应（微信支付v2要求）"""
    return f"<xml><return_code><![CDATA[{return_code}]]></return_code><return_msg><![CDATA[{return_msg}]]></return_msg></xml>"


@router.get("/coin/recharge/order/{order_id}", summary="查询订单状态")
async def query_order_status(
    order_id: str,
    current_user: User = Depends(get_current_miniprogram_user),
    db: AsyncSession = Depends(get_db)
):
    """
    查询充值订单状态

    Returns:
        {
            "code": 200,
            "data": {
                "order_id": "R202401011234567890",
                "payment_status": "paid",
                "payment_time": "2024-01-01T12:00:00",
                "wechat_transaction_id": "wx1234567890"
            },
            "msg": "查询成功"
        }
    """
    try:
        order_service = RechargeOrderService(db)
        order_status = await order_service.query_order_status(order_id)
        
        return success(data=order_status, msg="查询成功")
    except Exception as e:
        return fail(msg=f"查询失败: {str(e)}", code=500)
