"""
LLM Service Module - Factory Pattern Implementation

This module provides a unified interface for different LLM providers:
- DeepSeek (OpenAI compatible format)
- Claude (Anthropic API)
- Doubao (Volcengine/火山引擎 API)
"""
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, AsyncGenerator
import httpx

from core.config import settings


class BaseLLM(ABC):
    """Abstract base class for LLM implementations."""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
    
    @abstractmethod
    async def generate_text(self, prompt: str, **kwargs) -> str:
        """
        Generate text based on the given prompt.
        
        Args:
            prompt: The input prompt for text generation.
            **kwargs: Additional parameters for the API call.
            
        Returns:
            Generated text response.
        """
        pass
    
    @abstractmethod
    async def generate_stream(self, prompt: str, **kwargs) -> AsyncGenerator[str, None]:
        """
        Generate text in streaming mode.
        
        Args:
            prompt: The input prompt for text generation.
            **kwargs: Additional parameters for the API call.
            
        Yields:
            Generated text chunks.
        """
        pass


class DeepSeekLLM(BaseLLM):
    """
    DeepSeek LLM implementation using OpenAI-compatible API format.
    
    API Documentation: https://platform.deepseek.com/api-docs
    """
    
    DEFAULT_BASE_URL = "https://api.deepseek.com"
    DEFAULT_MODEL = "deepseek-chat"
    
    def __init__(
        self, 
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None
    ):
        super().__init__(api_key or settings.DEEPSEEK_API_KEY)
        self.base_url = base_url or self.DEFAULT_BASE_URL
        self.model = model or self.DEFAULT_MODEL
        
        if not self.api_key:
            raise ValueError("DeepSeek API key is required. Set DEEPSEEK_API_KEY environment variable.")
    
    async def generate_text(self, prompt: str, **kwargs) -> str:
        """Generate text using DeepSeek API (OpenAI compatible format)."""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "X-My-Gate-Key": "Huoyuan2026",  # 网关认证密钥
        }
        
        payload = {
            "model": kwargs.get("model", self.model),
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "temperature": kwargs.get("temperature", 0.7),
            "max_tokens": kwargs.get("max_tokens", 2048),
            "stream": False
        }
        
        if "system_prompt" in kwargs:
            payload["messages"].insert(0, {
                "role": "system",
                "content": kwargs["system_prompt"]
            })
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{self.base_url}/v1/chat/completions",
                headers=headers,
                json=payload
            )
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]
    
    async def generate_stream(self, prompt: str, **kwargs) -> AsyncGenerator[str, None]:
        """Generate text in streaming mode using DeepSeek API."""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "X-My-Gate-Key": "Huoyuan2026",  # 网关认证密钥
        }
        
        payload = {
            "model": kwargs.get("model", self.model),
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "temperature": kwargs.get("temperature", 0.7),
            "max_tokens": kwargs.get("max_tokens", 2048),
            "stream": True
        }
        
        if "system_prompt" in kwargs:
            payload["messages"].insert(0, {
                "role": "system",
                "content": kwargs["system_prompt"]
            })
        
        # 规范化 base_url 并构建完整 URL
        normalized_base_url = self.base_url.rstrip('/')
        if '/v1' not in normalized_base_url and not normalized_base_url.endswith('/v1'):
            request_url = f"{normalized_base_url}/v1/chat/completions"
        else:
            request_url = f"{normalized_base_url}/chat/completions"
        
        async with httpx.AsyncClient(timeout=120.0) as client:
            async with client.stream(
                "POST",
                request_url,
                headers=headers,
                json=payload
            ) as response:
                try:
                    response.raise_for_status()
                except httpx.HTTPStatusError as e:
                    # 先读取响应体到内存，然后才能访问 .text
                    await e.response.aread()
                    error_msg = e.response.text
                    print(f"DeepSeek服务器报错内容: {error_msg}")
                    raise
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data = line[6:]
                        if data == "[DONE]":
                            break
                        try:
                            import json
                            chunk = json.loads(data)
                            content = chunk["choices"][0]["delta"].get("content", "")
                            if content:
                                yield content
                        except (json.JSONDecodeError, KeyError, IndexError):
                            continue


class ClaudeLLM(BaseLLM):
    """
    Claude LLM implementation supporting both Anthropic API and OpenAI-compatible proxies.
    """
    
    DEFAULT_BASE_URL = "https://api.anthropic.com"
    DEFAULT_MODEL = "claude-3-5-sonnet-20241022"
    API_VERSION = "2023-06-01"
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None
    ):
        super().__init__(api_key or settings.ANTHROPIC_API_KEY)
        self.base_url = base_url or self.DEFAULT_BASE_URL
        self.model = model or self.DEFAULT_MODEL
        self.use_openai_format = False
        
        if not self.api_key:
            raise ValueError("Claude API key is required. Set ANTHROPIC_API_KEY environment variable.")
    
    async def generate_text(self, prompt: str, **kwargs) -> str:
        """Generate text using Claude API."""
        is_official_api = "api.anthropic.com" in self.base_url
        use_openai_format = self.use_openai_format or (not is_official_api)

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "X-My-Gate-Key": "Huoyuan2026",  # 网关认证密钥
        }

        if is_official_api and not use_openai_format:
            headers = {
                "x-api-key": self.api_key,
                "anthropic-version": self.API_VERSION,
                "Content-Type": "application/json",
                "X-My-Gate-Key": "Huoyuan2026",  # 网关认证密钥
            }

        base_url = self.base_url.rstrip("/")

        if use_openai_format:
            # 构建 messages，为 Claude 模型启用缓存
            messages = []
            is_claude_model = kwargs.get("model", self.model).startswith("claude")

            if "system_prompt" in kwargs and kwargs["system_prompt"]:
                system_prompt = kwargs["system_prompt"]
                if is_claude_model:
                    # Claude 模型使用列表结构并启用缓存
                    messages.append({
                        "role": "system",
                        "content": [
                            {
                                "type": "text",
                                "text": system_prompt,
                                "cache_control": {"type": "ephemeral"}
                            }
                        ]
                    })
                else:
                    # 其他模型使用普通字符串
                    messages.append({"role": "system", "content": system_prompt})

            # user 消息不需要缓存
            messages.append({"role": "user", "content": prompt})

            payload = {
                "model": kwargs.get("model", self.model),
                "messages": messages,
                "temperature": kwargs.get("temperature", 0.7),
                "max_tokens": kwargs.get("max_tokens", 2048),
                "stream": False
            }
            url = f"{base_url}/v1/chat/completions"
        else:
            # Anthropic 原生 API 格式
            is_claude_model = kwargs.get("model", self.model).startswith("claude")

            # 构建用户消息，为 Claude 启用缓存
            user_content = [{"type": "text", "text": prompt}]
            if is_claude_model:
                user_content[0]["cache_control"] = {"type": "ephemeral"}

            payload = {
                "model": kwargs.get("model", self.model),
                "max_tokens": kwargs.get("max_tokens", 2048),
                "messages": [{"role": "user", "content": user_content}]
            }
            if "temperature" in kwargs:
                payload["temperature"] = kwargs["temperature"]
            if "system_prompt" in kwargs and kwargs["system_prompt"]:
                payload["system"] = kwargs["system_prompt"]
            url = f"{base_url}/v1/messages"

        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()

            if use_openai_format:
                return data["choices"][0]["message"]["content"]
            else:
                content_blocks = data.get("content", [])
                return "".join(block.get("text", "") for block in content_blocks if block.get("type") == "text")
    
    async def generate_stream(self, prompt: str, **kwargs) -> AsyncGenerator[str, None]:
        """Generate text in streaming mode using Claude API."""
        import json

        is_official_api = "api.anthropic.com" in self.base_url
        use_openai_format = self.use_openai_format or (not is_official_api)

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "X-My-Gate-Key": "Huoyuan2026",  # 网关认证密钥
        }

        if is_official_api and not use_openai_format:
            headers = {
                "x-api-key": self.api_key,
                "anthropic-version": self.API_VERSION,
                "Content-Type": "application/json",
                "X-My-Gate-Key": "Huoyuan2026",  # 网关认证密钥
            }

        if use_openai_format:
            # 构建 messages，为 Claude 模型启用缓存
            messages = []
            is_claude_model = kwargs.get("model", self.model).startswith("claude")

            if "system_prompt" in kwargs and kwargs["system_prompt"]:
                system_prompt = kwargs["system_prompt"]
                if is_claude_model:
                    # Claude 模型使用列表结构并启用缓存
                    messages.append({
                        "role": "system",
                        "content": [
                            {
                                "type": "text",
                                "text": system_prompt,
                                "cache_control": {"type": "ephemeral"}
                            }
                        ]
                    })
                else:
                    # 其他模型使用普通字符串
                    messages.append({"role": "system", "content": system_prompt})

            # user 消息不需要缓存
            messages.append({"role": "user", "content": prompt})

            payload = {
                "model": kwargs.get("model", self.model),
                "messages": messages,
                "temperature": kwargs.get("temperature", 0.7),
                "max_tokens": kwargs.get("max_tokens", 2048),
                "stream": True
            }
            # 添加可选参数（与 AIService 保持一致）
            if "top_p" in kwargs:
                payload["top_p"] = kwargs["top_p"]
            if "frequency_penalty" in kwargs:
                payload["frequency_penalty"] = kwargs["frequency_penalty"]
            if "presence_penalty" in kwargs:
                payload["presence_penalty"] = kwargs["presence_penalty"]

            # 记录 system_prompt 长度（可能很大）
            system_prompt_length = len(kwargs.get("system_prompt", "")) if "system_prompt" in kwargs else 0

            # 规范化 base_url 并构建完整 URL
            normalized_base_url = self.base_url.rstrip('/')
            if '/v1' not in normalized_base_url and not normalized_base_url.endswith('/v1'):
                url = f"{normalized_base_url}/v1/chat/completions"
            else:
                url = f"{normalized_base_url}/chat/completions"
        else:
            # Anthropic 原生 API 格式
            is_claude_model = kwargs.get("model", self.model).startswith("claude")

            # 构建用户消息，为 Claude 启用缓存
            user_content = [{"type": "text", "text": prompt}]
            if is_claude_model:
                user_content[0]["cache_control"] = {"type": "ephemeral"}

            payload = {
                "model": kwargs.get("model", self.model),
                "max_tokens": kwargs.get("max_tokens", 2048),
                "messages": [{"role": "user", "content": user_content}],
                "stream": True
            }
            if "temperature" in kwargs:
                payload["temperature"] = kwargs["temperature"]
            if "system_prompt" in kwargs and kwargs["system_prompt"]:
                payload["system"] = kwargs["system_prompt"]
            url = f"{self.base_url}/v1/messages"
        
        async with httpx.AsyncClient(timeout=120.0, follow_redirects=True) as client:
            async with client.stream("POST", url, headers=headers, json=payload) as response:
                try:
                    response.raise_for_status()
                except httpx.HTTPStatusError as e:
                    # 先读取响应体到内存，然后才能访问 .text（必须在 async with 块内）
                    await e.response.aread()
                    error_msg = e.response.text
                    print(f"Claude服务器报错内容: {error_msg}")
                    raise
                # 如果状态码是 200，直接流式返回，不要调用 .aread()
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data = line[6:]
                        if data == "[DONE]":
                            break
                        try:
                            chunk = json.loads(data)
                            if use_openai_format:
                                content = chunk["choices"][0]["delta"].get("content", "")
                                if content:
                                    yield content
                            else:
                                if chunk.get("type") == "content_block_delta":
                                    text = chunk.get("delta", {}).get("text", "")
                                    if text:
                                        yield text
                        except (json.JSONDecodeError, KeyError, IndexError):
                            continue


class DoubaoLLM(BaseLLM):
    """
    Doubao (豆包) LLM implementation using Volcengine (火山引擎) API.
    """
    
    DEFAULT_BASE_URL = "https://ark.cn-beijing.volces.com/api/v3"
    DEFAULT_MODEL = "ep-20241226000000-00000"
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None
    ):
        super().__init__(api_key or settings.DOUBAO_API_KEY)
        self.base_url = base_url or self.DEFAULT_BASE_URL
        self.model = model or self.DEFAULT_MODEL
        
        if not self.api_key:
            raise ValueError("Doubao API key is required. Set DOUBAO_API_KEY environment variable.")
    
    async def generate_text(self, prompt: str, **kwargs) -> str:
        """Generate text using Volcengine Doubao API."""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "X-My-Gate-Key": "Huoyuan2026",  # 网关认证密钥
        }
        
        payload = {
            "model": kwargs.get("model", self.model),
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "temperature": kwargs.get("temperature", 0.7),
            "max_tokens": kwargs.get("max_tokens", 2048),
            "stream": False
        }
        
        if "system_prompt" in kwargs:
            payload["messages"].insert(0, {
                "role": "system",
                "content": kwargs["system_prompt"]
            })
        
        # 规范化 base_url 并构建完整 URL（Doubao 可能不需要 /v1）
        normalized_base_url = self.base_url.rstrip('/')
        # Doubao API 路径通常是 /api/v3/chat/completions
        # 但如果 base_url 已经包含路径，直接使用
        if '/chat/completions' in normalized_base_url:
            request_url = normalized_base_url
        elif '/v3' in normalized_base_url or normalized_base_url.endswith('/v3'):
            request_url = f"{normalized_base_url}/chat/completions"
        else:
            # 默认情况下，如果 base_url 是 /api，可能需要 /v1 或 /v3
            # 这里假设如果 base_url 不包含版本号，则使用 /v1
            if '/v1' not in normalized_base_url and '/v3' not in normalized_base_url:
                request_url = f"{normalized_base_url}/v1/chat/completions"
            else:
                request_url = f"{normalized_base_url}/chat/completions"
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                request_url,
                headers=headers,
                json=payload
            )
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]
    
    async def generate_stream(self, prompt: str, **kwargs) -> AsyncGenerator[str, None]:
        """Generate text in streaming mode using Volcengine Doubao API."""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "X-My-Gate-Key": "Huoyuan2026",  # 网关认证密钥
        }
        
        payload = {
            "model": kwargs.get("model", self.model),
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "temperature": kwargs.get("temperature", 0.7),
            "max_tokens": kwargs.get("max_tokens", 2048),
            "stream": True
        }
        
        if "system_prompt" in kwargs:
            payload["messages"].insert(0, {
                "role": "system",
                "content": kwargs["system_prompt"]
            })
        
        # 规范化 base_url 并构建完整 URL（Doubao 流式）
        normalized_base_url = self.base_url.rstrip('/')
        if '/chat/completions' in normalized_base_url:
            request_url = normalized_base_url
        elif '/v3' in normalized_base_url or normalized_base_url.endswith('/v3'):
            request_url = f"{normalized_base_url}/chat/completions"
        else:
            if '/v1' not in normalized_base_url and '/v3' not in normalized_base_url:
                request_url = f"{normalized_base_url}/v1/chat/completions"
            else:
                request_url = f"{normalized_base_url}/chat/completions"
        
        async with httpx.AsyncClient(timeout=120.0) as client:
            async with client.stream(
                "POST",
                request_url,
                headers=headers,
                json=payload
            ) as response:
                try:
                    response.raise_for_status()
                except httpx.HTTPStatusError as e:
                    await e.response.aread()
                    error_msg = e.response.text
                    print(f"Doubao服务器报错内容: {error_msg}")
                    raise
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data = line[6:]
                        if data == "[DONE]":
                            break
                        try:
                            import json
                            chunk = json.loads(data)
                            content = chunk["choices"][0]["delta"].get("content", "")
                            if content:
                                yield content
                        except (json.JSONDecodeError, KeyError, IndexError):
                            continue


class LLMFactory:
    """
    Factory class for creating LLM instances.
    """
    
    _registry: Dict[str, type] = {
        "deepseek": DeepSeekLLM,
        "doubao": DoubaoLLM,
        "claude": ClaudeLLM,
    }
    
    @classmethod
    def create(cls, model_type: str, **kwargs) -> BaseLLM:
        """Create an LLM instance based on the model type."""
        model_type = model_type.lower().strip()
        
        if model_type not in cls._registry:
            supported = ", ".join(cls._registry.keys())
            raise ValueError(
                f"Unsupported model type: '{model_type}'. "
                f"Supported types: {supported}"
            )
        
        return cls._registry[model_type](**kwargs)
    
    @classmethod
    def register(cls, name: str, llm_class: type) -> None:
        """Register a new LLM class."""
        if not issubclass(llm_class, BaseLLM):
            raise TypeError(f"{llm_class} must be a subclass of BaseLLM")
        cls._registry[name.lower()] = llm_class
    
    @classmethod
    def get_supported_models(cls) -> list:
        """Return a list of supported model types."""
        return list(cls._registry.keys())

