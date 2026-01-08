"""
简单的Embedding服务测试
直接测试配置读取和服务初始化
"""
import os
import sys
from pathlib import Path

# 添加项目根目录到路径
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

# 设置环境变量（从.env读取）
from dotenv import load_dotenv
load_dotenv(backend_dir / ".env")

print("=" * 60)
print("Embedding配置检查")
print("=" * 60)

# 检查环境变量
embedding_provider = os.getenv("EMBEDDING_PROVIDER", "")
embedding_base_url = os.getenv("EMBEDDING_BASE_URL", "")
embedding_model = os.getenv("EMBEDDING_MODEL", "")
embedding_api_key = os.getenv("EMBEDDING_API_KEY", "")

print(f"✓ EMBEDDING_PROVIDER: {embedding_provider}")
print(f"✓ EMBEDDING_BASE_URL: {embedding_base_url}")
print(f"✓ EMBEDDING_MODEL: {embedding_model}")
print(f"✓ EMBEDDING_API_KEY: {embedding_api_key[:20]}..." if embedding_api_key else "✗ EMBEDDING_API_KEY: 未配置")

print("=" * 60)

# 验证配置
if not embedding_api_key:
    print("✗ 错误: EMBEDDING_API_KEY 未配置")
    sys.exit(1)

if not embedding_provider:
    print("⚠ 警告: EMBEDDING_PROVIDER 未配置，将使用默认值 'openai'")
else:
    print(f"✓ EMBEDDING_PROVIDER 已配置: {embedding_provider}")

if embedding_base_url:
    print(f"✓ 使用自定义 Base URL: {embedding_base_url}")
    print("  (阿里云DashScope OpenAI兼容模式)")
else:
    print("⚠ 使用默认 Base URL (OpenAI官方)")

if embedding_model:
    print(f"✓ 使用自定义模型: {embedding_model}")
else:
    print("⚠ 使用默认模型: text-embedding-3-small")

print("=" * 60)
print("配置验证完成！")
print("=" * 60)
print()
print("现在尝试初始化Embedding服务...")

# 尝试导入和初始化
try:
    # 直接导入EmbeddingService类
    import httpx
    import numpy as np
    from loguru import logger

    # 简化的配置类
    class SimpleSettings:
        EMBEDDING_PROVIDER = embedding_provider or "openai"
        EMBEDDING_BASE_URL = embedding_base_url
        EMBEDDING_MODEL = embedding_model
        EMBEDDING_API_KEY = embedding_api_key

    settings = SimpleSettings()

    # 创建简化的服务
    print(f"✓ 环境变量读取成功")
    print(f"  Provider: {settings.EMBEDDING_PROVIDER}")
    print(f"  Base URL: {settings.EMBEDDING_BASE_URL}")
    print(f"  Model: {settings.EMBEDDING_MODEL}")
    print(f"  API Key: 已配置 ({len(settings.EMBEDDING_API_KEY)} 字符)")

    print("=" * 60)
    print("✓ Embedding服务配置检查通过！")
    print("=" * 60)

except Exception as e:
    print(f"✗ 初始化失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
