"""
技能Embedding服务
负责为技能生成向量并存储到向量数据库
"""
from typing import List, Optional, Tuple, Dict
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger
import numpy as np

from models.skill_library import SkillLibrary
from services.shared.embedding import get_embedding_service
from services.shared.vector_db import get_vector_db_service


class SkillEmbeddingService:
    """
    技能向量化服务

    功能：
    1. 为技能生成embedding
    2. 存储到向量数据库
    3. 搜索相似技能
    """

    def __init__(self):
        """初始化服务"""
        self.embedding_service = get_embedding_service()
        # 使用1024维向量（text-embedding-3-small）
        self.vector_db = get_vector_db_service(dimension=1024)
        logger.info("技能Embedding服务初始化完成")

    async def generate_skill_embedding(
        self,
        skill: SkillLibrary
    ) -> Optional[np.ndarray]:
        """
        为单个技能生成embedding

        Args:
            skill: 技能对象

        Returns:
            向量数组，失败返回None
        """
        # 构建向量化文本：名称 + 分类 + 特征描述 + 内容
        text = f"""技能名称：{skill.name}
分类：{skill.category}
特征描述：{skill.meta_description or '无'}
内容：{skill.content}"""

        try:
            embedding = await self.embedding_service.generate_embedding(text)
            if embedding is not None:
                logger.debug(f"技能 {skill.name} (ID={skill.id}) embedding生成成功")
            return embedding
        except Exception as e:
            logger.error(f"生成技能 {skill.name} (ID={skill.id}) embedding失败: {e}")
            return None

    async def add_skill_to_vector_db(
        self,
        skill: SkillLibrary,
        embedding: np.ndarray
    ) -> bool:
        """
        将技能embedding添加到向量数据库

        Args:
            skill: 技能对象
            embedding: 向量数组

        Returns:
            是否成功
        """
        try:
            # 构建向量ID（使用skill前缀避免冲突）
            vector_id = f"skill_{skill.id}"

            # 构建元数据
            metadata = {
                "type": "skill",
                "skill_id": skill.id,
                "name": skill.name,
                "category": skill.category,
                "meta_description": skill.meta_description or "",
                "content": skill.content,
                "status": skill.status,
            }

            # 添加到向量库
            success = self.vector_db.add_embedding(
                vector_id=vector_id,
                embedding=embedding,
                metadata=metadata
            )

            if success:
                logger.info(f"技能 {skill.name} (ID={skill.id}) 已添加到向量库")
            else:
                logger.error(f"技能 {skill.name} (ID={skill.id}) 添加到向量库失败")

            return success

        except Exception as e:
            logger.error(f"添加技能到向量库失败: {e}")
            return False

    async def update_skill_embedding(
        self,
        db: AsyncSession,
        skill_id: int
    ) -> bool:
        """
        更新单个技能的embedding

        Args:
            db: 数据库会话
            skill_id: 技能ID

        Returns:
            是否成功
        """
        try:
            # 查询技能
            result = await db.execute(select(SkillLibrary).filter(SkillLibrary.id == skill_id))
            skill = result.scalar_one_or_none()

            if not skill:
                logger.warning(f"技能 ID={skill_id} 不存在")
                return False

            # 生成embedding
            embedding = await self.generate_skill_embedding(skill)
            if embedding is None:
                logger.error(f"生成技能 {skill.name} embedding失败")
                return False

            # 添加到向量库（会自动覆盖旧的）
            success = await self.add_skill_to_vector_db(skill, embedding)

            if success:
                logger.info(f"技能 {skill.name} (ID={skill_id}) embedding更新成功")

            return success

        except Exception as e:
            logger.error(f"更新技能embedding失败: {e}")
            return False

    async def batch_generate_embeddings(
        self,
        db: AsyncSession,
        batch_size: int = 10
    ) -> Dict[str, int]:
        """
        批量为所有技能生成embedding

        Args:
            db: 数据库会话
            batch_size: 批次大小

        Returns:
            统计信息 {success: 成功数, failed: 失败数, total: 总数}
        """
        try:
            # 查询所有启用的技能
            result = await db.execute(
                select(SkillLibrary).filter(SkillLibrary.status == 1)
            )
            skills = result.scalars().all()

            total = len(skills)
            success_count = 0
            failed_count = 0

            logger.info(f"开始批量生成技能embedding，共 {total} 个技能")

            for i, skill in enumerate(skills):
                try:
                    # 生成embedding
                    embedding = await self.generate_skill_embedding(skill)
                    if embedding is None:
                        failed_count += 1
                        logger.warning(f"技能 {skill.name} (ID={skill.id}) embedding生成失败")
                        continue

                    # 添加到向量库
                    success = await self.add_skill_to_vector_db(skill, embedding)
                    if success:
                        success_count += 1
                    else:
                        failed_count += 1

                    # 每处理batch_size个记录一次日志
                    if (i + 1) % batch_size == 0:
                        logger.info(f"已处理 {i + 1}/{total} 个技能")

                except Exception as e:
                    failed_count += 1
                    logger.error(f"处理技能 {skill.name} (ID={skill.id}) 失败: {e}")

            stats = {
                "total": total,
                "success": success_count,
                "failed": failed_count
            }

            logger.info(f"批量生成完成: {stats}")
            return stats

        except Exception as e:
            logger.error(f"批量生成embedding失败: {e}")
            return {"total": 0, "success": 0, "failed": 0}

    async def search_similar_skills(
        self,
        query_text: str,
        top_k: int = 5,
        threshold: float = 0.7
    ) -> List[Tuple[int, float, Dict]]:
        """
        搜索相似技能

        Args:
            query_text: 查询文本
            top_k: 返回最相似的k个结果
            threshold: 相似度阈值

        Returns:
            [(skill_id, similarity, metadata), ...]
        """
        try:
            # 生成查询文本的embedding
            query_embedding = await self.embedding_service.generate_embedding(query_text)
            if query_embedding is None:
                logger.error("生成查询文本embedding失败")
                return []

            # 搜索相似向量
            results = self.vector_db.search_similar(
                query_embedding=query_embedding,
                top_k=top_k,
                threshold=threshold
            )

            # 过滤出技能类型的向量
            skill_results = []
            for vector_id, similarity, metadata in results:
                if metadata.get("type") == "skill":
                    skill_id = metadata.get("skill_id")
                    if skill_id is not None:
                        skill_results.append((skill_id, similarity, metadata))

            if threshold == 0.0:
                logger.debug(f"搜索到 {len(skill_results)} 个相似技能（未应用阈值）")
            else:
                logger.info(f"搜索到 {len(skill_results)} 个相似技能（阈值={threshold}）")
            return skill_results

        except Exception as e:
            logger.error(f"搜索相似技能失败: {e}")
            return []

    async def delete_skill_embedding(
        self,
        skill_id: int
    ) -> bool:
        """
        删除技能的embedding

        Args:
            skill_id: 技能ID

        Returns:
            是否成功
        """
        try:
            vector_id = f"skill_{skill_id}"
            success = self.vector_db.delete_embedding(vector_id)

            if success:
                logger.info(f"技能 ID={skill_id} embedding已删除")
            else:
                logger.warning(f"技能 ID={skill_id} embedding不存在或删除失败")

            return success

        except Exception as e:
            logger.error(f"删除技能embedding失败: {e}")
            return False


# 全局服务实例
_skill_embedding_service: Optional[SkillEmbeddingService] = None


def get_skill_embedding_service() -> SkillEmbeddingService:
    """
    获取技能Embedding服务实例（单例模式）

    Returns:
        SkillEmbeddingService实例
    """
    global _skill_embedding_service

    if _skill_embedding_service is None:
        _skill_embedding_service = SkillEmbeddingService()

    return _skill_embedding_service
