import asyncio
import shutil
import tempfile
from collections.abc import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

import app.core.database.session as db_session_module
from app.core.config.settings import settings
from app.core.database.mixins import Base
from app.core.database.session import get_db_session
from app.main import app

# Test Database URL (In-memory SQLite)
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

# Create test engine
test_engine = create_async_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
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


@pytest.fixture(autouse=True)
async def init_test_db():
    """
    Initialize the database schemas before executing tests.
    """
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Yields a transaction-scoped database session for unit tests.
    """
    async with TestingSessionLocal() as session:
        yield session
        await session.rollback()


@pytest.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """
    API client fixture overriding the database dependency with the test session.
    """

    async def _override_get_db_session() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    app.dependency_overrides[get_db_session] = _override_get_db_session

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="https://test"
    ) as ac:
        yield ac

    app.dependency_overrides.clear()
