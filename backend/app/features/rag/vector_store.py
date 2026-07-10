import uuid
from typing import Any

from app.features.vector.providers import get_vector_store_provider


class RAGVectorStore:
    """Handles insertions, deletions, clearing, and semantic matching on active vector store."""

    @staticmethod
    def add_chunks(
        user_id: uuid.UUID,
        chunk_ids: list[str],
        embeddings: list[list[float]],
        metadatas: list[dict[str, Any]],
    ) -> None:
        """Add batch of vector chunks to the database."""
        provider = get_vector_store_provider()
        provider.add_chunks(user_id, chunk_ids, embeddings, metadatas)

    @staticmethod
    def delete_chunks(user_id: uuid.UUID, chunk_ids: list[str]) -> None:
        """Remove chunks by IDs."""
        provider = get_vector_store_provider()
        provider.delete_chunks(user_id, chunk_ids)

    @staticmethod
    def clear(user_id: uuid.UUID) -> None:
        """Clear all indexed points for a specific user."""
        provider = get_vector_store_provider()
        provider.clear(user_id)

    @staticmethod
    def search(
        user_id: uuid.UUID,
        query_vector: list[float],
        limit: int = 5,
        metadata_filter: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """Search vector database with query vector and optional filters."""
        provider = get_vector_store_provider()
        return provider.search(
            user_id=user_id,
            query_vector=query_vector,
            limit=limit,
            metadata_filter=metadata_filter,
        )
