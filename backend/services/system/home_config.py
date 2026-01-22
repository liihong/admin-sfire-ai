"""
Home Config Service
首页配置服务层
"""
import json
from typing import List, Dict, Any, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from models.home_config import HomeConfig
from schemas.home_config import (
    HomeConfigUpdate,
    HomeConfigResponse,
    HomeConfigBatchUpdate,
)
from utils.exceptions import NotFoundException, BadRequestException
from db.redis import get_redis


class HomeConfigService:
    """首页配置服务类"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.redis_client = None
    
    async def _get_redis(self):
        """获取Redis客户端（延迟初始化）"""
        if self.redis_client is None:
            self.redis_client = await get_redis()
        return self.redis_client
    
    def _format_config_response(self, config: HomeConfig) -> dict:
        """格式化配置响应"""
        return {
            "id": config.id,
            "config_key": config.config_key,
            "config_value": config.config_value,
            "config_type": config.config_type,
            "description": config.description,
            "is_enabled": config.is_enabled,
            "created_at": config.created_at.isoformat() if config.created_at else None,
            "updated_at": config.updated_at.isoformat() if config.updated_at else None,
        }
    
    async def _get_cache_key(self, config_key: str) -> str:
        """获取缓存键"""
        return f"home_config:{config_key}"
    
    async def _get_from_cache(self, config_key: str) -> Optional[str]:
        """从缓存获取配置"""
        try:
            redis = await self._get_redis()
            if redis:
                cache_key = await self._get_cache_key(config_key)
                return await redis.get(cache_key)
        except Exception as e:
            logger.warning(f"Failed to get config from cache: {e}")
        return None
    
    async def _set_to_cache(self, config_key: str, config_value: str, ttl: int = 3600):
        """设置配置到缓存"""
        try:
            redis = await self._get_redis()
            if redis:
                cache_key = await self._get_cache_key(config_key)
                await redis.setex(cache_key, ttl, config_value)
        except Exception as e:
            logger.warning(f"Failed to set config to cache: {e}")
    
    async def _delete_from_cache(self, config_key: str):
        """从缓存删除配置"""
        try:
            redis = await self._get_redis()
            if redis:
                cache_key = await self._get_cache_key(config_key)
                await redis.delete(cache_key)
        except Exception as e:
            logger.warning(f"Failed to delete config from cache: {e}")
    
    async def get_all_configs(self) -> List[dict]:
        """
        获取所有配置
        
        Returns:
            配置列表
        """
        result = await self.db.execute(
            select(HomeConfig).order_by(HomeConfig.config_key)
        )
        configs = result.scalars().all()
        
        return [self._format_config_response(config) for config in configs]
    
    async def get_config_by_key(self, config_key: str, use_cache: bool = True) -> dict:
        """
        根据配置键获取配置
        
        Args:
            config_key: 配置键
            use_cache: 是否使用缓存
        
        Returns:
            配置信息
        """
        # 尝试从缓存获取
        if use_cache:
            cached_value = await self._get_from_cache(config_key)
            if cached_value is not None:
                result = await self.db.execute(
                    select(HomeConfig).where(HomeConfig.config_key == config_key)
                )
                config = result.scalar_one_or_none()
                if config:
                    return self._format_config_response(config)
        
        # 从数据库获取
        result = await self.db.execute(
            select(HomeConfig).where(HomeConfig.config_key == config_key)
        )
        config = result.scalar_one_or_none()
        
        if not config:
            raise NotFoundException(msg=f"配置不存在: {config_key}")
        
        config_dict = self._format_config_response(config)
        
        # 更新缓存
        if use_cache and config.config_value:
            await self._set_to_cache(config_key, config.config_value)
        
        return config_dict
    
    async def update_config(self, config_key: str, config_data: HomeConfigUpdate) -> dict:
        """
        更新配置
        
        Args:
            config_key: 配置键
            config_data: 配置更新数据
        
        Returns:
            更新后的配置信息
        """
        result = await self.db.execute(
            select(HomeConfig).where(HomeConfig.config_key == config_key)
        )
        config = result.scalar_one_or_none()
        
        if not config:
            raise NotFoundException(msg=f"配置不存在: {config_key}")
        
        # 验证JSON格式
        if config_data.config_value is not None:
            if config_data.config_type == "json" or config.config_type == "json":
                try:
                    json.loads(config_data.config_value)
                except json.JSONDecodeError:
                    raise BadRequestException(msg="配置值必须是有效的JSON格式")
            elif config_data.config_type == "array" or config.config_type == "array":
                try:
                    parsed = json.loads(config_data.config_value)
                    if not isinstance(parsed, list):
                        raise BadRequestException(msg="配置值必须是有效的数组格式")
                except json.JSONDecodeError:
                    raise BadRequestException(msg="配置值必须是有效的JSON数组格式")
        
        # 更新字段
        update_data = config_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(config, field, value)
        
        await self.db.flush()
        await self.db.refresh(config)
        
        # 更新缓存
        if config.config_value:
            await self._set_to_cache(config_key, config.config_value)
        else:
            await self._delete_from_cache(config_key)
        
        logger.info(f"Home config updated: {config_key}")
        
        return self._format_config_response(config)
    
    async def batch_update_configs(self, batch_data: HomeConfigBatchUpdate) -> List[dict]:
        """
        批量更新配置
        
        Args:
            batch_data: 批量更新数据
        
        Returns:
            更新后的配置列表
        """
        updated_configs = []
        
        for config_item in batch_data.configs:
            config_key = config_item.get("config_key")
            if not config_key:
                continue
            
            result = await self.db.execute(
                select(HomeConfig).where(HomeConfig.config_key == config_key)
            )
            config = result.scalar_one_or_none()
            
            if not config:
                logger.warning(f"Config not found: {config_key}, skipping")
                continue
            
            # 更新字段
            if "config_value" in config_item:
                config_value = config_item["config_value"]
                # 验证JSON格式
                if config.config_type == "json":
                    try:
                        json.loads(str(config_value))
                    except (json.JSONDecodeError, TypeError):
                        if isinstance(config_value, (dict, list)):
                            config_value = json.dumps(config_value)
                        else:
                            raise BadRequestException(msg=f"配置 {config_key} 的值必须是有效的JSON格式")
                elif config.config_type == "array":
                    if isinstance(config_value, list):
                        config_value = json.dumps(config_value)
                    else:
                        try:
                            parsed = json.loads(str(config_value))
                            if not isinstance(parsed, list):
                                raise BadRequestException(msg=f"配置 {config_key} 的值必须是有效的数组格式")
                        except json.JSONDecodeError:
                            raise BadRequestException(msg=f"配置 {config_key} 的值必须是有效的JSON数组格式")
                
                config.config_value = str(config_value) if not isinstance(config_value, str) else config_value
            
            if "config_type" in config_item:
                config.config_type = config_item["config_type"]
            
            if "description" in config_item:
                config.description = config_item["description"]
            
            if "is_enabled" in config_item:
                config.is_enabled = config_item["is_enabled"]
            
            updated_configs.append(config)
        
        await self.db.flush()
        
        # 更新缓存
        for config in updated_configs:
            await self.db.refresh(config)
            if config.config_value:
                await self._set_to_cache(config.config_key, config.config_value)
            else:
                await self._delete_from_cache(config.config_key)
        
        logger.info(f"Batch updated {len(updated_configs)} home configs")
        
        return [self._format_config_response(config) for config in updated_configs]

