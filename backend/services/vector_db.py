"""
向量数据库服务
使用FAISS进行向量存储和相似度搜索
"""
import os
import pickle
from typing import List, Optional, Tuple
import numpy as np
from loguru import logger

try:
    import faiss
    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False
    logger.warning("FAISS未安装，向量数据库功能将不可用。请安装: pip install faiss-cpu")

from core.config import settings


class VectorDBService:
    """
    向量数据库服务
    
    使用FAISS存储和检索向量
    """
    
    def __init__(self, dimension: int = 1024, index_type: str = "L2"):
        """
        初始化向量数据库服务
        
        Args:
            dimension: 向量维度（默认1024，适用于text-embedding-3-small的1024维版本）
            index_type: 索引类型，'L2' 或 'InnerProduct'
        """
        if not FAISS_AVAILABLE:
            raise RuntimeError("FAISS未安装，无法使用向量数据库功能")
        
        self.dimension = dimension
        self.index_type = index_type
        self.index: Optional[faiss.Index] = None
        self.id_to_text: dict = {}  # 向量ID到文本的映射
        self.id_to_faiss_id: dict = {}  # vector_id到FAISS内部ID的映射
        self.next_faiss_id: int = 0  # 下一个FAISS内部ID
        self.storage_path = os.path.join(os.path.dirname(__file__), "..", "storage", "faiss_index")
        
        # 确保存储目录存在
        os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
        
        # 初始化索引
        self._init_index()
    
    def _init_index(self):
        """初始化FAISS索引"""
        index_path = f"{self.storage_path}.index"
        metadata_path = f"{self.storage_path}.meta"
        
        if os.path.exists(index_path) and os.path.exists(metadata_path):
            # 加载现有索引
            try:
                self.index = faiss.read_index(index_path)
                with open(metadata_path, "rb") as f:
                    data = pickle.load(f)
                    self.id_to_text = data.get("id_to_text", {})
                    self.id_to_faiss_id = data.get("id_to_faiss_id", {})
                    self.next_faiss_id = data.get("next_faiss_id", 0)
                logger.info(f"已加载现有向量索引，包含 {self.index.ntotal} 个向量")
            except Exception as e:
                logger.error(f"加载向量索引失败: {e}，创建新索引")
                self._create_new_index()
        else:
            # 创建新索引
            self._create_new_index()
    
    def _create_new_index(self):
        """创建新的FAISS索引"""
        # 使用IndexIDMap包装，支持ID映射
        if self.index_type == "L2":
            # 使用L2距离（欧氏距离）
            base_index = faiss.IndexFlatL2(self.dimension)
        else:
            # 使用内积（余弦相似度，需要先归一化向量）
            base_index = faiss.IndexFlatIP(self.dimension)
        
        # 包装为支持ID映射的索引
        self.index = faiss.IndexIDMap(base_index)
        
        logger.info(f"创建新的向量索引，维度: {self.dimension}, 类型: {self.index_type}")
    
    def add_embedding(
        self,
        vector_id: str,
        embedding: np.ndarray,
        metadata: Optional[dict] = None
    ) -> bool:
        """
        添加向量到数据库
        
        Args:
            vector_id: 向量ID（唯一标识）
            embedding: 向量数组（numpy array）
            metadata: 元数据（包含文本内容等信息）
        
        Returns:
            bool: 是否成功
        """
        if self.index is None:
            logger.error("向量索引未初始化")
            return False
        
        try:
            # 转换为numpy数组并确保维度正确
            if isinstance(embedding, list):
                embedding = np.array(embedding, dtype=np.float32)
            else:
                embedding = embedding.astype(np.float32)
            
            if embedding.ndim != 1:
                logger.error(f"向量维度错误，期望1维，实际{embedding.ndim}维")
                return False
            
            if embedding.shape[0] != self.dimension:
                logger.error(f"向量维度不匹配，期望{self.dimension}，实际{embedding.shape[0]}")
                return False
            
            # 对于InnerProduct类型，需要归一化向量
            if self.index_type == "InnerProduct":
                norm = np.linalg.norm(embedding)
                if norm > 0:
                    embedding = embedding / norm
                else:
                    logger.warning(f"向量{vector_id}的模长为0，跳过归一化")
            
            # 重新整形为2D数组（FAISS要求）
            embedding = embedding.reshape(1, -1)
            
            # 检查是否已存在
            if vector_id in self.id_to_faiss_id:
                logger.warning(f"向量ID已存在: {vector_id}，将更新")
                # 删除旧的向量（FAISS不支持直接更新，需要删除后重新添加）
                faiss_id = self.id_to_faiss_id[vector_id]
                self.index.remove_ids(np.array([faiss_id], dtype=np.int64))
                del self.id_to_faiss_id[vector_id]
            
            # 生成FAISS内部ID
            faiss_id = self.next_faiss_id
            self.next_faiss_id += 1
            
            # 添加到索引（带ID映射）
            self.index.add_with_ids(embedding, np.array([faiss_id], dtype=np.int64))
            
            # 保存映射关系
            self.id_to_faiss_id[vector_id] = faiss_id
            self.id_to_text[vector_id] = metadata or {}
            
            # 保存到磁盘
            self._save_index()
            
            logger.debug(f"成功添加向量: {vector_id}")
            return True
            
        except Exception as e:
            logger.error(f"添加向量失败: {e}")
            return False
    
    def search_similar(
        self,
        query_embedding: np.ndarray,
        top_k: int = 5,
        threshold: float = 0.7
    ) -> List[Tuple[str, float, dict]]:
        """
        搜索相似向量
        
        Args:
            query_embedding: 查询向量
            top_k: 返回最相似的k个结果
            threshold: 相似度阈值（仅返回相似度 >= threshold的结果）
        
        Returns:
            List[Tuple[str, float, dict]]: [(vector_id, similarity, metadata), ...]
        """
        if self.index is None or self.index.ntotal == 0:
            logger.warning("向量索引为空或未初始化")
            return []
        
        try:
            # 转换为numpy数组
            if isinstance(query_embedding, list):
                query_embedding = np.array(query_embedding, dtype=np.float32)
            else:
                query_embedding = query_embedding.astype(np.float32)
            
            # 确保维度正确
            if query_embedding.ndim != 1:
                query_embedding = query_embedding.flatten()
            
            if query_embedding.shape[0] != self.dimension:
                logger.error(f"查询向量维度不匹配，期望{self.dimension}，实际{query_embedding.shape[0]}")
                return []
            
            # 对于InnerProduct类型，需要归一化
            if self.index_type == "InnerProduct":
                norm = np.linalg.norm(query_embedding)
                if norm > 0:
                    query_embedding = query_embedding / norm
            
            # 重新整形为2D数组
            query_embedding = query_embedding.reshape(1, -1)
            
            # 搜索
            distances, indices = self.index.search(query_embedding, min(top_k, self.index.ntotal))
            
            # 处理结果
            results = []
            for i, (distance, idx) in enumerate(zip(distances[0], indices[0])):
                if idx == -1:  # FAISS返回-1表示无效结果
                    continue
                
                # 计算相似度
                if self.index_type == "L2":
                    # L2距离转换为相似度（使用简单的转换：similarity = 1 / (1 + distance)）
                    similarity = 1.0 / (1.0 + distance)
                else:
                    # InnerProduct已经是相似度（余弦相似度）
                    similarity = float(distance)
                
                # 只返回超过阈值的结果
                if similarity >= threshold:
                    # 通过FAISS内部ID查找vector_id
                    vector_id = None
                    for vid, fid in self.id_to_faiss_id.items():
                        if fid == idx:
                            vector_id = vid
                            break
                    
                    if vector_id:
                        metadata = self.id_to_text.get(vector_id, {})
                        results.append((vector_id, similarity, metadata))
            
            # 按相似度降序排序
            results.sort(key=lambda x: x[1], reverse=True)
            
            return results[:top_k]
            
        except Exception as e:
            logger.error(f"搜索相似向量失败: {e}")
            return []
    
    def delete_embedding(self, vector_id: str) -> bool:
        """
        删除向量
        
        Args:
            vector_id: 向量ID
        
        Returns:
            bool: 是否成功
        """
        try:
            if vector_id not in self.id_to_faiss_id:
                logger.warning(f"向量ID不存在: {vector_id}")
                return False
            
            # 获取FAISS内部ID
            faiss_id = self.id_to_faiss_id[vector_id]
            
            # 从索引中删除
            self.index.remove_ids(np.array([faiss_id], dtype=np.int64))
            
            # 清理映射关系
            del self.id_to_faiss_id[vector_id]
            if vector_id in self.id_to_text:
                del self.id_to_text[vector_id]
            
            # 保存到磁盘
            self._save_index()
            
            logger.debug(f"已删除向量: {vector_id}")
            return True
            
        except Exception as e:
            logger.error(f"删除向量失败: {e}")
            return False
    
    def _save_index(self):
        """保存索引到磁盘"""
        try:
            index_path = f"{self.storage_path}.index"
            metadata_path = f"{self.storage_path}.meta"
            
            if self.index is not None:
                faiss.write_index(self.index, index_path)
            
            with open(metadata_path, "wb") as f:
                pickle.dump({
                    "id_to_text": self.id_to_text,
                    "id_to_faiss_id": self.id_to_faiss_id,
                    "next_faiss_id": self.next_faiss_id,
                }, f)
            
            logger.debug("向量索引已保存到磁盘")
        except Exception as e:
            logger.error(f"保存向量索引失败: {e}")
    
    def get_stats(self) -> dict:
        """获取向量数据库统计信息"""
        return {
            "total_vectors": self.index.ntotal if self.index else 0,
            "dimension": self.dimension,
            "index_type": self.index_type,
            "metadata_count": len(self.id_to_text),
        }


# 全局向量数据库服务实例（延迟初始化）
_vector_db_service: Optional[VectorDBService] = None


def get_vector_db_service(dimension: int = 1024) -> VectorDBService:
    """
    获取向量数据库服务实例（单例模式）
    
    Args:
        dimension: 向量维度
    
    Returns:
        VectorDBService实例
    """
    global _vector_db_service
    
    if _vector_db_service is None:
        _vector_db_service = VectorDBService(dimension=dimension)
    
    return _vector_db_service

