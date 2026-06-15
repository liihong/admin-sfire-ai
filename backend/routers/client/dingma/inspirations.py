"""
顶妈（dingma）灵感生成路由
独立于主程序 /inspirations/{id}/generate，注入产品知识库。
"""
from typing import Optional

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from core.client_public_scope import resolve_optional_public_tenant_id
from core.deps import get_current_miniprogram_user
from db import get_db
from models.user import User
from schemas.inspiration import InspirationGenerateRequest, InspirationGenerateResponse
from services.dingma.inspiration_generate import DingmaInspirationGenerateService
from utils.response import success

router = APIRouter()


@router.post("/{inspiration_id}/generate", response_model=dict)
async def dingma_generate_script(
    inspiration_id: int,
    request: InspirationGenerateRequest,
    current_user: User = Depends(get_current_miniprogram_user),
    db: AsyncSession = Depends(get_db),
    scoped_public_tenant_id: Optional[int] = Depends(resolve_optional_public_tenant_id),
):
    """
    dingma 专用：灵感一键生成口播文案，自动注入 copywriting 产品事实。
    主程序 POST /inspirations/{id}/generate 不受影响。
    """
    request.inspiration_id = inspiration_id
    service = DingmaInspirationGenerateService(db)
    result = await service.generate_script(
        user_id=current_user.id,
        request=request,
        scoped_public_tenant_id=scoped_public_tenant_id,
    )
    return success(
        data=InspirationGenerateResponse(**result).model_dump(),
        msg="生成成功",
    )
