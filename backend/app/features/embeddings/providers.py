import logging
import threading
from abc import ABC, abstractmethod
from collections.abc import Generator
from typing import Any

import torch

from app.core.config.settings import settings
from app.features.memory.embeddings import EmbeddingProvider, MockEmbeddingProvider

logger = logging.getLogger("app.embeddings.providers")

# Available model dimensions mapping
MODEL_DIMENSIONS = {
    "BAAI/bge-small-en-v1.5": 384,
    "BAAI/bge-base-en-v1.5": 768,
    "intfloat/e5-base-v2": 768,
    "sentence-transformers/all-MiniLM-L6-v2": 384,
}


def get_device() -> str:
    """Auto-detects active hardware device."""
    if torch.cuda.is_available():
        return "cuda"
    elif torch.backends.mps.is_available():
        return "mps"
    return "cpu"


class BaseEmbeddingProvider(EmbeddingProvider, ABC):
    """
    Abstract base class extending the Phase 5 EmbeddingProvider.
    """

    @abstractmethod
    def get_dimension(self) -> int:
        """Returns the embedding dimensions."""
        pass

    @abstractmethod
    def get_device(self) -> str:
        """Returns the active processing device."""
        pass

    @abstractmethod
    def stream_embeddings(
        self, texts: list[str], batch_size: int = 32
    ) -> Generator[list[list[float]], None, None]:
        """Yields chunks of embeddings batch by batch."""
        pass


class SentenceTransformersProvider(BaseEmbeddingProvider):
    """
    Production-quality Sentence Transformers provider supporting multi-models,
    GPU/CPU auto-detection, batching, and streaming.
    """

    def __init__(
        self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"
    ) -> None:
        self.model_name = model_name
        self.dimension = MODEL_DIMENSIONS.get(model_name, 384)
        self._model: Any = None
        self._device = get_device()
        self._lock = threading.Lock()

    def _load_model(self) -> Any:
        if self._model is None:
            with self._lock:
                if self._model is None:
                    logger.info(
                        f"Loading model '{self.model_name}' on device '{self._device}'"
                    )
                    from sentence_transformers import SentenceTransformer

                    self._model = SentenceTransformer(
                        self.model_name, device=self._device
                    )
        return self._model

    def get_dimension(self) -> int:
        return self.dimension

    def get_device(self) -> str:
        return self._device

    def generate_embedding(self, text: str) -> list[float]:
        if not text:
            return []
        model = self._load_model()
        # For e5-base-v2, queries require prefix "query: " to match documentation guidelines
        input_text = (
            f"query: {text}" if self.model_name == "intfloat/e5-base-v2" else text
        )
        vector = model.encode(input_text, convert_to_numpy=True)
        return vector.tolist()

    def batch_embedding(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        model = self._load_model()

        # Prepare prefix if model is e5-base-v2
        processed_texts = []
        for text in texts:
            processed_texts.append(
                f"passage: {text}" if self.model_name == "intfloat/e5-base-v2" else text
            )

        vectors = model.encode(
            processed_texts,
            show_progress_bar=False,
            convert_to_numpy=True,
            device=self._device,
        )
        return [v.tolist() for v in vectors]

    def stream_embeddings(
        self, texts: list[str], batch_size: int = 32
    ) -> Generator[list[list[float]], None, None]:
        """
        Yields batches of embeddings sequentially to support progressive streaming.
        """
        if not texts:
            return

        model = self._load_model()
        total_texts = len(texts)

        for i in range(0, total_texts, batch_size):
            batch = texts[i : i + batch_size]
            processed_batch = []
            for text in batch:
                processed_batch.append(
                    f"passage: {text}"
                    if self.model_name == "intfloat/e5-base-v2"
                    else text
                )
            vectors = model.encode(
                processed_batch,
                show_progress_bar=False,
                convert_to_numpy=True,
                device=self._device,
            )
            yield [v.tolist() for v in vectors]


# Registry or factory helper
_active_provider: BaseEmbeddingProvider | None = None


def get_active_provider() -> BaseEmbeddingProvider:
    """
    Returns the singleton active production embedding provider.
    """
    global _active_provider
    if _active_provider is None:
        provider_name = getattr(
            settings, "EMBEDDING_PROVIDER", "sentence-transformers/all-MiniLM-L6-v2"
        )
        if provider_name == "mock":
            # Support mock provider wrapper to behave like BaseEmbeddingProvider
            class WrapperMockProvider(BaseEmbeddingProvider):
                def __init__(self):
                    self.mock = MockEmbeddingProvider(dimension=384)
                    self.model_name = "mock"

                def get_dimension(self) -> int:
                    return 384

                def get_device(self) -> str:
                    return "cpu"

                def generate_embedding(self, text: str) -> list[float]:
                    return self.mock.generate_embedding(text)

                def batch_embedding(self, texts: list[str]) -> list[list[float]]:
                    return self.mock.batch_embedding(texts)

                def stream_embeddings(self, texts: list[str], batch_size: int = 32):
                    for i in range(0, len(texts), batch_size):
                        yield self.mock.batch_embedding(texts[i : i + batch_size])

            _active_provider = WrapperMockProvider()
        else:
            _active_provider = SentenceTransformersProvider(provider_name)
    return _active_provider


def set_active_provider(provider: BaseEmbeddingProvider) -> None:
    global _active_provider
    _active_provider = provider
