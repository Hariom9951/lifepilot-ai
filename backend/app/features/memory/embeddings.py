import hashlib
import random
from abc import ABC, abstractmethod


class EmbeddingProvider(ABC):
    """
    Abstract Base Class for generating vector embeddings.
    """

    @abstractmethod
    def generate_embedding(self, text: str) -> list[float]:
        """
        Generate embedding for a single text.
        """
        pass

    @abstractmethod
    def batch_embedding(self, texts: list[str]) -> list[list[float]]:
        """
        Generate embeddings for a list of texts.
        """
        pass


class MockEmbeddingProvider(EmbeddingProvider):
    """
    Mock Embedding Provider generating deterministic mock vectors of size 384.
    Utilizes hashing to generate identical vectors for identical inputs.
    """

    def __init__(self, dimension: int = 384) -> None:
        self.dimension = dimension

    def generate_embedding(self, text: str) -> list[float]:
        # Create a stable seed from the text hash
        hash_val = int(hashlib.sha256(text.encode("utf-8")).hexdigest(), 16)
        rng = random.Random(hash_val)
        # Generate dimension float values normalized between -1.0 and 1.0
        return [rng.uniform(-1.0, 1.0) for _ in range(self.dimension)]

    def batch_embedding(self, texts: list[str]) -> list[list[float]]:
        return [self.generate_embedding(text) for text in texts]
