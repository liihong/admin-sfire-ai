"""
Client Coze Endpoints
C端 Coze 工作流接口（小程序 & PC官网）
支持热点榜单等功能，通过 Coze 工作流 API 获取数据
"""
import asyncio
import json
from typing import List, Any
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from models.user import User
from core.deps import get_current_miniprogram_user
from core.config import settings
from utils.response import success
from utils.exceptions import ServerErrorException
from loguru import logger
from db.redis import RedisCache

router = APIRouter()

# 热点榜单缓存配置
HOTSPOT_CACHE_KEY = "coze:hotspot-list"
HOTSPOT_CACHE_TTL = 300  # 5 分钟
HOTSPOT_STREAM_TIMEOUT = 30  # Coze 工作流超时（秒）


class HotspotItem(BaseModel):
    """热点榜单项（Coze 工作流返回格式）"""
    hot: str = Field(..., description="热度值")
    id: str = Field(..., description="热点ID")
    mobileUrl: str = Field(default="", description="移动端链接")
    timestamp: str = Field(default="", description="更新时间")
    title: str = Field(..., description="热点标题")
    url: str = Field(default="", description="链接")


def _extract_hotspot_list_from_coze_response(coze_data: Any) -> List[dict]:
    """
    从 Coze 工作流返回中提取热点列表
    支持多种嵌套结构：直接数组、output[0].data、data、original_result 等
    """
    if isinstance(coze_data, str):
        try:
            coze_data = json.loads(coze_data)
        except json.JSONDecodeError:
            return []

    if isinstance(coze_data, list):
        return coze_data

    if isinstance(coze_data, dict):
        # 1. 顶层 data 数组
        if "data" in coze_data and isinstance(coze_data["data"], list):
            return coze_data["data"]
        # 2. original_result（Coze 内部格式）
        if "original_result" in coze_data and coze_data["original_result"] is not None:
            return _extract_hotspot_list_from_coze_response(coze_data["original_result"])
        # 3. output[0].data 等
        if "output" in coze_data and isinstance(coze_data["output"], list) and len(coze_data["output"]) > 0:
            first_output = coze_data["output"][0]
            if isinstance(first_output, dict):
                for key in ("data", "list", "items", "result", "results"):
                    if key in first_output and isinstance(first_output[key], list):
                        return first_output[key]
            if isinstance(first_output, list):
                return first_output
        # 4. 其他常见键
        for key in ("list", "items", "result", "results"):
            if key in coze_data and isinstance(coze_data[key], list):
                return coze_data[key]

    return []


def _validate_and_normalize_item(item: Any) -> dict | None:
    """校验并标准化单条热点数据"""
    if not isinstance(item, dict):
        return None
    title = (
        item.get("title")
        or item.get("word")
        or item.get("keyword")
        or item.get("name")
        or ""
    )
    if not title:
        return None
    return {
        "hot": str(item.get("hot", "")),
        "id": str(item.get("id", "")),
        "mobileUrl": str(item.get("mobileUrl", "") or item.get("url", "")),
        "timestamp": str(item.get("timestamp", "")),
        "title": str(title),
        "url": str(item.get("url", "") or item.get("mobileUrl", "")),
    }


@router.get("/hotspot-list", summary="获取抖音热点榜单")
async def get_hotspot_list(
    current_user: User = Depends(get_current_miniprogram_user),
):
    """
    获取抖音热点榜单

    通过 Coze 工作流 API（stream）获取热点数据，返回格式：
    [{"hot", "id", "mobileUrl", "timestamp", "title", "url"}, ...]

    路径：GET /api/v1/client/coze/hotspot-list
    """
    from cozepy import Coze, TokenAuth, COZE_CN_BASE_URL, WorkflowEventType
    from cozepy.exception import CozeAPIError

    pat_token = settings.COZE_PAT_TOKEN
    workflow_id = settings.COZE_HOTSPOT_WORKFLOW_ID

    if not pat_token or not workflow_id:
        logger.warning("Coze 热点工作流未配置: COZE_PAT_TOKEN 或 COZE_HOTSPOT_WORKFLOW_ID 为空")
        raise ServerErrorException("热点榜单服务未配置，请联系管理员")

    # 尝试从缓存获取
    try:
        cached = await RedisCache.get_json(HOTSPOT_CACHE_KEY)
        if isinstance(cached, list):
            return success(data=cached, msg="获取成功")
    except Exception:
        pass  # 缓存不可用时继续请求 Coze

    try:
        coze = Coze(
            auth=TokenAuth(token=pat_token),
            base_url=COZE_CN_BASE_URL,
        )

        def _run_stream() -> List[Any]:
            """同步执行 stream，收集所有 MESSAGE 的 content 和 ext"""
            items: List[Any] = []
            stream = coze.workflows.runs.stream(workflow_id=workflow_id)
            for event in stream:
                if event.event == WorkflowEventType.MESSAGE and event.message:
                    msg = event.message
                    if msg.content:
                        items.append(("content", msg.content))
                    if msg.ext:
                        items.append(("ext", msg.ext))
                elif event.event == WorkflowEventType.ERROR and event.error:
                    logger.error(f"Coze 工作流错误: {event.error}")
                    raise RuntimeError("获取热点榜单失败，请稍后重试")
                elif event.event == WorkflowEventType.INTERRUPT and event.interrupt:
                    logger.warning(f"Coze 工作流被中断: {event.interrupt}")
            return items

        # 在线程池中执行同步 stream，避免阻塞事件循环，并设置超时
        items = await asyncio.wait_for(
            asyncio.to_thread(_run_stream),
            timeout=HOTSPOT_STREAM_TIMEOUT,
        )

        if not items:
            logger.warning("Coze 工作流未返回有效数据")
            return success(data=[], msg="暂无热点数据")

        # 遍历所有 content/ext，找到包含 data 数组的有效数据
        raw_list: List[dict] = []
        for tag, val in items:
            if tag == "content":
                try:
                    p = json.loads(val)
                except json.JSONDecodeError:
                    continue
                if isinstance(p, str):
                    try:
                        p = json.loads(p)
                    except json.JSONDecodeError:
                        pass
            else:
                p = val
                if isinstance(p, str):
                    try:
                        p = json.loads(p)
                    except json.JSONDecodeError:
                        continue
            raw = _extract_hotspot_list_from_coze_response(p)
            if raw:
                raw_list = raw
                break

        if not raw_list:
            logger.warning(f"Coze 无法解析出热点列表，共 {len(items)} 条消息")
            return success(data=[], msg="暂无热点数据")

        result = []
        for item in raw_list:
            normalized = _validate_and_normalize_item(item)
            if normalized:
                result.append(normalized)

        # 写入缓存
        try:
            await RedisCache.set_json(HOTSPOT_CACHE_KEY, result, expire=HOTSPOT_CACHE_TTL)
        except Exception:
            pass  # 缓存写入失败不影响返回

        return success(data=result, msg="获取成功")

    except ServerErrorException:
        raise
    except asyncio.TimeoutError:
        logger.error("Coze 热点工作流请求超时")
        raise ServerErrorException("获取热点榜单超时，请稍后重试")
    except CozeAPIError as e:
        logger.warning(
            "Coze API 热点榜单失败: code={} msg={} logid={}",
            e.code,
            e.msg,
            e.logid,
        )
        # 4100：实测为 PAT 无效 / 鉴权失败（见 cozepy stream_run 返回）
        if e.code == 4100 or (
            e.msg and "authentication" in e.msg.lower()
        ):
            raise ServerErrorException(
                "热点榜单服务鉴权失败，请检查服务端 COZE_PAT_TOKEN 是否在 Coze 开放平台有效"
            )
        raise ServerErrorException(
            f"热点榜单服务暂时不可用（Coze 错误码 {e.code}），请稍后重试"
        )
    except RuntimeError as e:
        raise ServerErrorException(str(e))
    except Exception as e:
        logger.exception(f"Coze 热点榜单异常: {e}")
        raise ServerErrorException("获取热点榜单失败，请稍后重试")
