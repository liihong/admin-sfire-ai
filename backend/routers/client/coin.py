"""
火源币算力相关API路由
提供算力余额查询、算力计算、流水查询等接口
"""
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from db import get_db
from models.user import User
from core.deps import get_current_miniprogram_user
from services.coin.account import CoinAccountService
from services.coin.calculator import CoinCalculatorService
from services.resource import ComputeService
from schemas.coin import (
    CoinBalanceResponse,
    CoinCostRequest,
    CoinEstimateRequest,
    CoinCostResponse,
)
from utils.response import success, page_response, fail
from utils.exceptions import BadRequestException

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
        service = CoinAccountService(db)
        balance_info = await service.get_user_balance(current_user.id)

        return success(data=balance_info, msg="查询成功")
    except Exception as e:
        return fail(msg=f"查询失败: {str(e)}", code=500)


@router.get("/coin/transactions", summary="查询算力流水")
async def get_transactions(
    page_num: int = Query(default=1, ge=1, description="页码"),
    page_size: int = Query(default=10, ge=1, le=100, description="每页数量"),
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
        calculator = CoinCalculatorService(db)

        # 计算费用
        cost = await calculator.calculate_cost(
            input_tokens=request.input_tokens,
            output_tokens=request.output_tokens,
            model_id=request.model_id
        )

        # 获取费用明细
        breakdown = calculator.get_cost_breakdown(
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
        calculator = CoinCalculatorService(db)

        # 估算最大消耗
        cost = await calculator.estimate_max_cost(
            model_id=request.model_id,
            input_text=request.input_text,
            estimated_output_tokens=request.estimated_output_tokens
        )

        # 估算Token数
        input_tokens = calculator.estimate_tokens_from_text(request.input_text)
        output_tokens = request.estimated_output_tokens or 4096

        # 获取费用明细
        breakdown = calculator.get_cost_breakdown(
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
