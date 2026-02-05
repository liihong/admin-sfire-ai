"""
Application Configuration using pydantic-settings
"""
from typing import List, Optional
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
import json
import os
from urllib.parse import quote_plus
from loguru import logger


class Settings(BaseSettings):
    """应用配置类"""
    
    # 获取 .env 文件的绝对路径（相对于当前文件所在目录）
    _env_file_path = os.path.join(os.path.dirname(__file__), "..", ".env")
    _env_file_abs = os.path.abspath(_env_file_path)
    
    model_config = SettingsConfigDict(
        env_file=_env_file_abs,  # 使用绝对路径
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
        # 如果 .env 文件不存在或解析失败，不抛出异常，使用默认值
        env_ignore_empty=True,
    )

    # 应用配置
    APP_NAME: str = "SFire-Admin-API"
    APP_ENV: str = "development"
    DEBUG: bool = True
    SECRET_KEY: str = "your-super-secret-key-change-in-production"

    # 服务器配置
    HOST: str = "127.0.0.1"
    PORT: int = 8000

    # MySQL 数据库配置
    MYSQL_HOST: str = ""
    MYSQL_PORT: int = 3306
    MYSQL_USER: str = "root"
    MYSQL_PASSWORD: str = ""
    MYSQL_DATABASE: str = ""

    # Redis 配置
    REDIS_HOST: str = ""
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: str = ""
    REDIS_DB: int = 0

    # JWT 配置
    JWT_SECRET_KEY: str = "your-jwt-secret-key"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # 跨域配置
    CORS_ORIGINS: List[str] = ["http://0.0.0.0:8000", "http://0.0.0.0:9000"]

    # 第三方 API 配置（Dashboard 监控用）
    TIKHUB_API_KEY: str = ""  # Tikhub API Key
    OPENAI_API_KEY: str = ""  # OpenAI API Key
    
    # 微信小程序配置
    WECHAT_APP_ID: str = ""  # 微信小程序 AppID
    WECHAT_APP_SECRET: str = ""  # 微信小程序 AppSecret
    
    # 微信支付配置
    WECHAT_PAY_MCH_ID: str = ""  # 微信支付商户号
    WECHAT_PAY_API_KEY: str = ""  # 微信支付API密钥（v2 API密钥），仅支持32个字符，数字和大小写字母的组合
    WECHAT_PAY_NOTIFY_URL: str = ""  # 微信支付回调地址
    WECHAT_PAY_IP_WHITELIST: str = ""  # 微信支付IP白名单（逗号分隔）
    
    # LLM 配置
    DEEPSEEK_API_KEY: str = ""  # DeepSeek API Key
    DOUBAO_API_KEY: str = ""  # 火山引擎（Doubao）API Key
    ANTHROPIC_API_KEY: str = ""  # Anthropic (Claude) API Key
    
    # AI智能填写接口配置
    AI_COLLECT_MODEL_ID: str = ""  # AI采集接口使用的模型ID（数据库ID或模型标识，如 "doubao"）
    AI_COLLECT_API_KEY: str = ""  # AI采集接口使用的API Key（可选，优先使用模型配置）
    AI_COLLECT_BASE_URL: str = ""  # AI采集接口使用的Base URL（可选，优先使用模型配置）

    ROUTER_AGENT_ID: int = 12  # 路由Agent ID（存储Prompt模板）
    IP_COLLECTOR_AGENT_ID: Optional[int] = 13  # IP信息采集Agent ID（从数据库读取配置，如果为None则通过名称查找）
    IP_REPORT_AGENT_ID: int = 14  # IP定位报告生成Agent ID
    MASTER_PROMPT_AGENT_ID: int = 13  # Master Prompt生成Agent ID
    HOTSPOT_AGENT_ID: Optional[int] = None  # 蹭热点功能使用的智能体ID（从数据库读取配置，如果为None则通过名称查找）
    
    # Embedding 配置
    EMBEDDING_PROVIDER: str = "openai"  # Embedding服务提供商: openai, deepseek (注意：DeepSeek不提供embedding API)
    EMBEDDING_BASE_URL: str = ""  # Embedding API基础URL（可选，默认根据provider自动设置）
    EMBEDDING_MODEL: str = ""  # Embedding模型名称（可选，默认根据provider自动设置）
    EMBEDDING_API_KEY: str = ""  # Embedding API Key（可选，默认使用对应provider的API Key）

    # OSS 对象存储配置
    OSS_PROVIDER: str = ""  # OSS服务提供商: local(本地存储), aliyun(阿里云OSS), tencent(腾讯云COS), qiniu(七牛云)
    OSS_ACCESS_KEY_ID: str = ""  # OSS Access Key ID（阿里云/腾讯云/七牛云通用）
    OSS_ACCESS_KEY_SECRET: str = ""  # OSS Access Key Secret（阿里云/腾讯云/七牛云通用）
    OSS_BUCKET_NAME: str = ""  # OSS存储桶名称
    OSS_ENDPOINT: str = ""  # OSS服务端点（阿里云OSS使用，如: oss-cn-hangzhou.aliyuncs.com）
    OSS_REGION: str = ""  # OSS区域（腾讯云COS使用，如: ap-guangzhou）
    OSS_DOMAIN: str = ""  # OSS自定义域名（可选，用于文件访问URL，如: https://cdn.example.com）


    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        """解析 CORS_ORIGINS，支持 JSON 字符串格式"""
        if isinstance(v, str):
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                return [origin.strip() for origin in v.split(",")]
        return v

    @property
    def MYSQL_DATABASE_URL(self) -> str:
        """MySQL 异步连接 URL"""
        # URL 编码用户名和密码，避免特殊字符（如 @）导致解析错误
        encoded_user = quote_plus(self.MYSQL_USER)
        encoded_password = quote_plus(self.MYSQL_PASSWORD)
        return (
            f"mysql+aiomysql://{encoded_user}:{encoded_password}"
            f"@{self.MYSQL_HOST}:{self.MYSQL_PORT}/{self.MYSQL_DATABASE}"
            "?charset=utf8mb4"
        )

    @property
    def MYSQL_DATABASE_URL_SYNC(self) -> str:
        """MySQL 同步连接 URL（用于 Alembic 迁移）"""
        # URL 编码用户名和密码，避免特殊字符（如 @）导致解析错误
        encoded_user = quote_plus(self.MYSQL_USER)
        encoded_password = quote_plus(self.MYSQL_PASSWORD)
        return (
            f"mysql+pymysql://{encoded_user}:{encoded_password}"
            f"@{self.MYSQL_HOST}:{self.MYSQL_PORT}/{self.MYSQL_DATABASE}"
            "?charset=utf8mb4"
        )

    @property
    def REDIS_URL(self) -> str:
        """Redis 连接 URL"""
        if self.REDIS_PASSWORD:
            return f"redis://:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"


# 创建全局配置实例，优雅处理 .env 文件解析错误
def create_settings():
    """创建配置实例，如果 .env 文件解析失败则使用默认值"""
    # 获取 .env 文件路径
    env_file_path = os.path.join(os.path.dirname(__file__), "..", ".env")
    env_file_abs = os.path.abspath(env_file_path)
    
    logger.info(f"📋 尝试加载配置文件: {env_file_abs}")
    logger.info(f"📁 文件是否存在: {os.path.exists(env_file_abs)}")
    
    if os.path.exists(env_file_abs):
        # 检查文件权限
        file_stat = os.stat(env_file_abs)
        logger.info(f"📊 文件权限: {oct(file_stat.st_mode)}")
        logger.info(f"👤 文件所有者: UID={file_stat.st_uid}, GID={file_stat.st_gid}")
    
    try:
        settings = Settings()
        
        # 验证关键配置是否加载成功
        logger.info("🔍 验证配置加载状态...")
        
        # 检查微信支付配置
        wechat_pay_configured = bool(settings.WECHAT_PAY_MCH_ID and settings.WECHAT_PAY_API_KEY)
        if wechat_pay_configured:
            logger.info("✅ 微信支付配置加载成功")
            logger.debug(f"   - 商户号: {settings.WECHAT_PAY_MCH_ID[:4]}*** (已隐藏)")
            logger.debug(f"   - API密钥: {'*' * min(len(settings.WECHAT_PAY_API_KEY), 8)} (已隐藏)")
        else:
            logger.warning("⚠️ 微信支付配置为空或未完整加载")
            logger.warning(f"   - WECHAT_PAY_MCH_ID: {'已设置' if settings.WECHAT_PAY_MCH_ID else '未设置'}")
            logger.warning(f"   - WECHAT_PAY_API_KEY: {'已设置' if settings.WECHAT_PAY_API_KEY else '未设置'}")
        
        # 检查数据库配置
        db_configured = bool(settings.MYSQL_HOST and settings.MYSQL_DATABASE)
        if db_configured:
            logger.info("✅ 数据库配置加载成功")
        else:
            logger.warning("⚠️ 数据库配置未完整加载")
        
        # 检查 Redis 配置
        redis_configured = bool(settings.REDIS_HOST)
        if redis_configured:
            logger.info("✅ Redis配置加载成功")
        else:
            logger.warning("⚠️ Redis配置未完整加载")
        
        return settings
        
    except Exception as e:
        error_msg = str(e)
        logger.error(f"❌ 加载 .env 文件时出现错误: {error_msg}")
        logger.error(f"📁 配置文件路径: {env_file_abs}")
        logger.warning("将使用默认配置值，请检查 .env 文件格式是否正确")
        logger.info("提示: .env 文件格式要求:")
        logger.info("  - 每行格式: KEY=VALUE")
        logger.info("  - 注释以 # 开头，且 # 必须在行首")
        logger.info("  - 值中包含空格时需要用引号包裹: KEY=\"value with spaces\"")
        logger.info("  - 行首不能有空格或制表符")
        logger.info("  - 每行必须以 KEY= 开头，不能有空行（除非是注释）")
        
        # 创建不加载 .env 文件的配置类，继承原 Settings 的所有字段和方法
        class SettingsWithoutFile(Settings):
            """配置类（不加载 .env 文件，只使用环境变量和默认值）"""
            model_config = SettingsConfigDict(
                env_file=None,  # 不加载文件
                env_file_encoding="utf-8",
                case_sensitive=True,
                extra="ignore",
                env_ignore_empty=True,
            )
        
        return SettingsWithoutFile()

settings = create_settings()


