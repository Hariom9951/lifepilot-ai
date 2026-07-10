from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import AsyncClient
from pydantic import ValidationError

from app.core.config.settings import ProductionSettings


@pytest.mark.asyncio
async def test_health_check_endpoint(client: AsyncClient):
    """
    Verifies that the GET /health check endpoint resolves and responds with expected schema.
    """
    mock_session = MagicMock()
    mock_session.execute = AsyncMock(return_value=None)
    mock_session_context = MagicMock()
    mock_session_context.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session_context.__aexit__ = AsyncMock(return_value=None)

    with (
        patch(
            "app.main.redis_manager.ping",
            AsyncMock(return_value=True),
        ),
        patch(
            "app.main.SessionLocal",
            return_value=mock_session_context,
        ),
    ):
        res = await client.get("/health")
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "healthy"
        assert data["database"] == "ok"
        assert data["redis"] == "ok"
        assert "version" in data


@pytest.mark.asyncio
async def test_readiness_check_endpoint(client: AsyncClient):
    """
    Verifies that the GET /ready endpoint checks database, redis, embedding, and vector providers.
    """
    mock_session = MagicMock()
    mock_session.execute = AsyncMock(return_value=None)
    mock_session_context = MagicMock()
    mock_session_context.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session_context.__aexit__ = AsyncMock(return_value=None)

    with (
        patch(
            "app.main.redis_manager.ping",
            AsyncMock(return_value=True),
        ),
        patch(
            "app.main.SessionLocal",
            return_value=mock_session_context,
        ),
        patch("app.main.get_active_provider") as mock_emb,
        patch("app.main.get_vector_store_provider") as mock_vec,
    ):
        # Mock active providers returning valid configs
        mock_provider = MagicMock()
        mock_provider.get_dimension.return_value = 384
        mock_emb.return_value = mock_provider
        mock_vec.return_value = MagicMock()

        res = await client.get("/ready")
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "ready"
        assert data["database"] == "ok"
        assert data["redis"] == "ok"
        assert data["embedding_provider"] == "ok"
        assert data["vector_database"] == "ok"


def test_settings_environment_validation():
    """
    Checks that ProductionSettings raises validation errors for weak configurations.
    """
    # 1. Test weak production secret key
    with pytest.raises(ValidationError):
        ProductionSettings(
            ENVIRONMENT="production",
            SECRET_KEY="replace_me_with_a_secure_random_hex_string_sprinting_phase",
            DATABASE_URL="postgresql+asyncpg://lifepilot_user:pass@remote-host:5432/db",
            REDIS_URL="redis://:pass@remote-redis:6379/0",
        )

    # 2. Test localhost database in production
    with pytest.raises(ValidationError):
        ProductionSettings(
            ENVIRONMENT="production",
            SECRET_KEY="secure_prod_secret_key_minimum_length_required",
            DATABASE_URL="postgresql+asyncpg://lifepilot_user:pass@localhost:5432/db",
            REDIS_URL="redis://:pass@remote-redis:6379/0",
        )

    # 3. Test localhost redis in production
    with pytest.raises(ValidationError):
        ProductionSettings(
            ENVIRONMENT="production",
            SECRET_KEY="secure_prod_secret_key_minimum_length_required",
            DATABASE_URL="postgresql+asyncpg://lifepilot_user:pass@remote-host:5432/db",
            REDIS_URL="redis://:pass@127.0.0.1:6379/0",
        )

    # 4. Test valid production configuration passes and masks secrets
    valid_prod = ProductionSettings(
        ENVIRONMENT="production",
        DEBUG=False,
        SECRET_KEY="secure_prod_secret_key_minimum_length_required",
        DATABASE_URL="postgresql+asyncpg://lifepilot_user:secure_pass@remote-postgres.com:5432/lifepilot_db",
        REDIS_URL="rediss://:secure_redis_pass@remote-redis.com:6379/0",
    )
    assert valid_prod.ENVIRONMENT == "production"
    assert valid_prod.DEBUG is False
    assert valid_prod.get_masked_settings()["SECRET_KEY"] == "********"
    assert valid_prod.get_masked_settings()["DATABASE_URL"] == "********"
