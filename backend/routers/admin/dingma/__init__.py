"""
顶妈（dingma）管理后台路由
"""
from fastapi import APIRouter

from .product_knowledge import router as product_knowledge_router

dingma_admin_router = APIRouter()

dingma_admin_router.include_router(
    product_knowledge_router,
    prefix="/product-knowledge",
    tags=["顶妈-产品知识库"],
)
