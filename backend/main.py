"""
SFire Admin API - FastAPI Application Entry Point
"""
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from core.config import settings
from routers import client_router, admin_router
from utils.exceptions import register_exception_handlers
from db.session import init_db, close_db
from db.redis import init_redis, close_redis
from middleware.rate_limiter import RateLimiterMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时初始化
    await init_db()
    await init_redis()
    
    # 开发环境：自动创建缺失的表
    if settings.DEBUG:
        try:
            from db.session import create_tables
            # await create_tables()
        except Exception as e:
            from loguru import logger
            logger.warning(f"自动创建表失败（可能表已存在）: {e}")
    
    yield
    # 关闭时清理
    await close_redis()
    await close_db()


def create_app() -> FastAPI:
    """创建 FastAPI 应用实例"""
    app = FastAPI(
        title=settings.APP_NAME,
        description="SFire Admin 管理后台 API",
        version="1.0.0",
        docs_url="/docs" if settings.DEBUG else None,
        redoc_url="/redoc" if settings.DEBUG else None,
        openapi_url="/openapi.json" if settings.DEBUG else None,
        lifespan=lifespan,
    )

    # 注册 CORS 中间件
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # 注册 API 限流中间件
    app.add_middleware(RateLimiterMiddleware)

    # 注册全局异常处理器
    register_exception_handlers(app)

    # 注册 API 路由
    # C端接口（小程序 & PC官网）：包括认证、项目管理、内容生成、抖音分析等功能
    app.include_router(client_router, prefix="/api/v1/client", tags=["C端接口"])
    # B端接口（管理后台）：包括管理员认证、用户管理、系统配置等功能
    app.include_router(admin_router, prefix="/api/v1/admin", tags=["B端接口"])

    return app


app = create_app()


@app.get("/health")
async def health_check():
    """健康检查接口"""
    return {"status": "ok", "message": "Service is running"}


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
    )


