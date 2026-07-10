from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

from app.api.v1.routers.health.router import router as health_router
from app.core.config.settings import settings
from app.core.database.redis import redis_manager
from app.core.exceptions.handlers import register_exception_handlers
from app.core.logging.config import setup_logging
from app.core.middleware.request_id import RequestIdMiddleware
from app.core.middleware.security import SecurityHeadersMiddleware
from app.core.middleware.timing import RequestTimingMiddleware
from app.features.analytics.api import router as analytics_router
from app.features.auth.api import router as auth_router
from app.features.embeddings.api import router as embeddings_router
from app.features.knowledge.api import documents_router, knowledge_router
from app.features.memory.api import router as memory_router
from app.features.users.api import router as user_router
from app.features.vector.api import router as vector_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: setup structured log directories and formatters
    setup_logging()
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
    else ["*"]
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
