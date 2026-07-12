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
        if not text:
            return [0.0] * self.dimension

        import hashlib
        import random
        import re

        words = re.findall(r"\w+", text.lower())
        if not words:
            words = [text.lower()]

        summed = [0.0] * self.dimension
        for word in words:
            hash_val = int(hashlib.sha256(word.encode("utf-8")).hexdigest(), 16)
            rng = random.Random(hash_val)
            for i in range(self.dimension):
                summed[i] += rng.uniform(-1.0, 1.0)

        sum_sq = sum(x * x for x in summed)
        norm = sum_sq**0.5

        if norm > 0:
            return [x / norm for x in summed]
        return summed

    def batch_embedding(self, texts: list[str]) -> list[list[float]]:
        return [self.generate_embedding(text) for text in texts]
