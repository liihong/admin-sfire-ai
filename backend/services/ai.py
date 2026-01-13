"""
AI Service
AI 对话服务
"""
from typing import List, Optional, AsyncGenerator, Union
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger
import asyncio

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
        self.openai_base_url = "https://api.deepseek.com"

        # HTTP/2 + Gzip 压缩的客户端配置
        # 支持 HTTP/2 以提升性能（头部压缩、多路复用）
        # httpx 会自动处理 gzip 压缩（自动添加 Accept-Encoding: gzip）
        self._client_config = {
            "timeout": httpx.Timeout(120.0, connect=10.0),
            "limits": httpx.Limits(max_keepalive_connections=20, max_connections=100),
            "http2": True,  # 启用 HTTP/2 支持
            "verify": False,  # 验证 SSL 证书
            "follow_redirects": True,
            "trust_env": False,   # ⬅️ 关键：禁用读取系统代理环境变量
        }

    def _update_token_usage_async(self, model_id: str, total_tokens: int) -> None:
        """
        异步更新 token 使用统计（后台任务）

        使用 create_task 创建后台任务，不阻塞主流程
        """
        async def _do_update():
            # 创建独立的数据库会话
            from db.session import async_session_maker
            async with async_session_maker() as db:
                try:
                    # 使用新的会话创建 service
                    llm_service = LLMModelService(db)
                    await llm_service.update_token_usage(model_id, total_tokens)
                    await db.commit()
                except Exception as e:
                    await db.rollback()
                    # 只记录警告，不影响主流程
                    logger.warning(f"Failed to update token usage (async): {e}")

        # 创建后台任务
        asyncio.create_task(_do_update())

    
    async def _get_model_config(self, model_id: str) -> tuple[Optional[str], Optional[str]]:
        """
        根据模型ID获取模型配置（API key 和 base_url）

        Args:
            model_id: 模型ID（可能是数据库ID字符串，或模型标识如 "gpt-4o"）

        Returns:
            (api_key, base_url) 或 (None, None) 如果未找到
        """
        try:
            model = None

            # 优化：直接判断类型，避免 try-except 造成的重复查询
            if model_id.isdigit():
                # 如果是纯数字，作为数据库ID查找
                model = await self.llm_model_service.get_llm_model_by_id(int(model_id))
            else:
                # 否则作为 model_id 查找
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
            # 优先使用 AI_COLLECT 专用配置
            if hasattr(settings, 'AI_COLLECT_API_KEY') and settings.AI_COLLECT_API_KEY:
                api_key = settings.AI_COLLECT_API_KEY
                base_url = settings.AI_COLLECT_BASE_URL or self.openai_base_url
            else:
                # 使用通用配置
                api_key = self.openai_api_key
                base_url = self.openai_base_url
            
            if not api_key:
                raise ValueError("模型未配置 API Key，且环境变量也未配置（请设置 AI_COLLECT_API_KEY 或 OPENAI_API_KEY）")
        
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
        # # 检查 base_url 是否已经包含 /v1，如果没有则添加
        # if '/v1' not in normalized_base_url and not normalized_base_url.endswith('/v1'):
        #     api_url = f"{normalized_base_url}/v1/chat/completions"
        else:
            api_url = f"{normalized_base_url}/chat/completions"

        # 构建请求体
        request_body = {
            "model": actual_model_id,
            "messages": formatted_messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "top_p": top_p,
            "frequency_penalty": frequency_penalty,
            "presence_penalty": presence_penalty,
            "stream": False,
        }

        # 手动序列化JSON,确保正确的编码
        request_body_json = json.dumps(request_body, ensure_ascii=False)
        request_body_size = len(request_body_json.encode('utf-8'))

        # 构建请求头
        # httpx 会自动添加 Accept-Encoding: gzip, deflate
        # 显式添加可以确保压缩被启用
        request_headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json; charset=utf-8",
            "Accept-Encoding": "gzip, deflate",  # 显式启用压缩
            "X-My-Gate-Key": "Huoyuan2026",  # 网关认证密钥
            "Content-Length": str(request_body_size),
        }

        # 调用 API（使用 HTTP/2 和 Gzip 支持）
        async with httpx.AsyncClient(**self._client_config) as client:
            response = await client.post(
                api_url,
                headers=request_headers,
                content=request_body_json.encode('utf-8'),  # 手动编码,使用content而不是json
            )
            
            if response.status_code != 200:
                error_text = response.text

                # 🔍 详细错误日志
                # 查找system prompt长度(可能在任何位置)
                system_prompt_length = 'N/A'
                for msg in formatted_messages:
                    if msg.get('role') == 'system':
                        system_prompt_length = len(msg.get('content', ''))
                        break

                    
                logger.error(f"❌ [API] LLM API请求失败 (非流式):")
                logger.error(f"  - HTTP Status: {response.status_code}")
                logger.error(f"  - API URL: {api_url}")
                logger.error(f"  - Model ID: {actual_model_id}")
                logger.error(f"  - Model Type: {model}")
                logger.error(f"  - Response Headers: {dict(response.headers)}")
                logger.error(f"  - Error Response: {error_text[:1000]}")  # 限制长度
                logger.error(f"  - Request Messages Count: {len(formatted_messages)}")
                logger.error(f"  - System Prompt Length: {system_prompt_length}")

                # 如果是503,提供特别提示
                if response.status_code == 503:
                    logger.error(f"  ⚠️ 503错误可能原因:")
                    logger.error(f"    1. API网关过载或不可用")
                    logger.error(f"    2. Base URL配置错误: {api_url}")
                    logger.error(f"    3. 网关认证密钥(X-My-Gate-Key)无效")
                    logger.error(f"    4. 外部API服务暂时不可用")
                    logger.error(f"    💡 建议: 检查数据库中的base_url和api_key配置")

                raise Exception(f"API 请求失败 (HTTP {response.status_code}): {error_text[:200]}")
            
            data = response.json()

            # 更新 token 使用统计（异步后台任务，不阻塞响应）
            usage = data.get("usage")
            if usage and isinstance(usage, dict):
                total_tokens = usage.get("total_tokens", 0)
                if total_tokens > 0:
                    # 使用异步后台任务更新，不阻塞主流程
                    self._update_token_usage_async(actual_model_id, total_tokens)

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
            # 优先使用 AI_COLLECT 专用配置
            if hasattr(settings, 'AI_COLLECT_API_KEY') and settings.AI_COLLECT_API_KEY:
                api_key = settings.AI_COLLECT_API_KEY
                base_url = settings.AI_COLLECT_BASE_URL or self.openai_base_url
            else:
                # 使用通用配置
                api_key = self.openai_api_key
                base_url = self.openai_base_url
            
            if not api_key:
                raise ValueError("模型未配置 API Key，且环境变量也未配置（请设置 AI_COLLECT_API_KEY 或 OPENAI_API_KEY）")
        
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
        # httpx 会自动添加 Accept-Encoding: gzip, deflate
        # 显式添加可以确保压缩被启用
        request_headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "Accept-Encoding": "gzip, deflate",  # 显式启用压缩
            "X-My-Gate-Key": "Huoyuan2026",  # 网关认证密钥
        }

        # 规范化 base_url 并构建完整 URL
        normalized_base_url = base_url.rstrip('/')
        if '/chat/completions' in normalized_base_url:
            normalized_base_url = normalized_base_url.split('/chat/completions')[0]
        # 检查 base_url 是否已经包含 /v1，如果没有则添加
        # if '/v1' not in normalized_base_url and not normalized_base_url.endswith('/v1'):
        #     api_url = f"{normalized_base_url}/v1/chat/completions"
        else:
            api_url = f"{normalized_base_url}/chat/completions"

        # 🔍 调试日志: 打印请求详情
        logger.info(f"🔍 [DEBUG] API Request Details:")
        logger.info(f"  - API URL: {api_url}")
        logger.info(f"  - Model: {actual_model_id}")
        logger.info(f"  - Messages count: {len(formatted_messages)}")
        logger.info(f"  - HTTP/2 enabled: True")
        logger.info(f"  - Gzip compression: enabled")
        logger.info(f"  - Request headers keys: {list(request_headers.keys())}")

        # 打印消息结构(但不打印完整内容,避免日志过长)
        for i, msg in enumerate(formatted_messages):
            role = msg.get('role', 'unknown')
            content_len = len(msg.get('content', ''))
            logger.info(f"  - Message {i+1}: role={role}, content_length={content_len}")

        # 构建请求体
        request_body = {
            "model": actual_model_id,
            "messages": formatted_messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "top_p": top_p,
            "frequency_penalty": frequency_penalty,
            "presence_penalty": presence_penalty,
            "stream": True,
        }

        # 计算并打印请求体大小
        # 手动序列化JSON,使用ensure_ascii=False支持中文
        request_body_json = json.dumps(request_body, ensure_ascii=False)
        request_body_size = len(request_body_json.encode('utf-8'))
        logger.info(f"  - Request body size: {request_body_size} bytes ({request_body_size/1024:.2f} KB)")
        logger.info(f"  - Estimated compressed size: ~{request_body_size//3} bytes (gzip)")

        # 检查是否有可能导致问题的特殊字符
        if request_body_size > 50000:  # 50KB
            logger.warning(f"  ⚠️ Large request body detected: {request_body_size} bytes")
            logger.warning(f"  This may cause API gateway 503 errors")
            logger.warning(f"  💡 Gzip compression will reduce this by ~70%")

        # 使用content参数手动发送JSON,确保正确的编码
        request_headers["Content-Length"] = str(request_body_size)

        # 使用 HTTP/2 + Gzip 压缩的客户端
        async with httpx.AsyncClient(**self._client_config) as client:
            async with client.stream(
                "POST",
                api_url,
                headers=request_headers,
                content=request_body_json.encode('utf-8'),  # 手动编码,使用content而不是json
            ) as response:
                if response.status_code != 200:
                    error_text = await response.aread()
                    error_text_str = error_text.decode('utf-8', errors='ignore') if error_text else ""

                    # 🔍 详细错误日志
                    # 查找system prompt长度(可能在任何位置)
                    system_prompt_length = 'N/A'
                    for msg in formatted_messages:
                        if msg.get('role') == 'system':
                            system_prompt_length = len(msg.get('content', ''))
                            break

                    logger.error(f"{msg}")    
                    logger.error(f"❌ [API] LLM API请求失败:")
                    logger.error(f"  - HTTP Status: {response.status_code}")
                    logger.error(f"  - API URL: {api_url}")
                    logger.error(f"  - Model ID: {actual_model_id}")
                    logger.error(f"  - Model Type: {model}")
                    logger.error(f"  - Response Headers: {dict(response.headers)}")
                    logger.error(f"  - Error Response: {error_text_str[:1000]}")  # 限制长度
                    logger.error(f"  - Request Messages Count: {len(formatted_messages)}")
                    logger.error(f"  - System Prompt Length: {system_prompt_length}")

                    # 如果是503,提供特别提示
                    if response.status_code == 503:
                        logger.error(f"  ⚠️ 503错误可能原因:")
                        logger.error(f"    1. API网关过载或不可用")
                        logger.error(f"    2. Base URL配置错误: {api_url}")
                        logger.error(f"    3. 网关认证密钥(X-My-Gate-Key)无效")
                        logger.error(f"    4. 外部API服务暂时不可用")
                        logger.error(f"    💡 建议: 检查数据库中的base_url和api_key配置")

                    error_chunk = {
                        "error": {
                            "message": f"API 请求失败 (HTTP {response.status_code}): {error_text_str[:200]}",
                            "type": "APIError",
                            "status_code": response.status_code,
                            "api_url": api_url,
                            "model_id": actual_model_id
                        }
                    }
                    yield json.dumps(error_chunk)
                    return
                
                # 检查响应内容类型，如果不是 SSE 格式，返回错误
                content_type = response.headers.get("content-type", "").lower()
                if "text/event-stream" not in content_type and "text/plain" not in content_type and "application/json" not in content_type:
                    # 可能是 HTML 或其他格式的错误响应
                    error_text = await response.aread()
                    error_msg = error_text.decode('utf-8', errors='ignore')[:500]  # 限制长度
                    logger.error(f"API returned non-SSE response: {content_type} - {error_msg[:200]}")
                    error_chunk = {
                        "error": {
                            "message": f"API 返回了非 SSE 格式的响应 (content-type: {content_type})，可能是认证失败或 URL 错误",
                            "type": "InvalidResponseError",
                            "details": error_msg[:200] if len(error_msg) > 0 else "无错误详情"
                        }
                    }
                    yield json.dumps(error_chunk)
                    return
                
                # 解析 SSE 流
                buffer = ""
                async for chunk in response.aiter_text():
                    # 检查第一个 chunk 是否是 HTML 响应
                    if chunk.strip().startswith("<!DOCTYPE") or chunk.strip().startswith("<html"):
                        logger.error(f"API returned HTML response instead of SSE stream")
                        error_chunk = {
                            "error": {
                                "message": "API 返回了 HTML 响应而不是 SSE 流，可能是认证失败或 URL 错误",
                                "type": "InvalidResponseError",
                                "details": chunk[:200] if len(chunk) > 0 else "无错误详情"
                            }
                        }
                        yield json.dumps(error_chunk)
                        return
                    
                    buffer += chunk
                    
                    # 处理完整的 SSE 消息（以 \n\n 分隔）
                    while "\n\n" in buffer:
                        line, buffer = buffer.split("\n\n", 1)
                        
                        if not line.startswith("data: "):
                            continue
                        
                        data_str = line[6:]  # 移除 "data: " 前缀
                        
                        # 检查是否是结束标记
                        if data_str.strip() == "[DONE]":
                            # 流结束时更新 token 使用统计（异步后台任务，不阻塞响应）
                            if usage_info and usage_info.get("total_tokens", 0) > 0:
                                # 使用异步后台任务更新，不阻塞主流程
                                self._update_token_usage_async(actual_model_id, usage_info["total_tokens"])
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

