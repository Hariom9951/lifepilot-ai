import uuid
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.features.auth.models import Role, User
from app.features.auth.repositories import RoleRepository, UserRepository
from app.features.auth.security import create_access_token
from app.features.memory.embeddings import MockEmbeddingProvider
from app.features.memory.exceptions import MemoryNotFoundError, SessionNotFoundError
from app.features.memory.models import (
    ConversationSession,
    ConversationSummary,
    UserMemory,
)
from app.features.memory.services import MemoryService
from app.features.memory.vector_providers import FAISSVectorProvider
from app.features.memory.workers import (
    cleanup_expired_sessions,
    run_conversation_summarization,
    run_importance_score_decay,
)


class DummyAsyncContextManager:
    def __init__(self, session):
        self.session = session

    async def __aenter__(self):
        return self.session

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass


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
    user = await UserRepository.get_by_username(db_session, "memory_tester")
    if not user:
        user = await UserRepository.create(
            db_session,
            {
                "full_name": "Memory Tester",
                "username": "memory_tester",
                "email": "tester@example.com",
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
def mock_redis():
    mock_client = AsyncMock()
    mock_client.get = AsyncMock(return_value=None)
    mock_client.set = AsyncMock(return_value=True)

    with patch(
        "app.core.database.redis.redis_manager.get_client", return_value=mock_client
    ):
        yield mock_client


@pytest.fixture(autouse=True)
def mock_vector_provider(tmp_path):
    provider = FAISSVectorProvider(base_dir=tmp_path, dimension=384)
    MemoryService.set_vector_provider(provider)
    return provider


# =============================================================================
# Embeddings & Vector Provider Unit Tests
# =============================================================================


def test_mock_embedding_provider():
    provider = MockEmbeddingProvider(dimension=128)
    emb = provider.generate_embedding("hello")
    assert len(emb) == 128
    assert isinstance(emb[0], float)

    # Determinism check
    emb2 = provider.generate_embedding("hello")
    assert emb == emb2

    # Batch test
    embs = provider.batch_embedding(["hello", "world"])
    assert len(embs) == 2
    assert len(embs[0]) == 128


def test_faiss_vector_provider(mock_vector_provider):
    user_id = uuid.uuid4()
    item_id = uuid.uuid4()
    emb = [0.1] * 384
    meta = {"content": "test item"}

    # Add
    mock_vector_provider.add(user_id, item_id, emb, meta)

    # Search
    results = mock_vector_provider.search(user_id, emb, k=1, threshold=0.1)
    assert len(results) == 1
    assert results[0]["item_id"] == str(item_id)
    assert results[0]["metadata"] == meta
    assert results[0]["score"] > 0.0

    # Delete
    mock_vector_provider.delete(user_id, item_id)
    results_after = mock_vector_provider.search(user_id, emb, k=1, threshold=0.1)
    assert len(results_after) == 0


# =============================================================================
# Memory Service Unit Tests
# =============================================================================


def test_calculate_importance():
    assert MemoryService.calculate_importance("short") == 1.0
    assert (
        MemoryService.calculate_importance(
            "This is a much longer memory to trigger score increase by length helper"
        )
        > 1.0
    )
    assert (
        MemoryService.calculate_importance("Please remember my favorite food is pizza")
        > 4.0
    )


@pytest.mark.asyncio
async def test_memory_crud_service(db_session: AsyncSession, test_user: User):
    # Create
    mem = await MemoryService.create_memory(
        db_session,
        user_id=test_user.id,
        content="I love debugging unit tests in Python",
        category_name="Testing",
        tags=["unit", "test"],
    )
    assert mem.content == "I love debugging unit tests in Python"
    assert mem.category.name == "Testing"
    assert len(mem.tags) == 2

    # Update
    updated = await MemoryService.update_memory(
        db_session,
        memory_id=mem.id,
        user_id=test_user.id,
        content="Updated test content",
        importance_score=9.5,
    )
    assert updated.content == "Updated test content"
    assert updated.importance_score == 9.5

    # List
    mems = await MemoryService.list_memories(db_session, user_id=test_user.id)
    assert len(mems) == 1

    # Search (using threshold = 0.0 for mock hash vector compatibility)
    search_res = await MemoryService.search_memory(
        db_session, user_id=test_user.id, query="test", similarity_threshold=0.0
    )
    assert len(search_res) == 1
    assert search_res[0]["memory"].id == mem.id

    # Archive
    archived = await MemoryService.archive_memory(db_session, mem.id, test_user.id)
    assert archived.is_archived is True

    # Delete
    await MemoryService.delete_memory(db_session, mem.id, test_user.id)
    with pytest.raises(MemoryNotFoundError):
        await MemoryService.update_memory(
            db_session, mem.id, test_user.id, content="nonexistent"
        )


@pytest.mark.asyncio
async def test_memory_merge_duplicates(db_session: AsyncSession, test_user: User):
    mem1 = await MemoryService.create_memory(
        db_session,
        user_id=test_user.id,
        content="Duplicate memory A",
        category_name="General",
        tags=["dup"],
    )
    mem2 = await MemoryService.create_memory(
        db_session,
        user_id=test_user.id,
        content="Duplicate memory B",
        category_name="General",
        tags=["tag"],
    )

    merged = await MemoryService.merge_duplicate_memory(
        db_session, test_user.id, mem1.id, mem2.id
    )
    assert "Duplicate memory A" in merged.content
    assert "Duplicate memory B" in merged.content
    assert len(merged.tags) == 2


@pytest.mark.asyncio
async def test_short_term_conversation_service(
    db_session: AsyncSession, test_user: User
):
    # Session Create
    sess = await MemoryService.create_session(
        db_session, user_id=test_user.id, title="Test Session", ttl_seconds=120
    )
    assert sess.title == "Test Session"

    # Message Add
    msg1 = await MemoryService.add_message(
        db_session,
        session_id=sess.id,
        user_id=test_user.id,
        role="user",
        content="Hello AI",
    )
    msg2 = await MemoryService.add_message(
        db_session,
        session_id=sess.id,
        user_id=test_user.id,
        role="assistant",
        content="Hello tester",
    )
    assert msg1.role == "user"
    assert msg2.role == "assistant"

    # Summarize
    summary = await MemoryService.summarize_conversation(
        db_session, sess.id, test_user.id
    )
    assert summary.session_id == sess.id
    assert "Summary of 2 messages" in summary.summary


# =============================================================================
# API Endpoint Integration Tests
# =============================================================================


@pytest.mark.asyncio
async def test_api_memory_lifecycle(
    client: AsyncClient, auth_headers: dict, db_session: AsyncSession
):
    # POST /memory
    payload = {
        "content": "Always use absolute imports in python files",
        "category_name": "Coding",
        "tags": ["python"],
    }
    res = await client.post("/api/v1/memory", json=payload, headers=auth_headers)
    assert res.status_code == 201
    mem_id = res.json()["data"]["id"]

    # GET /memory
    res = await client.get("/api/v1/memory", headers=auth_headers)
    assert res.status_code == 200
    assert len(res.json()["data"]) == 1

    # GET /memory/{id}
    res = await client.get(f"/api/v1/memory/{mem_id}", headers=auth_headers)
    assert res.status_code == 200
    assert (
        res.json()["data"]["content"] == "Always use absolute imports in python files"
    )

    # PATCH /memory/{id}
    patch_payload = {"content": "Use relative imports inside package structures"}
    res = await client.patch(
        f"/api/v1/memory/{mem_id}", json=patch_payload, headers=auth_headers
    )
    assert res.status_code == 200
    assert (
        res.json()["data"]["content"]
        == "Use relative imports inside package structures"
    )

    # POST /memory/search (using threshold = 0.0 for mock hash vector compatibility)
    search_payload = {
        "query": "python imports",
        "limit": 2,
        "similarity_threshold": 0.0,
    }
    res = await client.post(
        "/api/v1/memory/search", json=search_payload, headers=auth_headers
    )
    assert res.status_code == 200
    assert len(res.json()["data"]["results"]) == 1

    # POST /memory/archive
    archive_payload = {"memory_id": mem_id}
    res = await client.post(
        "/api/v1/memory/archive", json=archive_payload, headers=auth_headers
    )
    assert res.status_code == 200
    assert res.json()["data"]["is_archived"] is True

    # DELETE /memory/{id}
    res = await client.delete(f"/api/v1/memory/{mem_id}", headers=auth_headers)
    assert res.status_code == 200


@pytest.mark.asyncio
async def test_api_session_lifecycle(client: AsyncClient, auth_headers: dict):
    # Create session
    sess_payload = {"title": "API Test Session", "ttl_seconds": 3600}
    res = await client.post(
        "/api/v1/memory/session", json=sess_payload, headers=auth_headers
    )
    assert res.status_code == 201
    sess_id = res.json()["data"]["id"]

    # Summarize session
    res = await client.post(
        f"/api/v1/memory/summarize?session_id={sess_id}", headers=auth_headers
    )
    assert res.status_code == 202
    assert res.json()["data"]["session_id"] == sess_id


# =============================================================================
# Background Workers Tests
# =============================================================================


@pytest.mark.asyncio
async def test_summarize_session_worker(db_session: AsyncSession, test_user: User):
    sess = await MemoryService.create_session(
        db_session, user_id=test_user.id, title="Worker Session", ttl_seconds=120
    )
    await MemoryService.add_message(
        db_session, sess.id, test_user.id, "user", "Task test message"
    )

    # Run background task function with patched SessionLocal
    with patch(
        "app.features.memory.workers.SessionLocal",
        return_value=DummyAsyncContextManager(db_session),
    ):
        await run_conversation_summarization(sess.id, test_user.id)

    # Check that summary exists
    res = await db_session.execute(
        select(ConversationSummary).where(ConversationSummary.session_id == sess.id)
    )
    summary = res.scalar_one_or_none()
    assert summary is not None
    assert "Summary of 1 messages" in summary.summary


@pytest.mark.asyncio
async def test_cleanup_expired_sessions_worker(
    db_session: AsyncSession, test_user: User
):
    # Expired session
    sess = ConversationSession(
        user_id=test_user.id,
        title="Expired session test",
        expires_at=datetime.now(UTC) - timedelta(seconds=10),
    )
    db_session.add(sess)
    await db_session.commit()

    # Run cleanup worker with patched SessionLocal
    with patch(
        "app.features.memory.workers.SessionLocal",
        return_value=DummyAsyncContextManager(db_session),
    ):
        deleted = await cleanup_expired_sessions()
    assert deleted == 1


@pytest.mark.asyncio
async def test_run_importance_score_decay_worker(
    db_session: AsyncSession, test_user: User
):
    mem = await MemoryService.create_memory(
        db_session,
        user_id=test_user.id,
        content="Important message",
        category_name="General",
    )
    original_score = mem.importance_score

    # Decaying with patched SessionLocal
    with patch(
        "app.features.memory.workers.SessionLocal",
        return_value=DummyAsyncContextManager(db_session),
    ):
        await run_importance_score_decay(decay_factor=0.5)

    # Re-query rather than refresh because mock session context exited
    res = await db_session.execute(select(UserMemory).where(UserMemory.id == mem.id))
    decayed_mem = res.scalar_one()
    assert decayed_mem.importance_score == original_score * 0.5


def test_faiss_vector_provider_corrupt_and_duplicates(mock_vector_provider, tmp_path):
    user_id = uuid.uuid4()
    item_id = uuid.uuid4()
    emb = [0.2] * 384

    # Duplicate add verification
    mock_vector_provider.add(user_id, item_id, emb, {"c": "first"})
    mock_vector_provider.add(user_id, item_id, emb, {"c": "second"})
    res = mock_vector_provider.search(user_id, emb, k=1, threshold=0.1)
    assert len(res) == 1
    assert res[0]["metadata"]["c"] == "second"

    # Corrupt index path check
    index_path = tmp_path / "memories" / str(user_id) / "index.faiss"
    index_path.write_text("corrupted content", encoding="utf-8")

    # Load index should fall back and load empty index instead of crashing
    idx, meta = mock_vector_provider._load_index(user_id)
    assert idx.ntotal == 0
    assert len(meta) == 0


@pytest.mark.asyncio
async def test_memory_crud_edge_cases(db_session: AsyncSession, test_user: User):
    # Empty tags / Empty category update
    mem = await MemoryService.create_memory(
        db_session,
        user_id=test_user.id,
        content="Testing imports and tags",
    )
    assert mem.category_id is None
    assert len(mem.tags) == 0

    # Update empty category / tags
    updated = await MemoryService.update_memory(
        db_session,
        memory_id=mem.id,
        user_id=test_user.id,
        category_name="",
        tags=[],
    )
    assert updated.category_id is None
    assert len(updated.tags) == 0

    # Merge duplicates exceptions check
    invalid_id = uuid.uuid4()
    with pytest.raises(MemoryNotFoundError):
        await MemoryService.merge_duplicate_memory(
            db_session, test_user.id, mem.id, invalid_id
        )

    # Delete exceptions check
    with pytest.raises(MemoryNotFoundError):
        await MemoryService.delete_memory(db_session, invalid_id, test_user.id)


@pytest.mark.asyncio
async def test_api_memory_edge_cases(
    client: AsyncClient,
    auth_headers: dict,
    db_session: AsyncSession,
    test_user: User,
):
    # GET /memory/{id} invalid check
    invalid_id = uuid.uuid4()
    res = await client.get(f"/api/v1/memory/{invalid_id}", headers=auth_headers)
    assert res.status_code == 404

    # PATCH /memory/{id} invalid check
    res = await client.patch(
        f"/api/v1/memory/{invalid_id}",
        json={"content": "new text"},
        headers=auth_headers,
    )
    assert res.status_code == 404

    # DELETE /memory/{id} invalid check
    res = await client.delete(f"/api/v1/memory/{invalid_id}", headers=auth_headers)
    assert res.status_code == 404

    # Merge POST /memory/merge check
    mem1 = await MemoryService.create_memory(
        db_session, test_user.id, "Merge content A"
    )
    mem2 = await MemoryService.create_memory(
        db_session, test_user.id, "Merge content B"
    )
    merge_payload = {"memory_id_1": str(mem1.id), "memory_id_2": str(mem2.id)}
    res = await client.post(
        "/api/v1/memory/merge", json=merge_payload, headers=auth_headers
    )
    assert res.status_code == 200
    assert "Merge content A" in res.json()["data"]["content"]


@pytest.mark.asyncio
async def test_redis_cache_error_handling(db_session: AsyncSession, test_user: User):
    # Test Redis exception safety
    with patch("app.core.database.redis.redis_manager.get_client") as mock_get:
        mock_client = MagicMock()
        mock_client.set = AsyncMock(side_effect=Exception("Redis connection error"))
        mock_client.get = AsyncMock(side_effect=Exception("Redis connection error"))
        mock_get.return_value = mock_client

        # caching should not raise error
        await MemoryService.cache_session_data(uuid.uuid4(), {"test": 1})
        data = await MemoryService.get_cached_session_data(uuid.uuid4())
        assert data is None


@pytest.mark.asyncio
async def test_session_expiration_error(db_session: AsyncSession, test_user: User):
    # Expired session message addition
    sess = ConversationSession(
        user_id=test_user.id,
        title="Expired Session",
        expires_at=datetime.now(UTC) - timedelta(seconds=1),
    )
    db_session.add(sess)
    await db_session.commit()

    with pytest.raises(SessionNotFoundError):
        await MemoryService.add_message(
            db_session, sess.id, test_user.id, "user", "Hello"
        )

    # get_session invalid session check
    with pytest.raises(SessionNotFoundError):
        await MemoryService.get_session(db_session, uuid.uuid4(), test_user.id)
