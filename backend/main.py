"""
SFire Admin API - FastAPI Application Entry Point
"""
import uvicorn
import asyncio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from core.config import settings
from routers import client_router, admin_router, admin_v2_router, client_v2_router
from utils.exceptions import register_exception_handlers
from db.session import init_db, close_db
from db.redis import init_redis, close_redis
from middleware.rate_limiter import RateLimiterMiddleware
from loguru import logger


# 队列Worker管理
queue_workers = []
worker_stop_event = asyncio.Event()

# 定时任务Worker管理
scheduled_task_workers = []
scheduled_task_stop_event = asyncio.Event()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时初始化
    await init_db()
    await init_redis()

    # 启动队列Worker(如果Redis可用)
    from db.redis import get_redis
    redis = await get_redis()

    if redis:
        try:
            # 启动3个Worker并发处理
            worker_count = 3
            for i in range(worker_count):
                worker_id = f"worker-{i+1}"

                from db.queue import conversation_queue_worker
                task = asyncio.create_task(
                    conversation_queue_worker(worker_id, worker_stop_event)
                )
                queue_workers.append(task)

            logger.info(f"✅ [队列] 已启动 {worker_count} 个Worker处理会话保存任务")
        except Exception as e:
            logger.warning(f"⚠️ [队列] Worker启动失败: {e}")
    
    # 启动定时任务Worker
    try:
        from tasks.vip_checker_task import vip_checker_worker
        vip_task = asyncio.create_task(
            vip_checker_worker(scheduled_task_stop_event)
        )
        scheduled_task_workers.append(vip_task)
        logger.info("✅ [定时任务] 已启动VIP过期检查任务")
    except Exception as e:
        logger.warning(f"⚠️ [定时任务] VIP检查任务启动失败: {e}")

    # 开发环境：自动创建缺失的表
    if settings.DEBUG:
        try:
            from db.session import create_tables
            # await create_tables()
        except Exception as e:
            logger.warning(f"自动创建表失败（可能表已存在）: {e}")

    yield

    # 关闭时清理
    # 1. 停止所有队列Worker
    if queue_workers:
        logger.info("正在停止队列Worker...")
        worker_stop_event.set()

        # 等待所有Worker完成
        await asyncio.gather(*queue_workers, return_exceptions=True)
        queue_workers.clear()

        logger.info("✅ [队列] 所有Worker已停止")
    
    # 2. 停止所有定时任务Worker
    if scheduled_task_workers:
        logger.info("正在停止定时任务Worker...")
        scheduled_task_stop_event.set()
        
        # 等待所有定时任务Worker完成
        await asyncio.gather(*scheduled_task_workers, return_exceptions=True)
        scheduled_task_workers.clear()
        
        logger.info("✅ [定时任务] 所有Worker已停止")

    # 3. 关闭Redis和数据库连接
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
    # v2版本接口：技能组装模式
    app.include_router(admin_v2_router, prefix="/api/v2/admin", tags=["B端接口（v2-技能组装）"])
    app.include_router(client_v2_router, prefix="/api/v2/client", tags=["C端接口（v2-执行）"])

    return app


app = create_app()


@app.get("/health")
async def health_check():
    """健康检查接口"""
    from db.queue import ConversationQueue
    queue_size = await ConversationQueue.get_queue_size()

    return {
        "status": "ok",
        "message": "Service is running",
        "queue_size": queue_size,
        "workers_active": len(queue_workers)
    }


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
    )


