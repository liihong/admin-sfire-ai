"""
AI Service
AI 对话服务
"""
from typing import List, Optional, AsyncGenerator, Union
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from app.core.config import settings
from app.schemas.ai import ChatMessage
import httpx
import json
import uuid


class AIService:
    """AI对话服务类"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.openai_api_key = settings.OPENAI_API_KEY
        self.openai_base_url = "https://api.openai.com/v1"
    
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
            model: 模型名称
            temperature: 温度参数
            max_tokens: 最大token数
            top_p: Top P采样
            frequency_penalty: 频率惩罚
            presence_penalty: 存在惩罚
        
        Returns:
            对话响应字典
        """
        if not self.openai_api_key:
            raise ValueError("OPENAI_API_KEY 未配置")
        
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
        
        # 调用 OpenAI API
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{self.openai_base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.openai_api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": model,
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
                logger.error(f"OpenAI API error: {response.status_code} - {error_text}")
                raise Exception(f"OpenAI API 请求失败: {error_text}")
            
            data = response.json()
            
            # 格式化响应
            return {
                "id": data.get("id", str(uuid.uuid4())),
                "model": data.get("model", model),
                "message": {
                    "role": data["choices"][0]["message"]["role"],
                    "content": data["choices"][0]["message"]["content"],
                },
                "usage": data.get("usage"),
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
            model: 模型名称
            temperature: 温度参数
            max_tokens: 最大token数
            top_p: Top P采样
            frequency_penalty: 频率惩罚
            presence_penalty: 存在惩罚
        
        Yields:
            JSON 字符串格式的流式数据块
        """
        if not self.openai_api_key:
            raise ValueError("OPENAI_API_KEY 未配置")
        
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
        
        # 调用 OpenAI API（流式）
        async with httpx.AsyncClient(timeout=120.0) as client:
            async with client.stream(
                "POST",
                f"{self.openai_base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.openai_api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": model,
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
                    logger.error(f"OpenAI API error: {response.status_code} - {error_text.decode()}")
                    error_chunk = {
                        "error": {
                            "message": f"OpenAI API 请求失败: {error_text.decode()}",
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
                            return
                        
                        try:
                            # 解析 JSON 数据
                            data = json.loads(data_str)
                            
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

