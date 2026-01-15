"""
Application Configuration using pydantic-settings
"""
from typing import List
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
import json
from urllib.parse import quote_plus


class Settings(BaseSettings):
    """应用配置类"""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
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
    MYSQL_HOST: str = "localhost"
    MYSQL_PORT: int = 3306
    MYSQL_USER: str = "root"
    MYSQL_PASSWORD: str = "Sfire@2026"
    MYSQL_DATABASE: str = "sfire_admin"

    # Redis 配置
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: str = ""
    REDIS_DB: int = 0

    # JWT 配置
    JWT_SECRET_KEY: str = "your-jwt-secret-key"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # 跨域配置
    CORS_ORIGINS: List[str] = ["http://localhost:5173", "http://localhost:3000"]

    # 第三方 API 配置（Dashboard 监控用）
    TIKHUB_API_KEY: str = ""  # Tikhub API Key
    OPENAI_API_KEY: str = "e44c68945ae94109b4d7f433c2442310.3v8Np2obJ8MtYj33"  # OpenAI API Key
    
    # 微信小程序配置
    WECHAT_APP_ID: str = "wxd9e4d8682e6caff6"  # 微信小程序 AppID
    WECHAT_APP_SECRET: str = "8a74db18d133f00d4e6360edec9d40d9"  # 微信小程序 AppSecret
    
    # LLM 配置
    DEEPSEEK_API_KEY: str = ""  # DeepSeek API Key
    DOUBAO_API_KEY: str = ""  # 火山引擎（Doubao）API Key
    ANTHROPIC_API_KEY: str = ""  # Anthropic (Claude) API Key
    
    # AI智能填写接口配置
    AI_COLLECT_MODEL_ID: str = ""  # AI采集接口使用的模型ID（数据库ID或模型标识，如 "doubao"）
    AI_COLLECT_API_KEY: str = ""  # AI采集接口使用的API Key（可选，优先使用模型配置）
    AI_COLLECT_BASE_URL: str = ""  # AI采集接口使用的Base URL（可选，优先使用模型配置）
    
    # Embedding 配置
    EMBEDDING_PROVIDER: str = "openai"  # Embedding服务提供商: openai, deepseek (注意：DeepSeek不提供embedding API)
    EMBEDDING_BASE_URL: str = ""  # Embedding API基础URL（可选，默认根据provider自动设置）
    EMBEDDING_MODEL: str = ""  # Embedding模型名称（可选，默认根据provider自动设置）
    EMBEDDING_API_KEY: str = ""  # Embedding API Key（可选，默认使用对应provider的API Key）

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


# 创建全局配置实例
settings = Settings()


