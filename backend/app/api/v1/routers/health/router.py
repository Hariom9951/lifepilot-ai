import time

from fastapi import APIRouter
from sqlalchemy import text

from app.api.v1.routers.health.schemas import HealthStatus, ServiceStatus
from app.common.responses.schemas import SuccessResponse
from app.core.config.settings import settings
from app.core.database.redis import redis_manager
from app.core.dependencies.providers import DbSession

router = APIRouter(prefix="/health", tags=["Health Diagnostics"])


@router.get("", response_model=SuccessResponse[HealthStatus])
async def check_health(db: DbSession) -> SuccessResponse[HealthStatus]:
    """
    Performs full health checks on the application, database, and Redis cache.

    Redis status values:
    - ``"healthy"``  — Redis is configured and responding.
    - ``"unhealthy"`` — Redis is configured but unreachable.
    - ``"disabled"``  — REDIS_URL is not set; Redis is intentionally absent.
    """
    # 1. Check Database
    db_start = time.perf_counter()
    db_status = "healthy"
    db_message = "PostgreSQL asyncpg connection responsive."
    try:
        await db.execute(text("SELECT 1"))
    except Exception as e:
        db_status = "unhealthy"
        db_message = f"Database query failed: {str(e)}"
    db_time = (time.perf_counter() - db_start) * 1000

    # 2. Check Redis — three possible outcomes
    redis_start = time.perf_counter()
    if not redis_manager.is_configured:
        # Redis is intentionally absent; not a failure condition
        redis_status = "disabled"
        redis_message = "REDIS_URL is not set. Redis caching is disabled."
        redis_time = 0.0
    else:
        redis_status = "healthy"
        redis_message = "Redis server ping successful."
        try:
            redis_ok = await redis_manager.ping()
            if not redis_ok:
                redis_status = "unhealthy"
                redis_message = "Redis did not return a positive ping response."
        except Exception as e:
            redis_status = "unhealthy"
            redis_message = f"Redis ping failed: {str(e)}"
        redis_time = (time.perf_counter() - redis_start) * 1000

    # 3. Overall application status
    # "disabled" Redis is not a degradation — only a genuinely unreachable
    # configured Redis degrades the application status.
    app_status = "healthy"
    if db_status != "healthy" or redis_status == "unhealthy":
        app_status = "degraded"

    health_data = HealthStatus(
        application=app_status,
        database=ServiceStatus(
            status=db_status,
            message=db_message,
            response_time_ms=round(db_time, 2),
        ),
        redis=ServiceStatus(
            status=redis_status,
            message=redis_message,
            response_time_ms=round(redis_time, 2) if redis_time else None,
        ),
        version=settings.APP_VERSION,
        environment=settings.ENVIRONMENT,
    )

    return SuccessResponse(
        success=True,
        message="System status checked successfully.",
        data=health_data,
    )
