import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from sqlalchemy import text

from app.api.v1.routers.health.router import router as health_router
from app.core.config.settings import settings
from app.core.database.redis import redis_manager
from app.core.database.session import SessionLocal
from app.core.exceptions.handlers import register_exception_handlers
from app.core.logging.config import setup_logging
from app.core.middleware.request_id import RequestIdMiddleware
from app.core.middleware.security import SecurityHeadersMiddleware
from app.core.middleware.timing import RequestTimingMiddleware
from app.features.analytics.api import router as analytics_router
from app.features.assistant.api import router as assistant_router
from app.features.auth.api import router as auth_router
from app.features.embeddings.api import router as embeddings_router
from app.features.embeddings.providers import get_active_provider
from app.features.knowledge.api import documents_router, knowledge_router
from app.features.memory.api import router as memory_router
from app.features.rag.api import router as rag_router
from app.features.users.api import router as user_router
from app.features.vector.api import router as vector_router
from app.features.vector.providers import get_vector_store_provider


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: setup structured log directories and formatters
    setup_logging()
    logger = logging.getLogger("app.main")
    logger.info(f"Initializing {settings.APP_NAME} (version: {settings.APP_VERSION})")
    logger.info(f"Active Environment: {settings.ENVIRONMENT.upper()}")
    logger.info(f"Configuration settings: {settings.get_masked_settings()}")
    yield
    # Shutdown: clean up active Redis connection pools
    await redis_manager.close()


app = FastAPI(
    title=settings.APP_NAME,
    description="Scalable Clean Architecture backend foundation for LifePilot AI.",
    version=settings.APP_VERSION,
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    lifespan=lifespan,
)

# 1. Register Trusted Host Middleware
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["*"],  # Adjust for target production domain settings
)

# 2. Register Request ID tracing
app.add_middleware(RequestIdMiddleware)

# 3. Register Security headers
app.add_middleware(SecurityHeadersMiddleware)

# 4. Register CORS configuration
cors_origins = (
    [str(origin) for origin in settings.CORS_ORIGINS]
    if settings.CORS_ORIGINS
    else ([] if settings.ENVIRONMENT == "production" else ["*"])
)
if settings.ENVIRONMENT == "production" and not cors_origins:
    logger = logging.getLogger("app.main")
    logger.warning(
        "CORS_ORIGINS is empty in production mode. API calls will be blocked."
    )
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 5. Register GZip compression
app.add_middleware(
    GZipMiddleware,
    minimum_size=1000,
)

# 6. Register request processing latency logger
app.add_middleware(RequestTimingMiddleware)

# 7. Register global exception handlers
register_exception_handlers(app)

# 8. Register API routers (Versioned /api/v1/)
app.include_router(health_router, prefix="/api/v1")
app.include_router(auth_router, prefix="/api/v1")
app.include_router(user_router, prefix="/api/v1")
app.include_router(knowledge_router, prefix="/api/v1")
app.include_router(documents_router, prefix="/api/v1")
app.include_router(embeddings_router, prefix="/api/v1")
app.include_router(vector_router, prefix="/api/v1")
app.include_router(memory_router, prefix="/api/v1")
app.include_router(analytics_router, prefix="/api/v1")
app.include_router(assistant_router, prefix="/api/v1")
app.include_router(rag_router, prefix="/api/v1")


@app.get("/")
async def root_health() -> dict:
    """
    Root status check endpoint returning metadata.
    """
    return {
        "project": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
    }


@app.get("/ping")
async def ping() -> dict:
    """
    Pure liveness probe — always returns HTTP 200 as long as the process is running.
    Used by container orchestrators and CI to confirm the server has started,
    independently of any external dependency (database, Redis, etc.).
    """
    return {"status": "ok"}


@app.get("/health")
async def health_check(response: Response) -> dict:
    """
    Production Health API. Verifies database and Redis readiness.

    Redis field values:
    - ``"ok"``       — Redis configured and responding.
    - ``"error"``    — Redis configured but unreachable.
    - ``"disabled"`` — REDIS_URL not set; Redis intentionally absent.
    """
    db_ok = "ok"
    try:
        async with SessionLocal() as session:
            await session.execute(text("SELECT 1"))
    except Exception:
        db_ok = "error"

    if not redis_manager.is_configured:
        redis_ok = "disabled"
    else:
        redis_ok = "ok"
        try:
            ping_res = await redis_manager.ping()
            if not ping_res:
                redis_ok = "error"
        except Exception:
            redis_ok = "error"

    # Only a genuine Redis failure (not "disabled") degrades health
    status_str = "healthy"
    if db_ok != "ok" or redis_ok == "error":
        status_str = "unhealthy"
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return {
        "status": status_str,
        "database": db_ok,
        "redis": redis_ok,
        "version": "1.0.0",
    }


@app.get("/ready")
async def readiness_check(response: Response) -> dict:
    """
    Production Readiness API. Verifies databases, cache, embedding, and vector providers.

    Redis field values:
    - ``"ok"``       — Redis configured and responding.
    - ``"error"``    — Redis configured but unreachable.
    - ``"disabled"`` — REDIS_URL not set; caching gracefully skipped.
    """
    db_ok = "ok"
    try:
        async with SessionLocal() as session:
            await session.execute(text("SELECT 1"))
    except Exception:
        db_ok = "error"

    if not redis_manager.is_configured:
        redis_ok = "disabled"
    else:
        redis_ok = "ok"
        try:
            ping_res = await redis_manager.ping()
            if not ping_res:
                redis_ok = "error"
        except Exception:
            redis_ok = "error"

    emb_ok = "ok"
    try:
        provider = get_active_provider()
        if not provider or provider.get_dimension() <= 0:
            emb_ok = "error"
    except Exception:
        emb_ok = "error"

    vec_ok = "ok"
    try:
        v_provider = get_vector_store_provider()
        if not v_provider:
            vec_ok = "error"
    except Exception:
        vec_ok = "error"

    # "disabled" Redis is acceptable for readiness — only a genuine error fails
    status_str = "ready"
    if any(x == "error" for x in [db_ok, redis_ok, emb_ok, vec_ok]):
        status_str = "not_ready"
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return {
        "status": status_str,
        "database": db_ok,
        "redis": redis_ok,
        "embedding_provider": emb_ok,
        "vector_database": vec_ok,
    }
