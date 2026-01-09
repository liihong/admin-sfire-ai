"""
Embedding服务
支持多种Embedding提供商（OpenAI、阿里云DashScope等）
"""
from typing import Optional, List
import numpy as np
from loguru import logger
import httpx

from core.config import settings


class EmbeddingService:
    """
    Embedding服务类
    
    支持通过OpenAI兼容API生成文本向量
    """
    
    # 默认配置
    DEFAULT_CONFIGS = {
        "openai": {
            "base_url": "https://api.openai.com/v1",
            "model": "text-embedding-3-small",
            "dimensions": 1024,
        },
        "dashscope": {
            "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
            "model": "text-embedding-v3",
            "dimensions": 1024,
        },
    }
    
    def __init__(self):
        """初始化Embedding服务"""
        # 获取提供商配置
        self.provider = settings.EMBEDDING_PROVIDER or "openai"
        
        # 获取默认配置
        default_config = self.DEFAULT_CONFIGS.get(self.provider, self.DEFAULT_CONFIGS["openai"])
        
        # 设置API配置（优先使用用户配置，否则使用默认值）
        self.base_url = settings.EMBEDDING_BASE_URL or default_config["base_url"]
        self.model = settings.EMBEDDING_MODEL or default_config["model"]
        self.default_dimensions = default_config["dimensions"]
        
        # 获取API Key（优先使用EMBEDDING_API_KEY，否则根据provider回退）
        self.api_key = settings.EMBEDDING_API_KEY or self._get_fallback_api_key()
        
        if not self.api_key:
            logger.warning(f"Embedding API Key未配置，provider: {self.provider}")
        
        logger.info(f"Embedding服务初始化: provider={self.provider}, model={self.model}, base_url={self.base_url}")
    
    def _get_fallback_api_key(self) -> str:
        """获取回退的API Key"""
        if self.provider == "openai":
            return settings.OPENAI_API_KEY
        elif self.provider == "dashscope":
            return settings.EMBEDDING_API_KEY  # DashScope需要专用key
        return ""
    
    async def generate_embedding(
        self,
        text: str,
        dimensions: Optional[int] = None
    ) -> Optional[np.ndarray]:
        """
        生成文本向量
        
        Args:
            text: 输入文本
            dimensions: 向量维度（可选，使用默认维度）
        
        Returns:
            numpy数组格式的向量，失败返回None
        """
        if not self.api_key:
            logger.error("Embedding API Key未配置")
            return None
        
        if not text or not text.strip():
            logger.warning("输入文本为空")
            return None
        
        dims = dimensions or self.default_dimensions
        
        try:
            # 构建请求
            url = f"{self.base_url.rstrip('/')}/embeddings"
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }
            
            # 请求体
            payload = {
                "model": self.model,
                "input": text,
            }
            
            # 如果模型支持dimensions参数（如OpenAI的text-embedding-3-*）
            if "embedding-3" in self.model or "v3" in self.model:
                payload["dimensions"] = dims
            
            # 发送请求
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(url, headers=headers, json=payload)
                response.raise_for_status()
                
                result = response.json()
                
                # 解析响应
                if "data" in result and len(result["data"]) > 0:
                    embedding = result["data"][0].get("embedding")
                    if embedding:
                        return np.array(embedding, dtype=np.float32)
                
                logger.error(f"Embedding响应格式异常: {result}")
                return None
                
        except httpx.HTTPStatusError as e:
            logger.error(f"Embedding API请求失败: {e.response.status_code} - {e.response.text}")
            return None
        except httpx.RequestError as e:
            logger.error(f"Embedding API请求错误: {e}")
            return None
        except Exception as e:
            logger.error(f"生成向量失败: {e}")
            return None
    
    async def generate_embeddings_batch(
        self,
        texts: List[str],
        dimensions: Optional[int] = None
    ) -> List[Optional[np.ndarray]]:
        """
        批量生成文本向量
        
        Args:
            texts: 输入文本列表
            dimensions: 向量维度（可选）
        
        Returns:
            向量列表，失败的项为None
        """
        if not self.api_key:
            logger.error("Embedding API Key未配置")
            return [None] * len(texts)
        
        if not texts:
            return []
        
        dims = dimensions or self.default_dimensions
        
        try:
            url = f"{self.base_url.rstrip('/')}/embeddings"
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "X-My-Gate-Key": "Huoyuan2026",  # 网关认证密钥
            }
            
            payload = {
                "model": self.model,
                "input": texts,
            }
            
            if "embedding-3" in self.model or "v3" in self.model:
                payload["dimensions"] = dims
            
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(url, headers=headers, json=payload)
                response.raise_for_status()
                
                result = response.json()
                
                if "data" in result:
                    # 按index排序确保顺序正确
                    sorted_data = sorted(result["data"], key=lambda x: x.get("index", 0))
                    return [
                        np.array(item["embedding"], dtype=np.float32) if item.get("embedding") else None
                        for item in sorted_data
                    ]
                
                logger.error(f"批量Embedding响应格式异常: {result}")
                return [None] * len(texts)
                
        except Exception as e:
            logger.error(f"批量生成向量失败: {e}")
            return [None] * len(texts)


# 全局Embedding服务实例（单例模式）
_embedding_service: Optional[EmbeddingService] = None


def get_embedding_service() -> EmbeddingService:
    """
    获取Embedding服务实例（单例模式）
    
    Returns:
        EmbeddingService实例
    """
    global _embedding_service
    
    if _embedding_service is None:
        _embedding_service = EmbeddingService()
    
    return _embedding_service
