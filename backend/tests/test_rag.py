import uuid
from datetime import timedelta

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.features.auth.models import Role, User
from app.features.auth.repositories import RoleRepository, UserRepository
from app.features.auth.security import create_access_token
from app.features.memory.models import UserMemory
from app.features.rag.chunking import RAGChunker
from app.features.rag.embedding import RAGEmbeddingEngine
from app.features.rag.reranker import RAGReranker
from app.features.rag.services import RAGService


@pytest.fixture(autouse=True)
async def seed_role(db_session: AsyncSession):
    role = await RoleRepository.get_by_name(db_session, "USER")
    if not role:
        role = await RoleRepository.create(
            db_session, name="USER", description="Standard user"
        )
    await db_session.commit()
    return role


@pytest.fixture
async def test_user(db_session: AsyncSession, seed_role: Role) -> User:
    user = await UserRepository.get_by_username(db_session, "rag_tester")
    if not user:
        user = await UserRepository.create(
            db_session,
            {
                "full_name": "RAG Tester",
                "username": "rag_tester",
                "email": "rag@example.com",
                "hashed_password": "fakehash",
                "role_id": seed_role.id,
            },
        )
        await db_session.commit()
    return user


@pytest.mark.anyio
async def test_rag_chunker():
    """Verify that document parser correctly chunks text and retains metadata."""
    text = (
        "This is a long test document about Python programming. "
        "We need to split this text into multiple chunks."
    )
    chunks = RAGChunker.chunk_document(
        text=text,
        chunk_size=30,
        chunk_overlap=5,
        source="test.txt",
        document_id=uuid.uuid4(),
        metadata={"category": "test"},
    )
    assert len(chunks) > 0
    assert chunks[0]["source"] == "test.txt"
    assert "timestamp" in chunks[0]["metadata"]
    assert chunks[0]["metadata"]["category"] == "test"


@pytest.mark.anyio
async def test_rag_embedding_engine(db_session: AsyncSession):
    """Verify the central embedding engine integration returns active dimensions."""
    texts = ["hello world", "rag database"]
    embeddings = await RAGEmbeddingEngine.get_embeddings(db_session, texts)
    assert len(embeddings) == 2
    assert len(embeddings[0]) == RAGEmbeddingEngine.get_dimension()


@pytest.mark.anyio
async def test_rag_reranker():
    """Verify the keyword-overlap local reranking logic scores matching documents higher."""
    query = "database system"
    matches = [
        {"content": "I like ice cream", "score": 0.9, "document": "doc1.txt"},
        {
            "content": "Connecting to a database system locally",
            "score": 0.5,
            "document": "doc2.txt",
        },
    ]
    reranked = RAGReranker.rerank(query, matches, top_n=2)
    assert len(reranked) == 2
    assert reranked[0]["document"] == "doc2.txt"


@pytest.mark.anyio
async def test_rag_retrieval_and_ingestion(db_session: AsyncSession, test_user: User):
    """Verify user memories ingestion and retrieval pipelines."""
    # 1. Seed UserMemory
    memory = UserMemory(
        id=uuid.uuid4(),
        user_id=test_user.id,
        content="This is a private note about my custom local database guidelines.",
        importance_score=1.0,
        is_archived=False,
    )
    db_session.add(memory)
    await db_session.commit()

    # 2. Trigger Memory Indexing
    indexed_count = await RAGService.index_user_knowledge(db_session, test_user.id)
    assert indexed_count > 0

    # 3. Retrieve matching context
    matches = await RAGService.search_knowledge_base(
        db=db_session,
        user_id=test_user.id,
        query="database guidelines",
        limit=5,
        score_threshold=0.2,
    )
    assert len(matches) > 0
    assert matches[0]["document"] == "memory"
    assert "guidelines" in matches[0]["content"]

    # 4. Reindex all
    reindex_count = await RAGService.reindex_all_user_knowledge(
        db_session, test_user.id
    )
    assert reindex_count > 0


@pytest.mark.anyio
async def test_rag_api_endpoints(
    client: AsyncClient, db_session: AsyncSession, test_user: User
):
    """Verify POST search and POST index APIs."""
    token = create_access_token(
        subject=str(test_user.id), expires_delta=timedelta(hours=1)
    )
    headers = {"Authorization": f"Bearer {token}"}

    # Seed UserMemory
    memory = UserMemory(
        id=uuid.uuid4(),
        user_id=test_user.id,
        content="AI ideas for LifePilot project.",
        importance_score=1.0,
        is_archived=False,
    )
    db_session.add(memory)
    await db_session.commit()

    # Trigger Indexing API
    index_res = await client.post(
        "/api/v1/rag/index",
        json={"notes": True, "journals": True},
        headers=headers,
    )
    assert index_res.status_code == 200
    assert index_res.json()["indexed_count"] > 0

    # Search API
    search_res = await client.post(
        "/api/v1/rag/search",
        json={"query": "AI ideas", "limit": 2, "score_threshold": 0.1},
        headers=headers,
    )
    assert search_res.status_code == 200
    data = search_res.json()
    assert data["query"] == "AI ideas"
    assert len(data["matches"]) > 0
    assert "AI ideas" in data["matches"][0]["content"]
