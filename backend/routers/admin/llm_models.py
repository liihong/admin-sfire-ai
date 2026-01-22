"""
大模型管理 Endpoints
"""
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from db import get_db
from schemas.llm_model import (
    LLMModelCreate,
    LLMModelUpdate,
    LLMModelQueryParams,
    AvailableModelItem,
    BalanceRefreshResponse,
)
from services.resource import LLMModelService
from utils.response import success, page_response
from utils.serializers import llm_model_to_response

router = APIRouter()


@router.get("", summary="获取大模型列表")
async def get_llm_models(
    pageNum: int = Query(1, ge=1, description="页码"),
    pageSize: int = Query(10, ge=1, le=100, description="每页数量"),
    name: Optional[str] = Query(None, description="模型名称（模糊查询）"),
    provider: Optional[str] = Query(None, description="提供商"),
    is_enabled: Optional[bool] = Query(None, description="是否启用"),
    db: AsyncSession = Depends(get_db),
):
    """
    获取大模型列表（分页）
    
    支持按名称、提供商、启用状态筛选
    """
    llm_model_service = LLMModelService(db)
    
    params = LLMModelQueryParams(
        pageNum=pageNum,
        pageSize=pageSize,
        name=name,
        provider=provider,
        is_enabled=is_enabled,
    )
    
    result = await llm_model_service.get_llm_model_list(params)
    items = [llm_model_to_response(model) for model in result.list]
    
    return page_response(
        items=items,
        total=result.total,
        page_num=pageNum,
        page_size=pageSize,
    )


@router.get("/available", summary="获取可用模型列表")
async def get_available_models(
    db: AsyncSession = Depends(get_db),
):
    """
    获取可用模型列表（供智能体编辑页使用）
    
    只返回启用的模型，格式为前端需要的格式
    """
    llm_model_service = LLMModelService(db)
    models = await llm_model_service.get_enabled_models()
    
    # 转换为前端需要的格式
    items = [
        AvailableModelItem(
            id=str(model.id),
            name=model.name,
            model_id=model.model_id,
            provider=model.provider,
            max_tokens=4096,  # 默认值，可以根据模型类型设置不同值
        )
        for model in models
    ]
    
    return success(data=items)


@router.get("/{model_id}", summary="获取大模型详情")
async def get_llm_model(
    model_id: int,
    db: AsyncSession = Depends(get_db),
):
    """获取大模型详情"""
    llm_model_service = LLMModelService(db)
    model = await llm_model_service.get_llm_model_by_id(model_id)
    return success(data=llm_model_to_response(model))


@router.post("", summary="创建大模型")
async def create_llm_model(
    model_data: LLMModelCreate,
    db: AsyncSession = Depends(get_db),
):
    """创建大模型配置"""
    llm_model_service = LLMModelService(db)
    model = await llm_model_service.create_llm_model(model_data)
    await db.commit()
    return success(data=llm_model_to_response(model), msg="创建成功")


@router.put("/{model_id}", summary="更新大模型")
async def update_llm_model(
    model_id: int,
    model_data: LLMModelUpdate,
    db: AsyncSession = Depends(get_db),
):
    """更新大模型配置"""
    llm_model_service = LLMModelService(db)
    model = await llm_model_service.update_llm_model(model_id, model_data)
    await db.commit()
    return success(data=llm_model_to_response(model), msg="更新成功")


@router.delete("/{model_id}", summary="删除大模型")
async def delete_llm_model(
    model_id: int,
    db: AsyncSession = Depends(get_db),
):
    """删除大模型配置"""
    llm_model_service = LLMModelService(db)
    await llm_model_service.delete_llm_model(model_id)
    await db.commit()
    return success(msg="删除成功")


@router.post("/{model_id}/refresh-balance", summary="刷新账户余额")
async def refresh_balance(
    model_id: int,
    db: AsyncSession = Depends(get_db),
):
    """刷新大模型账户余额"""
    llm_model_service = LLMModelService(db)
    
    try:
        balance, updated_at = await llm_model_service.refresh_balance(model_id)
        await db.commit()
        
        response = BalanceRefreshResponse(
            balance=float(balance) if balance is not None else None,
            balance_updated_at=updated_at.isoformat() if updated_at else None,
            success=balance is not None,
            message="刷新成功" if balance is not None else "刷新失败，请检查 API Key 是否正确",
        )
        return success(data=response.model_dump())
    except Exception as e:
        response = BalanceRefreshResponse(
            balance=None,
            balance_updated_at=None,
            success=False,
            message=str(e),
        )
        return success(data=response.model_dump(), msg="刷新失败")

