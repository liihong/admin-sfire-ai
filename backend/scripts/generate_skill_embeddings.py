"""
批量生成技能Embedding脚本

功能：
1. 为所有启用的技能生成向量
2. 存储到FAISS向量数据库
3. 输出统计信息

使用方法：
    python backend/scripts/generate_skill_embeddings.py

注意：
- 首次运行需要较长���间（取决于技能数量）
- 建议在技能库更新后重新运行
- 需要配置好Embedding API Key
"""
import sys
import os
from pathlib import Path
import asyncio
from loguru import logger

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from db.session import init_db, close_db
from services.skill_embedding import get_skill_embedding_service
import db.session as db_session


async def main():
    """主函数"""
    logger.info("=" * 60)
    logger.info("开始批量生成技能Embedding")
    logger.info("=" * 60)

    # 初始化数据库连接
    await init_db()

    # 获取数据库会话
    async with db_session.async_session_maker() as db:
        # 获取技能Embedding服务
        skill_embedding_service = get_skill_embedding_service()

        # 批量生成
        stats = await skill_embedding_service.batch_generate_embeddings(
            db=db,
            batch_size=10  # 每处理10个记录一次日志
        )

    # 输出统计信息
    logger.info("=" * 60)
    logger.info("批量生成完成！")
    logger.info(f"总计: {stats['total']} 个技能")
    logger.info(f"成功: {stats['success']} 个")
    logger.info(f"失败: {stats['failed']} 个")

    if stats['total'] > 0:
        success_rate = (stats['success'] / stats['total']) * 100
        logger.info(f"成功率: {success_rate:.1f}%")

    logger.info("=" * 60)

    # 关闭数据库连接
    await close_db()

    # 返回是否全部成功
    return stats['failed'] == 0


if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        logger.warning("用户中断操作")
        sys.exit(1)
    except Exception as e:
        logger.exception(f"脚本执行失败: {e}")
        sys.exit(1)
