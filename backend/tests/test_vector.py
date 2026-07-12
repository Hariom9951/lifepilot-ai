import uuid
from datetime import timedelta
from unittest.mock import patch

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config.settings import settings
from app.core.database.session import SessionLocal
from app.features.auth.models import Role, User
from app.features.auth.repositories import RoleRepository, UserRepository
from app.features.auth.security import create_access_token
from app.features.vector.providers import (
    ChromaVectorStoreProvider,
    FAISSVectorStoreProvider,
    QdrantVectorStoreProvider,
    get_vector_store_provider,
)
from app.features.vector.repositories import DocumentChunkRepository
from app.features.vector.services import HybridRetrievalService


@pytest.fixture(autouse=True)
async def seed_user_role():
    async with SessionLocal() as session:
        user_role = await RoleRepository.get_by_name(session, "USER")
        if not user_role:
            user_role = await RoleRepository.create(
                session, name="USER", description="Standard user"
            )
            await session.commit()
        return user_role


@pytest.fixture
async def test_user(seed_user_role: Role) -> User:
    async with SessionLocal() as session:
        user = await UserRepository.get_by_username(session, "vector_tester")
        if not user:
            user = await UserRepository.create(
                session,
                {
                    "full_name": "Vector Tester",
                    "username": "vector_tester",
                    "email": "tester_vector@example.com",
                    "hashed_password": "fakehashedpwd",
                    "role_id": seed_user_role.id,
                },
            )
            await session.commit()
            # Refresh user to load relationships and attach to current session state
            user = await UserRepository.get_by_id(session, user.id)
        return user


@pytest.fixture
def auth_headers(test_user: User) -> dict[str, str]:
    token = create_access_token(
        subject=str(test_user.id), expires_delta=timedelta(hours=1)
    )
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(autouse=True)
def mock_embedding_providers():
    from app.features.embeddings.providers import set_active_provider
    set_active_provider(None)
    with patch.object(settings, "EMBEDDING_PROVIDER", "mock"):
        # Force default settings to FAISS to avoid heavy chroma disk setups in fast unit tests
        with patch.object(settings, "VECTOR_PROVIDER", "faiss"):
            yield
    set_active_provider(None)


# =============================================================================
# Provider Swappability Tests
# =============================================================================


def test_vector_store_provider_factory():
    provider = get_vector_store_provider()
    assert isinstance(provider, FAISSVectorStoreProvider)

    with patch.object(settings, "VECTOR_PROVIDER", "chroma"):
        with patch("chromadb.PersistentClient"):
            p_chroma = get_vector_store_provider()
            assert isinstance(p_chroma, ChromaVectorStoreProvider)

    with patch.object(settings, "VECTOR_PROVIDER", "qdrant"):
        p_qdrant = get_vector_store_provider()
        assert isinstance(p_qdrant, QdrantVectorStoreProvider)


# =============================================================================
# SQL Persistence CRUD Tests
# =============================================================================


@pytest.mark.asyncio
async def test_document_chunk_repository(db_session: AsyncSession, test_user: User):
    cid = uuid.uuid4()
    content = "This is a custom database text chunk."

    # Add
    chunk = await DocumentChunkRepository.add_chunk(
        db=db_session,
        chunk_id=cid,
        user_id=test_user.id,
        content=content,
        source="doc1.txt",
        metadata_json={"tag": "finance"},
    )
    await db_session.commit()

    assert chunk.id == cid
    assert chunk.content == content
    assert chunk.source == "doc1.txt"

    # Get Single
    fetched = await DocumentChunkRepository.get_chunk(db_session, cid)
    assert fetched is not None
    assert fetched.content == content

    # Get User Chunks with filter
    filtered = await DocumentChunkRepository.get_user_chunks(
        db_session, test_user.id, {"tag": "finance"}
    )
    assert len(filtered) == 1
    assert filtered[0].id == cid

    # Delete
    deleted = await DocumentChunkRepository.delete_chunk(db_session, cid)
    assert deleted is True
    await db_session.commit()

    empty = await DocumentChunkRepository.get_chunk(db_session, cid)
    assert empty is None


# =============================================================================
# Hybrid Search Service Tests
# =============================================================================


@pytest.mark.asyncio
async def test_hybrid_search_orchestrator(db_session: AsyncSession, test_user: User):
    from app.features.knowledge.models import Document, DocumentStatus

    doc_id = uuid.uuid4()
    doc = Document(
        id=doc_id,
        user_id=test_user.id,
        original_filename="quarterly_report.pdf",
        storage_filename=str(uuid.uuid4()),
        mime_type="application/pdf",
        file_size=1024,
        status=DocumentStatus.READY,
    )
    db_session.add(doc)
    await db_session.commit()

    chunks = [
        {
            "id": str(uuid.uuid4()),
            "content": "Profit margins increased by twenty percent this quarter.",
            "document_id": doc_id,
            "source": "quarterly_report.pdf",
            "metadata": {"category": "business"},
        },
        {
            "id": str(uuid.uuid4()),
            "content": "Our machine learning models use advanced transformer architectures.",
            "document_id": doc_id,
            "source": "ml_guide.docx",
            "metadata": {"category": "tech"},
        },
        {
            "id": str(uuid.uuid4()),
            "content": "The quick brown fox jumps over the lazy dog.",
            "document_id": doc_id,
            "source": "animal_stories.txt",
            "metadata": {"category": "stories"},
        },
    ]

    # Index
    indexed = await HybridRetrievalService.batch_index_chunks(
        db_session, test_user.id, chunks
    )
    assert len(indexed) == 3
    await db_session.commit()

    # Search
    results = await HybridRetrievalService.hybrid_search(
        db=db_session,
        user_id=test_user.id,
        query="profit margins and business growth",
        limit=5,
        semantic_weight=0.0,
        keyword_weight=1.0,
    )
    assert len(results) > 0
    # First candidate should match business text due to BM25 content keyword matching
    assert "profit" in results[0]["content"].lower()

    # Rebuild Index
    count = await HybridRetrievalService.rebuild_index(db_session, test_user.id)
    assert count == 3
    await db_session.commit()

    # Delete Document Chunks
    deleted_count = await HybridRetrievalService.delete_by_document(
        db_session, test_user.id, doc_id
    )
    assert deleted_count == 3
    await db_session.commit()


# =============================================================================
# REST APIs Integration Tests
# =============================================================================


@pytest.mark.asyncio
async def test_vector_api_endpoints(
    client: AsyncClient, auth_headers: dict, db_session: AsyncSession
):
    # Index API
    payload = {
        "chunks": [
            {
                "content": "Vector databases speed up similarity lookup processes.",
                "source": "guide.txt",
                "metadata": {"doc_type": "textbook"},
            }
        ]
    }
    res = await client.post("/api/v1/vector/index", json=payload, headers=auth_headers)
    assert res.status_code == 201
    assert len(res.json()["data"]["indexed_chunks"]) == 1
    chunk_id = res.json()["data"]["indexed_chunks"][0]["id"]

    # Status API
    res = await client.get("/api/v1/vector/status", headers=auth_headers)
    assert res.status_code == 200
    assert res.json()["data"]["chunks_count"] > 0

    # Search API
    search_payload = {
        "query": "vector similarity lookup",
        "limit": 3,
        "semantic_weight": 0.5,
        "keyword_weight": 0.5,
        "metadata_filter": {"doc_type": "textbook"},
    }
    res = await client.post(
        "/api/v1/vector/search", json=search_payload, headers=auth_headers
    )
    assert res.status_code == 200
    assert len(res.json()["data"]["results"]) > 0

    # Rebuild API
    res = await client.post("/api/v1/vector/rebuild", headers=auth_headers)
    assert res.status_code == 200
    assert res.json()["data"]["success"] is True

    # Delete API
    res = await client.delete(f"/api/v1/vector/{chunk_id}", headers=auth_headers)
    assert res.status_code == 200
    assert res.json()["data"]["success"] is True
