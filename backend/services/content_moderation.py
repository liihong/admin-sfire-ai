"""
内容审查服务
实现敏感词检测功能
"""
from typing import Optional, Set
from loguru import logger


class ContentModerationService:
    """内容审查���务 (敏感词检测)"""

    # 默认敏感词库 (可从数据库或配置文件加载)
    DEFAULT_SENSITIVE_WORDS = {
        # 政治敏感词 (示例)
        "暴力恐怖", "分裂国家", "颠覆政权",

        # 色情词汇 (示例)
        "色情", "淫秽", "性服务",

        # 违法犯罪 (示例)
        "毒品", "赌博", "洗钱", "诈骗", "黑客攻击",

        # 其他违规内容
        "自杀", "自残",
    }

    def __init__(self, sensitive_words: Optional[Set[str]] = None):
        """
        初始化内容审查服务

        Args:
            sensitive_words: 自定义敏感词库,如果不提供则使用默认词库
        """
        self.sensitive_words = sensitive_words or self.DEFAULT_SENSITIVE_WORDS
        logger.info(f"内容审查服务初始化完成,加载敏感词 {len(self.sensitive_words)} 个")

    def _load_sensitive_words(self) -> Set[str]:
        """
        从数据库或配置文件加载敏感词库

        TODO: 后续可以从数据库动态加载
        """
        return self.DEFAULT_SENSITIVE_WORDS

    async def check_input(self, text: str) -> dict:
        """
        前置审查 - 用户输入

        Args:
            text: 用户输入的文本

        Returns:
            {
                "passed": bool,              # 是否通过审查
                "violation_type": Optional[str],  # 违规类型
                "matched_word": Optional[str]     # 匹配到的敏感词
            }
        """
        if not text:
            return {"passed": True, "violation_type": None, "matched_word": None}

        # 检查敏感词
        for word in self.sensitive_words:
            if word in text:
                logger.warning(f"用户输入包含敏感词: {word}")
                return {
                    "passed": False,
                    "violation_type": "sensitive_word",
                    "matched_word": word
                }

        return {"passed": True, "violation_type": None, "matched_word": None}

    async def check_output(self, text: str) -> dict:
        """
        后置审查 - AI输出

        Args:
            text: AI生成的文本

        Returns:
            {
                "passed": bool,              # 是否通过审查
                "violation_type": Optional[str],  # 违规类型
                "matched_word": Optional[str]     # 匹配到的敏感词
            }
        """
        if not text:
            return {"passed": True, "violation_type": None, "matched_word": None}

        # 检查敏感词
        for word in self.sensitive_words:
            if word in text:
                logger.warning(f"AI输出包含敏感词: {word}")
                return {
                    "passed": False,
                    "violation_type": "sensitive_word",
                    "matched_word": word
                }

        return {"passed": True, "violation_type": None, "matched_word": None}

    async def check_stream(self, chunk: str) -> bool:
        """
        流式检测 (实时检测)

        Args:
            chunk: 流式输出的一块文本

        Returns:
            True-通过, False-包含违规内容
        """
        if not chunk:
            return True

        for word in self.sensitive_words:
            if word in chunk:
                logger.warning(f"流式输出检测到敏感词: {word}")
                return False

        return True

    def add_sensitive_words(self, words: Set[str]) -> None:
        """
        添加敏感词

        Args:
            words: 要添加的敏感词集合
        """
        self.sensitive_words.update(words)
        logger.info(f"添加敏感词 {len(words)} 个,当前总数 {len(self.sensitive_words)}")

    def remove_sensitive_words(self, words: Set[str]) -> None:
        """
        移除敏感词

        Args:
            words: 要移除的敏感词集合
        """
        self.sensitive_words -= words
        logger.info(f"移除敏感词 {len(words)} 个,当前总数 {len(self.sensitive_words)}")


# 全局单例实例
_moderation_service: Optional[ContentModerationService] = None


def get_moderation_service() -> ContentModerationService:
    """
    获取内容审查服务单例

    Returns:
        ContentModerationService实例
    """
    global _moderation_service
    if _moderation_service is None:
        _moderation_service = ContentModerationService()
    return _moderation_service
