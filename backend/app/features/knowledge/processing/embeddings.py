import logging
import threading
from typing import Any

from app.core.config.settings import settings
from app.features.memory.embeddings import EmbeddingProvider, MockEmbeddingProvider

logger = logging.getLogger("app.knowledge.embeddings")


class SentenceTransformersEmbeddingProvider(EmbeddingProvider):
    """
    Sentence Transformers implementation of the EmbeddingProvider interface.
    Uses thread-safe lazy loading to cache the model.
    """

    def __init__(self, model_name: str) -> None:
        self.model_name = model_name
        self._model: Any = None
        self._lock = threading.Lock()

    def _load_model(self) -> Any:
        if self._model is None:
            with self._lock:
                if self._model is None:
                    logger.info(
                        f"Loading sentence-transformers model: {self.model_name}"
                    )
                    from sentence_transformers import SentenceTransformer  # Lazy import

                    self._model = SentenceTransformer(self.model_name)
                    logger.info("Model loaded successfully.")
        return self._model

    def generate_embedding(self, text: str) -> list[float]:
        if not text:
            return []
        model = self._load_model()
        vector = model.encode(text, convert_to_numpy=True)
        return vector.tolist()

    def batch_embedding(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        model = self._load_model()
        vectors = model.encode(texts, show_progress_bar=False, convert_to_numpy=True)
        return [v.tolist() for v in vectors]


# Registry pattern or factory helper
def get_embedding_provider() -> EmbeddingProvider:
    """
    Returns the configured EmbeddingProvider.
    Uses MockEmbeddingProvider if set to mock, or SentenceTransformersEmbeddingProvider.
    """
    # For testing and lightweight execution, we support fallback to mock embedding provider
    if getattr(settings, "KNOWLEDGE_EMBEDDING_MODEL", None) == "mock":
        return MockEmbeddingProvider(dimension=384)

    try:
        model_name = getattr(settings, "KNOWLEDGE_EMBEDDING_MODEL", "all-MiniLM-L6-v2")
        return SentenceTransformersEmbeddingProvider(model_name)
    except ImportError:
        logger.warning(
            "sentence-transformers not installed. Falling back to MockEmbeddingProvider."
        )
        return MockEmbeddingProvider(dimension=384)
