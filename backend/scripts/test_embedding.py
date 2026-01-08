"""
测试Embedding服务配置
验证阿里云DashScope Embedding API是否正常工作
"""
import asyncio
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from services.embedding import get_embedding_service
from core.config import settings
from loguru import logger


async def test_embedding():
    """测试Embedding服务"""
    logger.info("=" * 60)
    logger.info("开始测试Embedding服务配置")
    logger.info("=" * 60)

    # 打印配置信息
    logger.info(f"EMBEDDING_PROVIDER: {settings.EMBEDDING_PROVIDER}")
    logger.info(f"EMBEDDING_BASE_URL: {settings.EMBEDDING_BASE_URL}")
    logger.info(f"EMBEDDING_MODEL: {settings.EMBEDDING_MODEL}")
    logger.info(f"EMBEDDING_API_KEY: {settings.EMBEDDING_API_KEY[:20]}..." if settings.EMBEDDING_API_KEY else "未配置")
    logger.info("=" * 60)

    # 获取Embedding服务实例
    embedding_service = get_embedding_service()

    # 测试文本
    test_text = "这是一个测试文本，用于验证Embedding服务是否正常工作。"

    logger.info(f"测试文本: {test_text}")
    logger.info("正在生成向量...")

    try:
        # 生成向量
        embedding = await embedding_service.generate_embedding(test_text)

        if embedding is not None:
            logger.success(f"✓ 向量生成成功！")
            logger.info(f"向量维度: {len(embedding)}")
            logger.info(f"向量前10个值: {embedding[:10]}")
            logger.info("=" * 60)
            logger.success("Embedding服务配置正确，工作正常！")
            logger.info("=" * 60)
            return True
        else:
            logger.error("✗ 向量生成失败！返回None")
            logger.error("请检查API Key和Base URL配置")
            return False

    except Exception as e:
        logger.error(f"✗ 向量生成失败！")
        logger.error(f"错误信息: {e}")
        logger.error("=" * 60)
        logger.error("请检查以下配置：")
        logger.error("1. EMBEDDING_API_KEY 是否正确")
        logger.error("2. EMBEDDING_BASE_URL 是否可访问")
        logger.error("3. EMBEDDING_MODEL 是否支持")
        logger.error("=" * 60)
        return False


if __name__ == "__main__":
    success = asyncio.run(test_embedding())
    sys.exit(0 if success else 1)
