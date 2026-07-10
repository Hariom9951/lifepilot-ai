import uuid
from datetime import timedelta
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import UploadFile
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config.settings import settings
from app.features.auth.models import Role, User
from app.features.auth.repositories import RoleRepository, UserRepository
from app.features.auth.security import create_access_token
from app.features.knowledge.exceptions import (
    FileTooLargeError,
    UnsupportedFileTypeError,
)
from app.features.knowledge.models import Document, DocumentStatus
from app.features.knowledge.processing.chunker import ChunkingStrategy, get_chunker
from app.features.knowledge.processing.storage import LocalStorageProvider
from app.features.knowledge.services import KnowledgeService
from tests.test_memory import DummyAsyncContextManager

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
    user = await UserRepository.get_by_username(db_session, "knowledge_tester")
    if not user:
        user = await UserRepository.create(
            db_session,
            {
                "full_name": "Knowledge Tester",
                "username": "knowledge_tester",
                "email": "tester_rag@example.com",
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
def mock_storage(tmp_path):
    provider = LocalStorageProvider(base_dir=tmp_path)
    KnowledgeService.set_storage_provider(provider)
    return provider


@pytest.fixture(autouse=True)
def mock_embedding_provider():
    from app.features.memory.embeddings import MockEmbeddingProvider

    with patch(
        "app.features.knowledge.services.get_embedding_provider",
        return_value=MockEmbeddingProvider(dimension=384),
    ):
        yield


# =============================================================================
# Chunker Unit Tests
# =============================================================================


def test_chunkers():
    text = "Paragraph one. It has some text. \n\nParagraph two. It is separate."

    # Fixed Size Chunker
    fixed = get_chunker(ChunkingStrategy.FIXED, chunk_size=30, chunk_overlap=5)
    c_fixed = fixed.chunk(text)
    assert len(c_fixed) > 0

    # Recursive Chunker
    rec = get_chunker(ChunkingStrategy.RECURSIVE, chunk_size=40, chunk_overlap=10)
    c_rec = rec.chunk(text)
    assert len(c_rec) > 0

    # Paragraph Chunker
    para = get_chunker(ChunkingStrategy.PARAGRAPH, chunk_size=30, chunk_overlap=5)
    c_para = para.chunk(text)
    assert len(c_para) == 3

    # Sentence Chunker
    sent = get_chunker(ChunkingStrategy.SENTENCE, chunk_size=40, chunk_overlap=5)
    c_sent = sent.chunk(text)
    assert len(c_sent) > 0


# =============================================================================
# Storage Provider Unit Tests
# =============================================================================


def test_local_storage_provider(tmp_path):
    provider = LocalStorageProvider(base_dir=tmp_path)
    name = "test_file.txt"
    content = b"Storage content test"

    # Save
    path = provider.save_file(name, content)
    assert Path(path).exists()

    # Load
    loaded = provider.load_file(name)
    assert loaded == content

    # Delete
    provider.delete_file(name)
    assert not Path(path).exists()

    with pytest.raises(FileNotFoundError):
        provider.load_file(name)


# =============================================================================
# Knowledge Service Tests
# =============================================================================


@pytest.mark.asyncio
async def test_upload_document_service(db_session: AsyncSession, test_user: User):
    # Setup mock upload file
    mock_file = MagicMock(spec=UploadFile)
    mock_file.filename = "test_doc.txt"
    mock_file.content_type = "text/plain"
    mock_file.read = AsyncMock(return_value=b"Raw text contents for RAG search testing")

    # Success Upload
    doc = await KnowledgeService.upload_document(db_session, test_user.id, mock_file)
    assert doc.original_filename == "test_doc.txt"
    assert doc.status == DocumentStatus.UPLOADED

    # Validation Checks - Invalid Type
    mock_file.content_type = "application/invalid"
    with pytest.raises(UnsupportedFileTypeError):
        await KnowledgeService.upload_document(db_session, test_user.id, mock_file)

    # Validation Checks - Large File
    mock_file.content_type = "text/plain"
    large_size = (settings.KNOWLEDGE_MAX_FILE_SIZE_MB + 1) * 1024 * 1024
    mock_file.read = AsyncMock(return_value=b"x" * large_size)
    with pytest.raises(FileTooLargeError):
        await KnowledgeService.upload_document(db_session, test_user.id, mock_file)


@pytest.mark.asyncio
async def test_process_document_background(
    db_session: AsyncSession, test_user: User, tmp_path
):
    doc = Document(
        id=uuid.uuid4(),
        user_id=test_user.id,
        original_filename="dummy.txt",
        storage_filename="dummy.txt",
        mime_type="text/plain",
        file_size=20,
        status=DocumentStatus.UPLOADED,
    )
    db_session.add(doc)
    await db_session.commit()

    # Save initial mock file in storage
    storage = KnowledgeService.get_storage_provider()
    storage.save_file(
        "dummy.txt", b"Mock document raw content with keywords python developer."
    )

    # Patch SessionLocal and processing
    with patch(
        "app.features.knowledge.services.SessionLocal",
        return_value=DummyAsyncContextManager(db_session),
    ):
        await KnowledgeService.process_document_background(doc.id)

    # Re-query
    res = await db_session.execute(select(Document).where(Document.id == doc.id))
    processed = res.scalar_one()
    assert processed.status == DocumentStatus.READY
    assert processed.chunk_count > 0


@pytest.mark.asyncio
async def test_document_search_and_reindex(db_session: AsyncSession, test_user: User):
    doc = Document(
        id=uuid.uuid4(),
        user_id=test_user.id,
        original_filename="dummy2.txt",
        storage_filename="dummy2.txt",
        mime_type="text/plain",
        file_size=20,
        status=DocumentStatus.READY,
    )
    db_session.add(doc)
    await db_session.commit()

    # Seed mock vector result to simulate search match
    from app.features.knowledge.processing.vector_store import (
        get_document_vector_provider,
    )

    vec_provider = get_document_vector_provider()
    vec_provider.add(
        test_user.id,
        uuid.uuid4(),
        [0.1] * 384,
        {
            "document_id": str(doc.id),
            "text": "Python indexing search candidate",
            "category": "Coding",
        },
    )

    # Search
    search_res = await KnowledgeService.search_documents(
        db_session, test_user.id, query="Python", similarity_threshold=0.0
    )
    assert len(search_res) == 1
    assert search_res[0]["document_id"] == doc.id

    # Reindex
    reindexed = await KnowledgeService.reindex_user_documents(db_session, test_user.id)
    assert reindexed == 1
    await db_session.refresh(doc)
    assert doc.status == DocumentStatus.UPLOADED


# =============================================================================
# API Endpoint Integration Tests
# =============================================================================


@pytest.mark.asyncio
async def test_api_documents_lifecycle(
    client: AsyncClient, auth_headers: dict, db_session: AsyncSession
):
    # Upload
    files = {"file": ("test_api.txt", b"API RAG test upload file text", "text/plain")}
    res = await client.post(
        "/api/v1/documents/upload", files=files, headers=auth_headers
    )
    assert res.status_code == 202
    doc_id = res.json()["data"]["id"]

    # List
    res = await client.get("/api/v1/documents", headers=auth_headers)
    assert res.status_code == 200
    assert len(res.json()["data"]["items"]) == 1

    # Get Details
    res = await client.get(f"/api/v1/documents/{doc_id}", headers=auth_headers)
    assert res.status_code == 200

    # Get Status
    res = await client.get(f"/api/v1/documents/status/{doc_id}", headers=auth_headers)
    assert res.status_code == 200

    # Search (using threshold = 0.0 for mock hash vector compatibility)
    payload = {"query": "RAG", "limit": 2, "similarity_threshold": 0.0}
    res = await client.post(
        "/api/v1/documents/search", json=payload, headers=auth_headers
    )
    assert res.status_code == 200

    # Reindex
    res = await client.post("/api/v1/documents/reindex", headers=auth_headers)
    assert res.status_code == 200

    # Delete
    res = await client.delete(f"/api/v1/documents/{doc_id}", headers=auth_headers)
    assert res.status_code == 200


@pytest.mark.asyncio
async def test_api_legacy_knowledge_paths(client: AsyncClient, auth_headers: dict):
    # Fulfill compatibility verification
    res = await client.get("/api/v1/knowledge/documents", headers=auth_headers)
    assert res.status_code == 200
    assert res.json()["data"]["items"] == []


# =============================================================================
# Background Workers Tests
# =============================================================================


@pytest.mark.asyncio
async def test_retry_failed_documents_worker(db_session: AsyncSession, test_user: User):
    doc = Document(
        id=uuid.uuid4(),
        user_id=test_user.id,
        original_filename="failed_doc.txt",
        storage_filename="failed_doc.txt",
        mime_type="text/plain",
        file_size=20,
        status=DocumentStatus.FAILED,
        retry_count=0,
        retries_exhausted=False,
    )
    db_session.add(doc)
    await db_session.commit()

    # Run retry failed task with patched SessionLocal
    with patch(
        "app.features.knowledge.services.SessionLocal",
        return_value=DummyAsyncContextManager(db_session),
    ):
        retried = await KnowledgeService.retry_failed_documents()
    assert retried == 1


@pytest.mark.asyncio
async def test_cleanup_orphaned_files_worker(
    db_session: AsyncSession, test_user: User, tmp_path
):
    # Setup storage files
    storage = KnowledgeService.get_storage_provider()
    # Save a registered file
    storage.save_file("registered.txt", b"Data")
    # Save an orphaned file
    storage.save_file("orphaned.txt", b"Data")

    doc = Document(
        id=uuid.uuid4(),
        user_id=test_user.id,
        original_filename="registered.txt",
        storage_filename="registered.txt",
        mime_type="text/plain",
        file_size=4,
        status=DocumentStatus.READY,
    )
    db_session.add(doc)
    await db_session.commit()

    # Run cleanup failed task with patched SessionLocal
    with patch(
        "app.features.knowledge.services.SessionLocal",
        return_value=DummyAsyncContextManager(db_session),
    ):
        cleaned = await KnowledgeService.cleanup_orphaned_files()
    assert cleaned == 1
