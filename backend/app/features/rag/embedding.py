from sqlalchemy.ext.asyncio import AsyncSession

from app.features.embeddings.providers import get_active_provider
from app.features.embeddings.services import EmbeddingEngineService


class RAGEmbeddingEngine:
    """Wrapper surrounding the core project-wide embedding caching services."""

    @staticmethod
    async def get_embeddings(db: AsyncSession, texts: list[str]) -> list[list[float]]:
        """Fetch cached or newly computed embeddings for text segments."""
        return await EmbeddingEngineService.generate_embeddings(db, texts)

    @staticmethod
    def get_dimension() -> int:
        """Fetch model dimensions from active embedding provider."""
        return get_active_provider().get_dimension()

    @staticmethod
    def get_provider_name() -> str:
        """Fetch model name/ID from active embedding provider."""
        return get_active_provider().model_name
