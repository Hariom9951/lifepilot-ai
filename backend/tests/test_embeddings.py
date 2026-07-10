from datetime import timedelta
from unittest.mock import MagicMock, patch

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config.settings import settings
from app.features.auth.models import Role, User
from app.features.auth.repositories import RoleRepository, UserRepository
from app.features.auth.security import create_access_token
from app.features.embeddings.benchmarks import run_benchmark
from app.features.embeddings.cache import EmbeddingCacheManager
from app.features.embeddings.providers import (
    MODEL_DIMENSIONS,
    get_active_provider,
    get_device,
)
from app.features.embeddings.services import (
    EmbeddingEngineService,
    cosine_similarity,
    dot_product,
)

# Fixtures


@pytest.fixture(autouse=True)
async def seed_user_role(db_session: AsyncSession):
    user_role = await RoleRepository.get_by_name(db_session, "USER")
    if not user_role:
        user_role = await RoleRepository.create(
            db_session, name="USER", description="Standard user"
        )
    await db_session.commit()
    return user_role


@pytest.fixture
async def test_user(db_session: AsyncSession, seed_user_role: Role) -> User:
    user = await UserRepository.get_by_username(db_session, "embeddings_tester")
    if not user:
        user = await UserRepository.create(
            db_session,
            {
                "full_name": "Embeddings Tester",
                "username": "embeddings_tester",
                "email": "tester_embeddings@example.com",
                "hashed_password": "fakehashedpwd",
                "role_id": seed_user_role.id,
            },
        )
        await db_session.commit()
    return user


@pytest.fixture
def auth_headers(test_user: User) -> dict[str, str]:
    token = create_access_token(
        subject=str(test_user.id), expires_delta=timedelta(hours=1)
    )
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(autouse=True)
def mock_embedding_providers():
    """Patches settings to always use mock embedding provider for tests."""
    with patch.object(settings, "EMBEDDING_PROVIDER", "mock"):
        yield


# =============================================================================
# Mathematical Computations & Similarity Unit Tests
# =============================================================================


def test_vector_similarity_math():
    v1 = [1.0, 0.0, 0.0]
    v2 = [0.0, 1.0, 0.0]
    v3 = [1.0, 1.0, 0.0]

    # Dot Product
    assert dot_product(v1, v2) == 0.0
    assert dot_product(v1, v3) == 1.0

    # Cosine Similarity
    assert cosine_similarity(v1, v2) == 0.0
    assert abs(cosine_similarity(v1, v3) - 0.7071) < 0.001
    assert cosine_similarity([0, 0], [1, 1]) == 0.0


# =============================================================================
# Providers & Device Auto-detect Unit Tests
# =============================================================================


def test_device_auto_detect():
    device = get_device()
    assert device in ["cpu", "cuda", "mps"]


def test_mock_provider_loading():
    provider = get_active_provider()
    assert provider.get_dimension() == 384
    assert provider.get_device() == "cpu"

    text = "Hello world"
    vec = provider.generate_embedding(text)
    assert len(vec) == 384
    assert isinstance(vec[0], float)

    batch_vecs = provider.batch_embedding([text, "test"])
    assert len(batch_vecs) == 2
    assert len(batch_vecs[0]) == 384


# =============================================================================
# Caching Manager Unit Tests
# =============================================================================


@pytest.mark.asyncio
async def test_embedding_cache_manager(db_session: AsyncSession):
    text = "Cache check text line"
    model = "mock"
    vector = [0.2] * 384

    # Save
    await EmbeddingCacheManager.save_embedding(db_session, text, vector, model)
    await db_session.commit()

    # Get single
    cached = await EmbeddingCacheManager.get_cached_embedding(db_session, text, model)
    assert cached is not None
    assert cached == vector

    # Get bulk
    bulk = await EmbeddingCacheManager.get_bulk_cached_embeddings(
        db_session, [text, "missing"], model
    )
    assert text in bulk
    assert "missing" not in bulk
    assert bulk[text] == vector

    # Clear
    cleared = await EmbeddingCacheManager.clear_cache(db_session)
    assert cleared > 0
    await db_session.commit()

    cached_empty = await EmbeddingCacheManager.get_cached_embedding(
        db_session, text, model
    )
    assert cached_empty is None


# =============================================================================
# Embedding Engine Service Tests
# =============================================================================


@pytest.mark.asyncio
async def test_embedding_engine_service(db_session: AsyncSession):
    texts = ["Sentence one for testing", "Sentence two for testing"]

    # Generate
    vectors = await EmbeddingEngineService.generate_embeddings(db_session, texts)
    assert len(vectors) == 2
    assert len(vectors[0]) == 384

    # Metrics
    metrics = EmbeddingEngineService.get_metrics()
    assert metrics["total_requests"] > 0
    assert metrics["active_provider"] == "mock"


# =============================================================================
# Semantic Search Execution Tests
# =============================================================================


def test_semantic_search_filtering():
    query = [1.0, 0.0, 0.0]
    candidates = [
        {
            "text": "Match One",
            "metadata": {"category": "Tech"},
            "embedding": [0.9, 0.1, 0.0],
        },
        {
            "text": "Match Two",
            "metadata": {"category": "Finance"},
            "embedding": [0.8, 0.0, 0.0],
        },
        {
            "text": "Match One",
            "metadata": {"category": "Tech"},
            "embedding": [0.9, 0.1, 0.0],
        },  # Duplicate text
        {
            "text": "Low Score",
            "metadata": {"category": "Tech"},
            "embedding": [0.1, 0.9, 0.0],
        },  # Under threshold
    ]

    # Search with Cosine threshold
    results = EmbeddingEngineService.semantic_search(
        query_embedding=query,
        candidates=candidates,
        limit=5,
        score_threshold=0.5,
        metric="cosine",
    )
    # Excludes duplicates and low score
    assert len(results) == 2
    assert results[0]["text"] == "Match Two"
    assert "embedding" not in results[0]

    # Search with metadata filter
    filtered_results = EmbeddingEngineService.semantic_search(
        query_embedding=query,
        candidates=candidates,
        limit=5,
        score_threshold=0.5,
        metric="cosine",
        metadata_filter={"category": "Finance"},
    )
    assert len(filtered_results) == 1
    assert filtered_results[0]["text"] == "Match Two"


# =============================================================================
# API Endpoint Integration Tests
# =============================================================================


@pytest.mark.asyncio
async def test_embeddings_api_routes(
    client: AsyncClient, auth_headers: dict, db_session: AsyncSession
):
    # Generate API
    payload = {"texts": ["Sentence one", "Sentence two"]}
    res = await client.post(
        "/api/v1/embeddings/generate", json=payload, headers=auth_headers
    )
    assert res.status_code == 200
    assert len(res.json()["data"]["embeddings"]) == 2

    # Providers API
    res = await client.get("/api/v1/embeddings/providers", headers=auth_headers)
    assert res.status_code == 200
    assert len(res.json()["data"]["providers"]) == len(MODEL_DIMENSIONS)

    # Status API
    res = await client.get("/api/v1/embeddings/status", headers=auth_headers)
    assert res.status_code == 200
    assert res.json()["data"]["active_provider"] == "mock"

    # Rebuild API
    res = await client.post("/api/v1/embeddings/rebuild", headers=auth_headers)
    assert res.status_code == 200
    assert res.json()["data"]["success"] is True


# =============================================================================
# Benchmarking Execution Tests
# =============================================================================


def test_benchmarking_utility():
    # Patch sentence-transformers loading to run instant mocks
    with patch(
        "app.features.embeddings.benchmarks.SentenceTransformersProvider"
    ) as mock_provider_class:
        mock_provider = MagicMock()
        mock_provider.get_dimension.return_value = 384
        mock_provider.get_device.return_value = "cpu"
        mock_provider.generate_embedding.return_value = [0.1] * 384
        mock_provider.batch_embedding.return_value = [[0.1] * 384]
        mock_provider_class.return_value = mock_provider

        bench_res = run_benchmark(["Sample text"])
        assert len(bench_res) == len(MODEL_DIMENSIONS)
        assert bench_res[0]["status"] == "success"
