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

from app.core.config import settings


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
            "Content-Type": "application/json"
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
            "Content-Type": "application/json"
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
        
        async with httpx.AsyncClient(timeout=120.0) as client:
            async with client.stream(
                "POST",
                f"{self.base_url}/v1/chat/completions",
                headers=headers,
                json=payload
            ) as response:
                response.raise_for_status()
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
            "Content-Type": "application/json"
        }
        
        if is_official_api and not use_openai_format:
            headers = {
                "x-api-key": self.api_key,
                "anthropic-version": self.API_VERSION,
                "Content-Type": "application/json"
            }
        
        base_url = self.base_url.rstrip("/")
        
        if use_openai_format:
            messages = []
            if "system_prompt" in kwargs and kwargs["system_prompt"]:
                messages.append({"role": "system", "content": kwargs["system_prompt"]})
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
            payload = {
                "model": kwargs.get("model", self.model),
                "max_tokens": kwargs.get("max_tokens", 2048),
                "messages": [{"role": "user", "content": prompt}]
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
            "Content-Type": "application/json"
        }
        
        if is_official_api and not use_openai_format:
            headers = {
                "x-api-key": self.api_key,
                "anthropic-version": self.API_VERSION,
                "Content-Type": "application/json"
            }
        
        if use_openai_format:
            messages = []
            if "system_prompt" in kwargs and kwargs["system_prompt"]:
                messages.append({"role": "system", "content": kwargs["system_prompt"]})
            messages.append({"role": "user", "content": prompt})
            
            payload = {
                "model": kwargs.get("model", self.model),
                "messages": messages,
                "temperature": kwargs.get("temperature", 0.7),
                "max_tokens": kwargs.get("max_tokens", 2048),
                "stream": True
            }
            url = f"{self.base_url}/v1/chat/completions"
        else:
            payload = {
                "model": kwargs.get("model", self.model),
                "max_tokens": kwargs.get("max_tokens", 2048),
                "messages": [{"role": "user", "content": prompt}],
                "stream": True
            }
            if "temperature" in kwargs:
                payload["temperature"] = kwargs["temperature"]
            if "system_prompt" in kwargs and kwargs["system_prompt"]:
                payload["system"] = kwargs["system_prompt"]
            url = f"{self.base_url}/v1/messages"
        
        async with httpx.AsyncClient(timeout=120.0) as client:
            async with client.stream("POST", url, headers=headers, json=payload) as response:
                response.raise_for_status()
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
            "Content-Type": "application/json"
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
                f"{self.base_url}/chat/completions",
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
            "Content-Type": "application/json"
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
        
        async with httpx.AsyncClient(timeout=120.0) as client:
            async with client.stream(
                "POST",
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload
            ) as response:
                response.raise_for_status()
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

