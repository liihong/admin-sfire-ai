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

from app.models.llm_model import LLMModel
from app.schemas.llm_model import (
    LLMModelCreate,
    LLMModelUpdate,
    LLMModelQueryParams,
)
from app.utils.exceptions import (
    NotFoundException,
    BadRequestException,
)
from app.utils.pagination import paginate_query, PageResult


class LLMModelService:
    """大模型管理服务类"""
    
    # 默认的 API Base URL
    DEFAULT_BASE_URLS = {
        "openai": "https://api.openai.com/v1",
        "anthropic": "https://api.anthropic.com/v1",
        "deepseek": "https://api.deepseek.com/v1",
    }
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
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
        result = await self.db.execute(
            select(LLMModel).where(LLMModel.id == model_id)
        )
        model = result.scalar_one_or_none()
        if not model:
            raise NotFoundException(f"大模型 {model_id} 不存在")
        return model
    
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
        
        # 如果没有提供 base_url，使用默认值
        base_url = model_data.base_url
        if not base_url:
            base_url = self.DEFAULT_BASE_URLS.get(model_data.provider)
        
        model = LLMModel(
            name=model_data.name,
            model_id=model_data.model_id,
            provider=model_data.provider,
            api_key=model_data.api_key,  # TODO: 加密存储
            base_url=base_url,
            is_enabled=model_data.is_enabled,
            sort_order=model_data.sort_order,
            remark=model_data.remark,
        )
        
        self.db.add(model)
        await self.db.flush()
        await self.db.refresh(model)
        return model
    
    async def update_llm_model(self, model_id: int, model_data: LLMModelUpdate) -> LLMModel:
        """更新大模型配置"""
        model = await self.get_llm_model_by_id(model_id)
        
        # 如果更新 model_id，检查是否重复
        if model_data.model_id and model_data.model_id != model.model_id:
            existing = await self.get_llm_model_by_model_id(model_data.model_id)
            if existing:
                raise BadRequestException(f"模型标识 '{model_data.model_id}' 已存在")
        
        if model_data.name:
            model.name = model_data.name
        if model_data.model_id:
            model.model_id = model_data.model_id
        if model_data.provider:
            model.provider = model_data.provider
        if model_data.api_key is not None:
            model.api_key = model_data.api_key  # TODO: 加密存储
        if model_data.base_url is not None:
            model.base_url = model_data.base_url or self.DEFAULT_BASE_URLS.get(model.provider)
        if model_data.is_enabled is not None:
            model.is_enabled = model_data.is_enabled
        if model_data.sort_order is not None:
            model.sort_order = model_data.sort_order
        if model_data.remark is not None:
            model.remark = model_data.remark
        
        await self.db.flush()
        await self.db.refresh(model)
        return model
    
    async def delete_llm_model(self, model_id: int) -> None:
        """删除大模型配置"""
        model = await self.get_llm_model_by_id(model_id)
        await self.db.delete(model)
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

