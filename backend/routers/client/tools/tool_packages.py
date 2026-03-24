"""
C 端工具包元数据（启用项列表，供小程序/PC 展示）
无需登录：仅公开配置信息
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from db import get_db
from services.tools.tool_package_service import ToolPackageService
from utils.response import success

router = APIRouter()


@router.get("", summary="已启用工具包列表")
async def list_enabled_tool_packages(db: AsyncSession = Depends(get_db)):
    svc = ToolPackageService(db)
    items = await svc.list_enabled_public()
    return success(data=items)


@router.get("/{code}", summary="按 code 获取工具包（须已启用）")
async def get_tool_package_by_code(code: str, db: AsyncSession = Depends(get_db)):
    svc = ToolPackageService(db)
    data = await svc.get_public_by_code(code)
    return success(data=data)
