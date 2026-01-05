"""
大模型管理服务
"""
from typing import List, Optional
from datetime import datetime
from decimal import Decimal
from sqlalchemy import select, func, and_, desc, asc
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger
import httpx

from models.llm_model import LLMModel
from schemas.llm_model import (
    LLMModelCreate,
    LLMModelUpdate,
    LLMModelQueryParams,
)
from utils.exceptions import (
    NotFoundException,
    BadRequestException,
)
from utils.pagination import paginate_query, PageResult
from services.base import BaseService


class LLMModelService(BaseService):
    """大模型管理服务类"""
    
    # 默认的 API Base URL
    DEFAULT_BASE_URLS = {
        "openai": "https://api.openai.com/v1",
        "anthropic": "https://api.anthropic.com/v1",
        "deepseek": "https://api.deepseek.com/v1",
    }
    
    def __init__(self, db: AsyncSession):
        super().__init__(db, LLMModel, "大模型", check_soft_delete=False)
    
    async def get_llm_model_list(
        self,
        params: LLMModelQueryParams,
    ) -> PageResult[LLMModel]:
        """
        获取大模型列表（分页）
        
        Args:
            params: 查询参数
            
        Returns:
            PageResult[LLMModel]: 分页结果
        """
        query = select(LLMModel)
        conditions = []
        
        if params.name:
            conditions.append(LLMModel.name.like(f"%{params.name}%"))
        if params.provider:
            conditions.append(LLMModel.provider == params.provider)
        if params.is_enabled is not None:
            conditions.append(LLMModel.is_enabled == params.is_enabled)
        
        if conditions:
            query = query.where(and_(*conditions))
        
        query = query.order_by(asc(LLMModel.sort_order), desc(LLMModel.created_at))
        
        count_query = select(func.count(LLMModel.id))
        if conditions:
            count_query = count_query.where(and_(*conditions))
        
        return await paginate_query(
            self.db,
            query,
            count_query,
            page_num=params.pageNum,
            page_size=params.pageSize,
        )
    
    async def get_llm_model_by_id(self, model_id: int) -> LLMModel:
        """根据ID获取大模型"""
        return await super().get_by_id(model_id, error_msg=f"大模型 {model_id} 不存在")
    
    async def get_llm_model_by_model_id(self, model_id: str) -> Optional[LLMModel]:
        """根据模型标识获取大模型"""
        result = await self.db.execute(
            select(LLMModel).where(LLMModel.model_id == model_id)
        )
        return result.scalar_one_or_none()
    
    async def get_enabled_models(self) -> List[LLMModel]:
        """获取所有启用的模型（供智能体编辑页使用）"""
        result = await self.db.execute(
            select(LLMModel)
            .where(LLMModel.is_enabled == True)
            .order_by(asc(LLMModel.sort_order), asc(LLMModel.name))
        )
        return list(result.scalars().all())
    
    async def create_llm_model(self, model_data: LLMModelCreate) -> LLMModel:
        """创建大模型配置"""
        # 检查 model_id 是否已存在
        existing = await self.get_llm_model_by_model_id(model_data.model_id)
        if existing:
            raise BadRequestException(f"模型标识 '{model_data.model_id}' 已存在")
        
        def before_create(model: LLMModel, data: LLMModelCreate):
            """创建前的钩子函数：设置默认 base_url"""
            # 如果没有提供 base_url，使用默认值
            if not data.base_url and hasattr(data, "provider"):
                model.base_url = self.DEFAULT_BASE_URLS.get(data.provider)
        
        model = await super().create(
            data=model_data,
            before_create=before_create,
        )
        
        await self.db.flush()
        await self.db.refresh(model)
        return model
    
    async def update_llm_model(self, model_id: int, model_data: LLMModelUpdate) -> LLMModel:
        """更新大模型配置"""
        # 如果更新 model_id，检查是否重复
        unique_fields = None
        if model_data.model_id:
            model = await self.get_llm_model_by_id(model_id)
            if model_data.model_id != model.model_id:
                existing = await self.get_llm_model_by_model_id(model_data.model_id)
                if existing:
                    raise BadRequestException(f"模型标识 '{model_data.model_id}' 已存在")
                # 设置唯一性检查（仅当 model_id 变化时）
                unique_fields = {
                    "model_id": {"error_msg": f"模型标识 '{model_data.model_id}' 已存在"},
                }
        
        def before_update(model: LLMModel, data: LLMModelUpdate):
            """更新前的钩子函数：处理默认 base_url"""
            # 如果 base_url 在更新数据中，且为空值，使用默认值
            if hasattr(data, "base_url") and data.base_url is not None:
                if not data.base_url:
                    # base_url 明确设置为空，使用默认值
                    provider = getattr(data, "provider", None) or model.provider
                    model.base_url = self.DEFAULT_BASE_URLS.get(provider)
        
        model = await super().update(
            obj_id=model_id,
            data=model_data,
            unique_fields=unique_fields,
            before_update=before_update,
        )
        
        await self.db.flush()
        await self.db.refresh(model)
        return model
    
    async def delete_llm_model(self, model_id: int) -> None:
        """删除大模型配置"""
        await super().delete(model_id, hard_delete=True)
        await self.db.flush()
    
    async def refresh_balance(self, model_id: int) -> tuple[Optional[float], Optional[datetime]]:
        """
        刷新账户余额
        
        Args:
            model_id: 模型ID
            
        Returns:
            (余额, 更新时间) 或 (None, None) 如果查询失败
        """
        model = await self.get_llm_model_by_id(model_id)
        
        if not model.api_key:
            raise BadRequestException("模型未配置 API Key")
        
        balance = None
        try:
            if model.provider == "openai":
                balance = await self._get_openai_balance(model.api_key)
            elif model.provider == "anthropic":
                balance = await self._get_anthropic_balance(model.api_key)
            elif model.provider == "deepseek":
                balance = await self._get_deepseek_balance(model.api_key)
            else:
                logger.warning(f"未知的提供商: {model.provider}")
                return None, None
        except Exception as e:
            logger.error(f"刷新余额失败: {e}")
            raise BadRequestException(f"刷新余额失败: {str(e)}")
        
        if balance is not None:
            model.balance = float(balance)
            model.balance_updated_at = datetime.now()
            await self.db.flush()
        
        return balance, model.balance_updated_at
    
    async def _get_openai_balance(self, api_key: str) -> Optional[float]:
        """
        获取 OpenAI 账户余额
        
        使用 OpenAI billing API
        """
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    "https://api.openai.com/v1/dashboard/billing/credit_grants",
                    headers={"Authorization": f"Bearer {api_key}"}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    total_granted = float(data.get("total_granted", 0))
                    total_used = float(data.get("total_used", 0))
                    balance = total_granted - total_used
                    return balance
                else:
                    logger.warning(f"OpenAI API returned status {response.status_code}")
                    return None
        except Exception as e:
            logger.error(f"Failed to get OpenAI balance: {e}")
            return None
    
    async def _get_anthropic_balance(self, api_key: str) -> Optional[float]:
        """
        获取 Anthropic 账户余额
        
        注意: Anthropic API 可能不直接提供余额查询接口
        这里先返回 None，后续根据实际 API 文档完善
        """
        # TODO: 实现 Anthropic 余额查询
        # Anthropic 可能需要使用其他方式查询余额
        logger.warning("Anthropic balance query not implemented yet")
        return None
    
    async def _get_deepseek_balance(self, api_key: str) -> Optional[float]:
        """
        获取 DeepSeek 账户余额
        
        注意: DeepSeek API 可能需要特定的余额查询接口
        这里先返回 None，后续根据实际 API 文档完善
        """
        # TODO: 实现 DeepSeek 余额查询
        logger.warning("DeepSeek balance query not implemented yet")
        return None
    
    async def update_token_usage(self, model_id: str, tokens_used: int) -> None:
        """
        更新 token 使用统计
        
        Args:
            model_id: 模型标识（如 "gpt-4o"）
            tokens_used: 本次使用的 token 数
        """
        model = await self.get_llm_model_by_model_id(model_id)
        if model:
            model.total_tokens_used += tokens_used
            await self.db.flush()

