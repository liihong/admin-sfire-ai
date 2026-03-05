"""
Client Coze Endpoints
C端 Coze 工作流接口（小程序 & PC官网）
支持热点榜单等功能，通过 Coze 工作流 API 获取数据
"""
import json
import httpx
from typing import List, Any
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from models.user import User
from core.deps import get_current_miniprogram_user
from core.config import settings
from utils.response import success
from utils.exceptions import ServerErrorException
from loguru import logger

router = APIRouter()

# Coze 工作流 API
COZE_WORKFLOW_RUN_URL = "https://api.coze.cn/v1/workflow/run"
COZE_REQUEST_TIMEOUT = 90


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
    从 Coze 工作流返回的 data 中提取热点列表
    支持多种嵌套结构：直接数组、output[0].data、data 等
    """
    if isinstance(coze_data, list):
        return coze_data

    if isinstance(coze_data, dict):
        # 优先取 data 数组
        if "data" in coze_data and isinstance(coze_data["data"], list):
            return coze_data["data"]
        # 取 output 第一个元素的 data
        if "output" in coze_data and isinstance(coze_data["output"], list) and len(coze_data["output"]) > 0:
            first_output = coze_data["output"][0]
            if isinstance(first_output, dict) and "data" in first_output and isinstance(first_output["data"], list):
                return first_output["data"]
            if isinstance(first_output, list):
                return first_output

    return []


def _validate_and_normalize_item(item: Any, index: int) -> dict | None:
    """校验并标准化单条热点数据"""
    if not isinstance(item, dict):
        return None
    title = item.get("title") or item.get("word") or ""
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

    通过 Coze 工作流 API 获取热点数据，返回格式：
    [{"hot", "id", "mobileUrl", "timestamp", "title", "url"}, ...]

    路径：GET /api/v1/client/coze/hotspot-list
    """
    pat_token = settings.COZE_PAT_TOKEN
    workflow_id = settings.COZE_HOTSPOT_WORKFLOW_ID

    if not pat_token or not workflow_id:
        logger.warning("Coze 热点工作流未配置: COZE_PAT_TOKEN 或 COZE_HOTSPOT_WORKFLOW_ID 为空")
        raise ServerErrorException("热点榜单服务未配置，请联系管理员")

    try:
        async with httpx.AsyncClient(timeout=COZE_REQUEST_TIMEOUT) as client:
            response = await client.post(
                COZE_WORKFLOW_RUN_URL,
                headers={
                    "Authorization": f"Bearer {pat_token}",
                    "Content-Type": "application/json",
                },
                json={
                    "workflow_id": workflow_id,
                    "parameters": {},
                },
            )

            if response.status_code != 200:
                logger.error(f"Coze 工作流请求失败: status={response.status_code}, body={response.text[:500]}")
                raise ServerErrorException("获取热点榜单失败，请稍后重试")

            body = response.json()
            coze_code = body.get("code", -1)
            if coze_code != 0:
                coze_msg = body.get("msg", "未知错误")
                logger.error(f"Coze 工作流执行失败: code={coze_code}, msg={coze_msg}")
                raise ServerErrorException(f"获取热点榜单失败: {coze_msg}")

            data_raw = body.get("data")
            if not data_raw:
                logger.warning("Coze 工作流返回的 data 为空")
                return success(data=[], msg="暂无热点数据")

            # data 可能是 JSON 字符串，需二次解析
            if isinstance(data_raw, str):
                try:
                    parsed = json.loads(data_raw)
                except json.JSONDecodeError as e:
                    logger.error(f"解析 Coze data 失败: {e}")
                    raise ServerErrorException("热点数据解析失败")
            else:
                parsed = data_raw

            raw_list = _extract_hotspot_list_from_coze_response(parsed)
            result = []
            for idx, item in enumerate(raw_list):
                normalized = _validate_and_normalize_item(item, idx)
                if normalized:
                    result.append(normalized)

            return success(data=result, msg="获取成功")

    except ServerErrorException:
        raise
    except httpx.TimeoutException:
        logger.error("Coze 工作流请求超时")
        raise ServerErrorException("请求超时，请稍后重试")
    except Exception as e:
        logger.exception(f"Coze 热点榜单异常: {e}")
        raise ServerErrorException("获取热点榜单失败，请稍后重试")
