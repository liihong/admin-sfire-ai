"""
AI Service
AI 对话服务
"""
from typing import List, Optional, AsyncGenerator, Union
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from core.config import settings
from schemas.ai import ChatMessage
from services.llm_model import LLMModelService
import httpx
import json
import uuid


class AIService:
    """AI对话服务类"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.llm_model_service = LLMModelService(db)
        # 兼容旧代码：如果没有配置模型，使用环境变量
        self.openai_api_key = settings.OPENAI_API_KEY
        self.openai_base_url = "https://api.openai.com/v1"
    
    async def _get_model_config(self, model_id: str) -> tuple[Optional[str], Optional[str]]:
        """
        根据模型ID获取模型配置（API key 和 base_url）
        
        Args:
            model_id: 模型ID（可能是数据库ID字符串，或模型标识如 "gpt-4o"）
        
        Returns:
            (api_key, base_url) 或 (None, None) 如果未找到
        """
        try:
            # 先尝试作为数据库ID查找
            try:
                db_id = int(model_id)
                model = await self.llm_model_service.get_llm_model_by_id(db_id)
            except (ValueError, Exception) as e:
                # 如果转换失败，尝试作为 model_id 查找
                model = await self.llm_model_service.get_llm_model_by_model_id(model_id)
            
            if model:
                if model.api_key and model.is_enabled:
                    base_url = model.base_url or self.llm_model_service.DEFAULT_BASE_URLS.get(model.provider)
                    # 规范化 base_url：移除末尾斜杠和路径部分
                    if base_url:
                        base_url = base_url.rstrip('/')
                        # 移除 /chat/completions 等路径（如果存在）
                        if '/chat/completions' in base_url:
                            base_url = base_url.split('/chat/completions')[0]
                    
                    return model.api_key, base_url
        except Exception as e:
            logger.warning(f"Failed to get model config for {model_id}: {e}")
        
        return None, None
    
    async def chat(
        self,
        messages: List[Union[dict, ChatMessage]],
        model: str = "gpt-3.5-turbo",
        temperature: float = 0.7,
        max_tokens: int = 2000,
        top_p: float = 1.0,
        frequency_penalty: float = 0.0,
        presence_penalty: float = 0.0,
    ) -> dict:
        """
        非流式对话
        
        Args:
            messages: 消息列表
            model: 模型ID（数据库ID字符串或模型标识）
            temperature: 温度参数
            max_tokens: 最大token数
            top_p: Top P采样
            frequency_penalty: 频率惩罚
            presence_penalty: 存在惩罚
        
        Returns:
            对话响应字典
        """
        # 尝试从数据库获取模型配置
        api_key, base_url = await self._get_model_config(model)
        
        # 如果数据库中没有配置，使用环境变量（向后兼容）
        if not api_key:
            api_key = self.openai_api_key
            base_url = self.openai_base_url
            if not api_key:
                raise ValueError("模型未配置 API Key，且环境变量 OPENAI_API_KEY 也未配置")
        
        # 转换消息格式（支持ChatMessage对象或字典）
        formatted_messages = []
        for msg in messages:
            if isinstance(msg, dict):
                formatted_messages.append(msg)
            else:
                formatted_messages.append({
                    "role": msg.role,
                    "content": msg.content
                })
        
        # 确定实际使用的模型标识（从数据库模型配置中获取 model_id）
        actual_model_id = model
        try:
            try:
                db_id = int(model)
                llm_model = await self.llm_model_service.get_llm_model_by_id(db_id)
                if llm_model:
                    actual_model_id = llm_model.model_id
            except (ValueError, Exception):
                # 如果 model 不是数字ID，直接使用
                pass
        except Exception:
            pass
        
        # 规范化 base_url 并构建完整 URL
        normalized_base_url = base_url.rstrip('/')
        if '/chat/completions' in normalized_base_url:
            normalized_base_url = normalized_base_url.split('/chat/completions')[0]
        api_url = f"{normalized_base_url}/chat/completions"
        
        # 调用 API
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                api_url,
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": actual_model_id,
                    "messages": formatted_messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                    "top_p": top_p,
                    "frequency_penalty": frequency_penalty,
                    "presence_penalty": presence_penalty,
                    "stream": False,
                },
            )
            
            if response.status_code != 200:
                error_text = response.text
                logger.error(f"API error: {response.status_code} - {error_text}")
                raise Exception(f"API 请求失败: {error_text}")
            
            data = response.json()
            
            # 更新 token 使用统计
            usage = data.get("usage")
            if usage and isinstance(usage, dict):
                total_tokens = usage.get("total_tokens", 0)
                if total_tokens > 0:
                    try:
                        # 使用实际的模型标识更新 token 使用量
                        await self.llm_model_service.update_token_usage(actual_model_id, total_tokens)
                    except Exception as e:
                        logger.warning(f"Failed to update token usage: {e}")
            
            # 格式化响应
            return {
                "id": data.get("id", str(uuid.uuid4())),
                "model": data.get("model", actual_model_id),
                "message": {
                    "role": data["choices"][0]["message"]["role"],
                    "content": data["choices"][0]["message"]["content"],
                },
                "usage": usage,
                "finish_reason": data["choices"][0].get("finish_reason"),
            }
    
    async def stream_chat(
        self,
        messages: List[Union[dict, ChatMessage]],
        model: str = "gpt-3.5-turbo",
        temperature: float = 0.7,
        max_tokens: int = 2000,
        top_p: float = 1.0,
        frequency_penalty: float = 0.0,
        presence_penalty: float = 0.0,
    ) -> AsyncGenerator[str, None]:
        """
        SSE 流式对话
        
        Args:
            messages: 消息列表
            model: 模型ID（数据库ID字符串或模型标识）
            temperature: 温度参数
            max_tokens: 最大token数
            top_p: Top P采样
            frequency_penalty: 频率惩罚
            presence_penalty: 存在惩罚
        
        Yields:
            JSON 字符串格式的流式数据块
        """
        # 尝试从数据库获取模型配置
        api_key, base_url = await self._get_model_config(model)
        
        # 如果数据库中没有配置，使用环境变量（向后兼容）
        if not api_key:
            api_key = self.openai_api_key
            base_url = self.openai_base_url
            if not api_key:
                raise ValueError("模型未配置 API Key，且环境变量 OPENAI_API_KEY 也未配置")
        
        # 转换消息格式（支持ChatMessage对象或字典）
        formatted_messages = []
        for msg in messages:
            if isinstance(msg, dict):
                formatted_messages.append(msg)
            else:
                formatted_messages.append({
                    "role": msg.role,
                    "content": msg.content
                })
        
        # 确定实际使用的模型标识（从数据库模型配置中获取 model_id）
        actual_model_id = model
        try:
            try:
                db_id = int(model)
                llm_model = await self.llm_model_service.get_llm_model_by_id(db_id)
                if llm_model:
                    actual_model_id = llm_model.model_id
            except (ValueError, Exception):
                # 如果 model 不是数字ID，直接使用
                pass
        except Exception:
            pass
        
        # 调用 API（流式）
        usage_info = None
        
        # 构建请求头
        request_headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        
        # 规范化 base_url 并构建完整 URL
        normalized_base_url = base_url.rstrip('/')
        if '/chat/completions' in normalized_base_url:
            normalized_base_url = normalized_base_url.split('/chat/completions')[0]
        api_url = f"{normalized_base_url}/chat/completions"
        
        async with httpx.AsyncClient(timeout=120.0) as client:
            async with client.stream(
                "POST",
                api_url,
                headers=request_headers,
                json={
                    "model": actual_model_id,
                    "messages": formatted_messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                    "top_p": top_p,
                    "frequency_penalty": frequency_penalty,
                    "presence_penalty": presence_penalty,
                    "stream": True,
                },
            ) as response:
                if response.status_code != 200:
                    error_text = await response.aread()
                    logger.error(f"API error: {response.status_code} - {error_text.decode()}")
                    error_chunk = {
                        "error": {
                            "message": f"API 请求失败: {error_text.decode()}",
                            "type": "APIError"
                        }
                    }
                    yield json.dumps(error_chunk)
                    return
                
                # 解析 SSE 流
                buffer = ""
                async for chunk in response.aiter_text():
                    buffer += chunk
                    
                    # 处理完整的 SSE 消息（以 \n\n 分隔）
                    while "\n\n" in buffer:
                        line, buffer = buffer.split("\n\n", 1)
                        
                        if not line.startswith("data: "):
                            continue
                        
                        data_str = line[6:]  # 移除 "data: " 前缀
                        
                        # 检查是否是结束标记
                        if data_str.strip() == "[DONE]":
                            # 流结束时更新 token 使用统计
                            if usage_info and usage_info.get("total_tokens", 0) > 0:
                                try:
                                    # 使用实际的模型标识更新 token 使用量
                                    await self.llm_model_service.update_token_usage(actual_model_id, usage_info["total_tokens"])
                                except Exception as e:
                                    logger.warning(f"Failed to update token usage: {e}")
                            return
                        
                        try:
                            # 解析 JSON 数据
                            data = json.loads(data_str)
                            
                            # 保存 usage 信息（通常在最后一个 chunk 中）
                            if "usage" in data:
                                usage_info = data["usage"]
                            
                            # 提取 delta content
                            choices = data.get("choices", [])
                            if choices and "delta" in choices[0]:
                                delta = choices[0]["delta"]
                                content = delta.get("content", "")
                                
                                if content:
                                    # 格式化为前端需要的格式
                                    chunk_data = {
                                        "id": data.get("id", ""),
                                        "delta": {
                                            "content": content,
                                            "role": delta.get("role"),
                                        },
                                        "finish_reason": choices[0].get("finish_reason"),
                                    }
                                    yield json.dumps(chunk_data)
                        except json.JSONDecodeError as e:
                            logger.warning(f"Failed to parse SSE data: {data_str[:100]} - {e}")
                            continue

