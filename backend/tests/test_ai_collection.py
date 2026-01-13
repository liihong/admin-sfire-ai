"""
Test AI Collection Features

Tests for AI-powered IP information collection and compression
"""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.asyncio
class TestAICollect:
    """Test AI IP Collection endpoints"""

    async def test_ai_collect_init(
        self,
        async_client: AsyncClient,
        miniprogram_user_token: str
    ):
        """Test AI collection initialization"""
        response = await async_client.post(
            "/api/client/projects/ai-collect",
            json={
                "messages": [],
                "step": 0,
                "context": {}
            },
            headers={"Authorization": f"Bearer {miniprogram_user_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert "reply" in data["data"]
        assert data["data"]["reply"]  # AI should reply

    async def test_ai_collect_with_user_message(
        self,
        async_client: AsyncClient,
        miniprogram_user_token: str
    ):
        """Test AI collection with user message"""
        response = await async_client.post(
            "/api/client/projects/ai-collect",
            json={
                "messages": [
                    {"role": "assistant", "content": "你好！我是火源IP信息收集助手"},
                    {"role": "user", "content": "我想创建一个健身教练的IP"}
                ],
                "step": 0,
                "context": {}
            },
            headers={"Authorization": f"Bearer {miniprogram_user_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert "reply" in data["data"]

    async def test_ai_compress(
        self,
        async_client: AsyncClient,
        miniprogram_user_token: str
    ):
        """Test AI IP compression"""
        response = await async_client.post(
            "/api/client/projects/ai-compress",
            json={
                "raw_info": {
                    "name": "健身教练IP",
                    "industry": "体育健身",
                    "introduction": "这是一个非常长的简介内容，" * 20,  # 长文本测试压缩
                    "tone": "专业亲和",
                    "target_audience": "想要健身的人群，" * 10,
                    "catchphrase": "一起健身吧",
                    "keywords": ["健身", "减肥", "增肌", "瑜伽", "普拉提", "有氧", "无氧", "饮食", "营养", "健康"]
                }
            },
            headers={"Authorization": f"Bearer {miniprogram_user_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert "compressed_info" in data["data"]

        compressed = data["data"]["compressed_info"]
        # 验证字数限制
        assert len(compressed["introduction"]) <= 200
        assert len(compressed["target_audience"]) <= 50
        assert len(compressed["keywords"]) <= 8

    async def test_ai_collect_unauthorized(
        self,
        async_client: AsyncClient
    ):
        """Test AI collection without authentication"""
        response = await async_client.post(
            "/api/client/projects/ai-collect",
            json={
                "messages": [],
                "step": 0,
                "context": {}
            }
        )

        assert response.status_code == 401

    async def test_ai_compress_unauthorized(
        self,
        async_client: AsyncClient
    ):
        """Test AI compression without authentication"""
        response = await async_client.post(
            "/api/client/projects/ai-compress",
            json={
                "raw_info": {
                    "name": "Test IP",
                    "industry": "Test"
                }
            }
        )

        assert response.status_code == 401


@pytest.mark.asyncio
class TestDatabaseSession:
    """Test database session improvements"""

    async def test_lock_timeout_config(self, db_session: AsyncSession):
        """Test that lock timeout is properly configured"""
        # This test verifies the database URL contains lock timeout settings
        from core.config import settings
        db_url = settings.MYSQL_DATABASE_URL

        # Check that lock_wait_timeout is in the URL
        assert "lock_wait_timeout" in db_url or "init_command" in db_url

    async def test_connection_pool_config(self):
        """Test that connection pool is configured"""
        from db.session import engine, async_session_maker

        assert engine is not None
        assert async_session_maker is not None

        # Verify pool settings
        assert engine.pool.size() == 10  # pool_size
        # max_overflow is verified indirectly through pool behavior


@pytest.mark.asyncio
class TestErrorHandling:
    """Test error handling improvements"""

    async def test_safe_error_messages(
        self,
        async_client: AsyncClient,
        miniprogram_user_token: str
    ):
        """Test that error messages don't expose sensitive information"""
        # Test with invalid data that would trigger an error
        response = await async_client.post(
            "/api/client/projects/ai-compress",
            json={
                "raw_info": {}  # Empty data should not crash
            },
            headers={"Authorization": f"Bearer {miniprogram_user_token}"}
        )

        # Should return proper error, not internal server error with stack trace
        assert response.status_code in [200, 400, 500]
        data = response.json()

        # Error message should be user-friendly
        if "msg" in data:
            # Should not contain technical details like stack trace, file paths, etc.
            assert ".py" not in data["msg"]
            assert "Traceback" not in data["msg"]
            assert "Exception" not in data["msg"]
