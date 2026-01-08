"""
Embedding服务
调用Embedding API生成文本向量
"""
import httpx
from typing import List, Optional
import numpy as np
from loguru import logger

from core.config import settings


class EmbeddingService:
    """
    Embedding生成服务
    
    支持多种Embedding API提供商（OpenAI兼容格式）
    注意：DeepSeek不提供embedding API，默认使用OpenAI
    """
    
    # 支持的提供商配置
    PROVIDER_CONFIGS = {
        "openai": {
            "base_url": "https://api.openai.com/v1",
            "default_model": "text-embedding-3-small",
            "default_dimensions": 1024,  # 使用1024维版本，效果更好且更省存储
            "api_key_setting": "OPENAI_API_KEY"
        },
        "deepseek": {
            "base_url": "https://api.deepseek.com/v1",
            "default_model": "text-embedding-3-small",  # DeepSeek不提供embedding，使用OpenAI兼容服务
            "default_dimensions": 1024,
            "api_key_setting": "DEEPSEEK_API_KEY"
        }
    }
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        provider: Optional[str] = None
    ):
        """
        初始化Embedding服务
        
        Args:
            api_key: API Key（可选，默认从配置读取）
            base_url: API基础URL（可选，默认根据provider自动设置）
            model: Embedding模型名称（可选，默认根据provider自动设置）
            provider: 服务提供商（可选，默认从配置读取，支持: openai, deepseek）
        
        注意：
        - DeepSeek不提供embedding API，如果provider为deepseek，会回退到使用OpenAI（如果配置了）
        - 建议使用OpenAI的embedding服务（text-embedding-3-small等）
        """
        # 确定使用的provider
        self.provider = provider or settings.EMBEDDING_PROVIDER.lower()
        
        # 如果provider不在支持列表中，回退到openai
        if self.provider not in self.PROVIDER_CONFIGS:
            logger.warning(f"不支持的embedding provider: {self.provider}，回退到openai")
            self.provider = "openai"
        
        # 如果provider是deepseek，但DeepSeek不提供embedding，回退到openai
        if self.provider == "deepseek":
            logger.warning("DeepSeek不提供embedding API，回退到OpenAI")
            self.provider = "openai"
        
        # 获取provider配置
        provider_config = self.PROVIDER_CONFIGS[self.provider]
        
        # 设置API Key
        if api_key:
            self.api_key = api_key
        elif settings.EMBEDDING_API_KEY:
            self.api_key = settings.EMBEDDING_API_KEY
        else:
            # 从provider对应的配置中获取API Key
            api_key_attr = getattr(settings, provider_config["api_key_setting"], "")
            self.api_key = api_key_attr or ""
        
        # 设置base_url
        if base_url:
            self.base_url = base_url.rstrip("/")
        elif settings.EMBEDDING_BASE_URL:
            self.base_url = settings.EMBEDDING_BASE_URL.rstrip("/")
        else:
            self.base_url = provider_config["base_url"]
        
        # 设置model
        if model:
            self.model = model
        elif settings.EMBEDDING_MODEL:
            self.model = settings.EMBEDDING_MODEL
        else:
            self.model = provider_config["default_model"]
        
        # 设置默认维度（用于text-embedding-3-small等支持dimensions参数的模型）
        self.default_dimensions = provider_config.get("default_dimensions", 1024)
        
        if not self.api_key:
            logger.warning(f"{self.provider.upper()} API Key未配置，Embedding功能将不可用")
        else:
            logger.info(f"Embedding服务已初始化: provider={self.provider}, base_url={self.base_url}, model={self.model}, dimensions={self.default_dimensions}")
    
    async def generate_embedding(
        self,
        text: str,
        model: Optional[str] = None,
        dimensions: Optional[int] = None
    ) -> Optional[np.ndarray]:
        """
        生成单个文本的向量
        
        Args:
            text: 输入文本
            model: 模型名称（可选，默认使用初始化时的模型）
            dimensions: 向量维度（可选，默认1024）
        
        Returns:
            numpy数组表示的向量，失败返回None
        """
        if not self.api_key:
            logger.error(f"{self.provider.upper()} API Key未配置")
            return None
        
        try:
            embeddings = await self.batch_generate_embeddings([text], model=model, dimensions=dimensions)
            if embeddings and len(embeddings) > 0:
                return embeddings[0]
            return None
        except Exception as e:
            logger.error(f"生成Embedding失败: {e}")
            return None
    
    async def batch_generate_embeddings(
        self,
        texts: List[str],
        model: Optional[str] = None,
        dimensions: Optional[int] = None
    ) -> List[Optional[np.ndarray]]:
        """
        批量生成向量
        
        Args:
            texts: 文本列表
            model: 模型名称（可选）
            dimensions: 向量维度（可选，默认1024，适用于text-embedding-3-small）
        
        Returns:
            向量列表，失败的元素为None
        """
        if not self.api_key:
            logger.error(f"{self.provider.upper()} API Key未配置")
            return [None] * len(texts)
        
        if not texts:
            return []
        
        model_name = model or self.model
        embedding_dimensions = dimensions or self.default_dimensions
        
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "input": texts,
                "model": model_name
            }
            
            # 对于支持dimensions参数的模型（如text-embedding-3-small），添加dimensions参数
            if "text-embedding-3" in model_name.lower():
                payload["dimensions"] = embedding_dimensions
            
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{self.base_url}/embeddings",
                    headers=headers,
                    json=payload
                )
                response.raise_for_status()
                
                data = response.json()
                embeddings = []
                
                for item in data.get("data", []):
                    embedding = item.get("embedding")
                    if embedding:
                        embeddings.append(np.array(embedding, dtype=np.float32))
                    else:
                        embeddings.append(None)
                
                logger.debug(f"成功生成 {len(embeddings)} 个向量")
                return embeddings
                
        except httpx.HTTPStatusError as e:
            logger.error(f"Embedding API请求失败: {e.response.status_code} - {e.response.text}")
            return [None] * len(texts)
        except Exception as e:
            logger.error(f"生成Embedding失败: {e}")
            return [None] * len(texts)
    
    def embed_text(self, text: str) -> Optional[np.ndarray]:
        """
        同步方法：文本向量化（不推荐，建议使用异步方法）
        
        Args:
            text: 输入文本
        
        Returns:
            向量数组
        """
        import asyncio
        try:
            loop = asyncio.get_event_loop()
            return loop.run_until_complete(self.generate_embedding(text))
        except RuntimeError:
            # 如果没有事件循环，创建一个新的
            return asyncio.run(self.generate_embedding(text))


# 全局Embedding服务实例（延迟初始化）
_embedding_service: Optional[EmbeddingService] = None


def get_embedding_service(
    api_key: Optional[str] = None,
    model: Optional[str] = None,
    provider: Optional[str] = None,
    force_reinit: bool = False
) -> EmbeddingService:
    """
    获取Embedding服务实例（单例模式）
    
    Args:
        api_key: API Key（可选）
        model: 模型名称（可选）
        provider: 服务提供商（可选）
        force_reinit: 是否强制重新初始化（用于配置变更后）
    
    Returns:
        EmbeddingService实例
    
    注意：
    - DeepSeek不提供embedding API，如果指定provider为deepseek，会自动回退到OpenAI
    - 建议在环境变量中设置 EMBEDDING_PROVIDER=openai 并使用 OPENAI_API_KEY
    """
    global _embedding_service
    
    if _embedding_service is None or force_reinit:
        _embedding_service = EmbeddingService(
            api_key=api_key,
            model=model,
            provider=provider
        )
    
    return _embedding_service


