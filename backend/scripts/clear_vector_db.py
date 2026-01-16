"""
清空向量数据库脚本
删除FAISS索引文件和元数据文件，重新初始化向量数据库
"""
import os
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from loguru import logger
from services.vector_db import VectorDBService


def clear_vector_db():
    """
    清空向量数据库
    删除所有FAISS索引文件和元数据文件
    """
    logger.info("=" * 50)
    logger.info("开始清空向量数据库...")
    logger.info("=" * 50)
    
    # 获取向量数据库存储路径
    storage_dir = os.path.join(os.path.dirname(__file__), "..", "storage")
    index_path = os.path.join(storage_dir, "faiss_index.index")
    metadata_path = os.path.join(storage_dir, "faiss_index.meta")
    
    deleted_files = []
    
    # 删除索引文件
    if os.path.exists(index_path):
        try:
            os.remove(index_path)
            deleted_files.append(index_path)
            logger.info(f"已删除索引文件: {index_path}")
        except Exception as e:
            logger.error(f"删除索引文件失败: {e}")
            return False
    
    # 删除元数据文件
    if os.path.exists(metadata_path):
        try:
            os.remove(metadata_path)
            deleted_files.append(metadata_path)
            logger.info(f"已删除元数据文件: {metadata_path}")
        except Exception as e:
            logger.error(f"删除元数据文件失败: {e}")
            return False
    
    if not deleted_files:
        logger.warning("未找到向量数据库文件，可能已经是空的状态")
    else:
        logger.info(f"成功删除 {len(deleted_files)} 个文件")
    
    # 重新初始化向量数据库（使用1024维）
    try:
        logger.info("重新初始化向量数据库（维度: 1024）...")
        vector_db = VectorDBService(dimension=1024)
        stats = vector_db.get_stats()
        logger.info(f"向量数据库已重新初始化: {stats}")
    except Exception as e:
        logger.error(f"重新初始化向量数据库失败: {e}")
        return False
    
    logger.info("=" * 50)
    logger.info("向量数据库清空完成！")
    logger.info("=" * 50)
    
    return True


if __name__ == "__main__":
    success = clear_vector_db()
    sys.exit(0 if success else 1)
















