"""
Embedding service abstraction wrapping sentence-transformers.
Uses a lazy-loaded, thread-safe singleton to avoid repeated model loading.
"""

import logging
import threading
from typing import Any

logger = logging.getLogger("app.knowledge.embeddings")


class EmbeddingService:
    """
    Thin wrapper around a sentence-transformers model.

    The model is loaded lazily on first use and cached as a module-level
    singleton.  Thread-safe initialization is ensured via a Lock.
    """

    def __init__(self, model_name: str) -> None:
        self._model_name = model_name
        self._model: Any | None = None
        self._lock = threading.Lock()

    def _load_model(self) -> Any:
        """Load the SentenceTransformer model if not already loaded."""
        if self._model is None:
            with self._lock:
                if self._model is None:
                    logger.info(
                        f"Loading embedding model: {self._model_name} (first use)."
                    )
                    from sentence_transformers import SentenceTransformer  # Lazy import

                    self._model = SentenceTransformer(self._model_name)
                    logger.info("Embedding model loaded successfully.")
        return self._model

    def embed(self, texts: list[str]) -> list[list[float]]:
        """
        Produce embeddings for a list of text chunks.

        Args:
            texts: Non-empty list of text strings.

        Returns:
            List of float vectors, one per input text.
        """
        if not texts:
            return []

        model = self._load_model()
        logger.debug(f"Embedding {len(texts)} text chunks.")
        embeddings = model.encode(texts, show_progress_bar=False, convert_to_numpy=True)
        return [vec.tolist() for vec in embeddings]

    def embed_single(self, text: str) -> list[float]:
        """
        Produce a single embedding vector.

        Args:
            text: The query or document string to embed.

        Returns:
            A float vector of shape (embedding_dim,).
        """
        results = self.embed([text])
        return results[0] if results else []

    @property
    def model_name(self) -> str:
        return self._model_name


def build_embedding_service() -> EmbeddingService:
    """Factory that builds EmbeddingService from application settings."""
    from app.core.config.settings import settings

    return EmbeddingService(model_name=settings.KNOWLEDGE_EMBEDDING_MODEL)


# Module-level singleton — instantiated once per process
_embedding_service: EmbeddingService | None = None
_embedding_lock = threading.Lock()


def get_embedding_service() -> EmbeddingService:
    """Return the global EmbeddingService singleton (thread-safe)."""
    global _embedding_service
    if _embedding_service is None:
        with _embedding_lock:
            if _embedding_service is None:
                _embedding_service = build_embedding_service()
    return _embedding_service
