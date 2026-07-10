import asyncio
import os
import shutil
import subprocess
import sys
import tempfile
from collections.abc import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import pool
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# Import database session modules and settings
import app.core.database.session as db_session_module
from app.core.config.settings import settings
from app.core.database.mixins import Base

# Import all SQLAlchemy models to ensure Base.metadata registers them
from app.features.analytics.models import (  # noqa: F401
    AnalyticsBudget,
    AnalyticsExpense,
    AnalyticsGoal,
    AnalyticsHabit,
    AnalyticsTask,
)
from app.features.assistant.models import AssistantChat  # noqa: F401
from app.features.auth.models import RefreshToken, Role, User  # noqa: F401
from app.features.embeddings.models import EmbeddingCache  # noqa: F401
from app.features.knowledge.models import Document  # noqa: F401
from app.features.memory.models import (  # noqa: F401
    ConversationMessage,
    ConversationSession,
    ConversationSummary,
    MemoryCategory,
    MemoryTag,
    UserMemory,
)
from app.features.vector.models import VectorDocumentChunk  # noqa: F401
from app.main import app

# Ensure test session uses the exact same DATABASE_URL as settings (no mismatches)
TEST_DATABASE_URL = settings.DATABASE_URL

# Create test engine
test_engine = create_async_engine(
    TEST_DATABASE_URL,
    poolclass=pool.NullPool,
)

# Test session factory
TestingSessionLocal = async_sessionmaker(
    bind=test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# Monkeypatch SessionLocal and engine globally for background task compatibility
db_session_module.SessionLocal = TestingSessionLocal
db_session_module.engine = test_engine

# Setup isolated directories for vector persistent databases and uploads
temp_vector_dir = tempfile.mkdtemp()
settings.CHROMA_DB_PATH = temp_vector_dir
settings.KNOWLEDGE_VECTOR_DIR = temp_vector_dir
settings.KNOWLEDGE_UPLOAD_DIR = temp_vector_dir


def run_alembic_migrations():
    """
    Run Alembic migrations programmatically against settings.DATABASE_URL.
    """
    cwd = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    # Run alembic upgrade head using subprocess to execute it in clean context
    subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        check=True,
        cwd=cwd,
    )


@pytest.fixture(scope="session", autouse=True)
def cleanup_temp_directories(request):
    """
    Session-level cleanup of all temporary directories created for the tests run.
    """

    def remove_temp():
        shutil.rmtree(temp_vector_dir, ignore_errors=True)

    request.addfinalizer(remove_temp)


@pytest.fixture
def event_loop():
    """
    Creates an instance of the default event loop for the test session.
    """
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session", autouse=True)
def init_test_db_session():
    """
    Initialize the database schema once at the start of the entire test session.
    """
    # 1. Clear database before running migrations if using SQLite
    if "sqlite" in settings.DATABASE_URL:
        db_path = settings.DATABASE_URL.replace("sqlite+aiosqlite:///", "")
        if os.path.exists(db_path):
            try:
                os.remove(db_path)
            except Exception:
                pass

    # 2. Run migrations
    run_alembic_migrations()
    yield


@pytest.fixture(autouse=True)
async def clean_db_between_tests():
    """
    Clean up database data between tests to ensure test isolation.
    """
    yield
    # Delete data from all tables, keeping table structures intact
    async with test_engine.begin() as conn:
        for table in reversed(Base.metadata.sorted_tables):
            await conn.execute(table.delete())


@pytest.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Yields a transaction-scoped database session for unit tests.
    """
    async with db_session_module.SessionLocal() as session:
        yield session
        await session.rollback()


@pytest.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    """
    API client fixture for integration testing.
    """
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="https://test"
    ) as ac:
        yield ac
