import os
import sys
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException, Request

# Ensure parent path is in sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from routes.deps import is_safe_webhook_url, rate_limit_cloud_llm_and_batch


def test_is_safe_webhook_url():
    # Safe URLs
    assert is_safe_webhook_url("https://example.com/webhook") is True
    assert is_safe_webhook_url("http://google.com/api") is True
    assert is_safe_webhook_url("https://httpbin.org/post") is True

    # SSRF payloads / unsafe URLs
    assert is_safe_webhook_url("http://127.0.0.1/webhook") is False
    assert is_safe_webhook_url("http://localhost/webhook") is False
    assert is_safe_webhook_url("http://10.0.0.1:6379") is False
    assert is_safe_webhook_url("http://192.168.1.100/status") is False
    assert is_safe_webhook_url("http://169.254.169.254/metadata") is False
    assert is_safe_webhook_url("ftp://example.com/file") is False  # Invalid scheme
    assert is_safe_webhook_url("gopher://localhost") is False


@pytest.mark.anyio
async def test_rate_limit_cloud_llm_and_batch_new_key():
    # Test rate limiter when the key is new (first request)
    import hashlib

    mock_redis = MagicMock()
    mock_pipeline = MagicMock()
    mock_pipeline.execute = AsyncMock(return_value=[1, -1])
    mock_redis.pipeline.return_value = mock_pipeline
    mock_redis.expire = AsyncMock()

    mock_request = MagicMock(spec=Request)
    mock_request.client = MagicMock()
    mock_request.client.host = "1.2.3.4"
    mock_request.url.path = "/api/predict/hybrid"

    key_source = "1.2.3.4:/api/predict/hybrid"
    key_hash = hashlib.sha256(key_source.encode("utf-8")).hexdigest()[:32]
    expected_key = f"rate_limit:{key_hash}"

    with patch("classifier.get_redis", return_value=mock_redis):
        await rate_limit_cloud_llm_and_batch(mock_request)

        # Verify pipe.incr and pipe.ttl were called
        mock_pipeline.incr.assert_called_once_with(expected_key)
        mock_pipeline.ttl.assert_called_once_with(expected_key)

        # Verify expire was called because val == 1 and ttl == -1
        mock_redis.expire.assert_called_once_with(expected_key, 60)


@pytest.mark.anyio
async def test_rate_limit_cloud_llm_and_batch_existing_key():
    # Test rate limiter when key already exists and has TTL (second request)
    mock_redis = MagicMock()
    mock_pipeline = MagicMock()
    mock_pipeline.execute = AsyncMock(return_value=[2, 59])
    mock_redis.pipeline.return_value = mock_pipeline
    mock_redis.expire = AsyncMock()

    mock_request = MagicMock(spec=Request)
    mock_request.client = MagicMock()
    mock_request.client.host = "1.2.3.4"
    mock_request.url.path = "/api/predict/hybrid"

    with patch("classifier.get_redis", return_value=mock_redis):
        await rate_limit_cloud_llm_and_batch(mock_request)

        # Verify expire was NOT called because val > 1 and ttl > 0
        mock_redis.expire.assert_not_called()


@pytest.mark.anyio
async def test_rate_limit_cloud_llm_and_batch_limit_exceeded():
    # Test rate limiter when request count exceeds 15
    mock_redis = MagicMock()
    mock_pipeline = MagicMock()
    mock_pipeline.execute = AsyncMock(return_value=[16, 45])
    mock_redis.pipeline.return_value = mock_pipeline
    mock_redis.expire = AsyncMock()

    mock_request = MagicMock(spec=Request)
    mock_request.client = MagicMock()
    mock_request.client.host = "1.2.3.4"
    mock_request.url.path = "/api/predict/hybrid"

    with patch("classifier.get_redis", return_value=mock_redis):
        with pytest.raises(HTTPException) as exc_info:
            await rate_limit_cloud_llm_and_batch(mock_request)

        assert exc_info.value.status_code == 429
        assert "Too many requests" in exc_info.value.detail

        # Verify expire was NOT called
        mock_redis.expire.assert_not_called()


def test_production_startup_without_api_key():
    # Test that db_config raises ValueError in production if API_KEY is missing
    import importlib

    with patch.dict(os.environ, {"ENV": "production", "API_KEY": ""}):
        # Reloading db_config should trigger the ValueError
        with pytest.raises(ValueError) as exc_info:
            import classifier.db_config

            importlib.reload(classifier.db_config)

        assert "CRITICAL: Variabel lingkungan API_KEY tidak diatur" in str(exc_info.value)
