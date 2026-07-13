import logging

from redis.asyncio import Redis, from_url

from app.core.config.settings import settings

logger = logging.getLogger("app.database.redis")


class RedisManager:
    """
    Optional Redis client manager.

    When ``redis_url`` is ``None`` (REDIS_URL env var not set), the manager
    operates in *disabled* mode: every operation is a no-op and
    ``is_configured`` returns ``False``.  No exception is raised at import or
    startup time.

    When ``redis_url`` is set the manager behaves identically to before —
    lazy client initialisation, connection pooling, and health-ping support.
    """

    def __init__(self, redis_url: str | None) -> None:
        self._redis_url = redis_url
        self._client: Redis | None = None

        if redis_url is None:
            logger.warning(
                "REDIS_URL is not set. Redis caching and session storage are "
                "disabled. Set the REDIS_URL environment variable (e.g. via a "
                "Railway Redis add-on) to enable them."
            )
        else:
            logger.info("Redis configured — client will connect on first use.")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @property
    def is_configured(self) -> bool:
        """Return True when a REDIS_URL has been provided."""
        return self._redis_url is not None

    def get_client(self) -> Redis | None:
        """
        Return the active Redis client, initialising it on first call.

        Returns ``None`` when Redis is not configured so that callers can
        guard with a simple ``if client:`` check rather than catching
        exceptions.
        """
        if not self.is_configured:
            return None
        if self._client is None:
            self._client = from_url(
                self._redis_url,  # type: ignore[arg-type]
                decode_responses=True,
            )
        return self._client

    async def close(self) -> None:
        """Close active connection pools (no-op when not configured)."""
        if self._client is not None:
            await self._client.aclose()
            self._client = None
            logger.info("Closed Redis connection pool.")

    async def ping(self) -> bool:
        """
        Perform a health-check ping.

        Returns ``False`` both when Redis is not configured *and* when the
        server is unreachable, so callers do not need to special-case the
        disabled state.
        """
        if not self.is_configured:
            return False
        try:
            client = self.get_client()
            if client is None:
                return False
            response = await client.ping()
            return response is True
        except Exception as e:
            logger.error("Redis connection check failed: %s", e)
            return False


# ---------------------------------------------------------------------------
# Singleton — shared across the entire application process
# ---------------------------------------------------------------------------
redis_manager = RedisManager(settings.REDIS_URL)
