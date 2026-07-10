import logging

from redis.asyncio import Redis, from_url

from app.core.config.settings import settings

logger = logging.getLogger("app.database.redis")


class RedisManager:
    """
    Manager class responsible for Redis client initialization and lifecycle health status checks.
    """

    def __init__(self, redis_url: str):
        self._redis_url = redis_url
        self._client: Redis | None = None

    def get_client(self) -> Redis:
        """
        Return active Redis client. Initializes client on demand.
        """
        if self._client is None:
            self._client = from_url(self._redis_url, decode_responses=True)
        return self._client

    async def close(self) -> None:
        """
        Close active connection pools.
        """
        if self._client is not None:
            await self._client.aclose()
            self._client = None
            logger.info("Closed Redis connection pool.")

    async def ping(self) -> bool:
        """
        Performs a health check ping to verify that the Redis server is responsive.
        """
        try:
            client = self.get_client()
            response = await client.ping()
            return response is True
        except Exception as e:
            logger.error(f"Redis connection check failed: {e}")
            return False


# Singleton Redis manager instance
redis_manager = RedisManager(settings.REDIS_URL)
