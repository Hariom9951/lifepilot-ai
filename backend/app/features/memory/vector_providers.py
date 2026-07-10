import json
import logging
import uuid
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

import numpy as np

logger = logging.getLogger("app.memory.vector_providers")


class BaseVectorProvider(ABC):
    """
    Abstract Base Class for vector database providers.
    """

    @abstractmethod
    def add(
        self,
        user_id: uuid.UUID,
        item_id: uuid.UUID,
        embedding: list[float],
        metadata: dict[str, Any],
    ) -> None:
        """
        Add a single item to the vector database.
        """
        pass

    @abstractmethod
    def search(
        self,
        user_id: uuid.UUID,
        embedding: list[float],
        k: int = 5,
        threshold: float = 0.8,
    ) -> list[dict[str, Any]]:
        """
        Perform vector similarity search.
        """
        pass

    @abstractmethod
    def delete(self, user_id: uuid.UUID, item_id: uuid.UUID) -> None:
        """
        Delete an item from the vector database.
        """
        pass


class FAISSVectorProvider(BaseVectorProvider):
    """
    Concrete Vector Provider using FAISS locally.
    Saves user-specific indexes to <base_dir>/memories/<user_id>/.
    """

    INDEX_FILENAME = "index.faiss"
    META_FILENAME = "metadata.json"

    def __init__(self, base_dir: Path, dimension: int = 384) -> None:
        self.base_dir = base_dir
        self.dimension = dimension

    def _get_user_paths(self, user_id: uuid.UUID) -> tuple[Path, Path]:
        user_dir = self.base_dir / "memories" / str(user_id)
        user_dir.mkdir(parents=True, exist_ok=True)
        return user_dir / self.INDEX_FILENAME, user_dir / self.META_FILENAME

    def _load_index(self, user_id: uuid.UUID) -> tuple[Any, list[dict[str, Any]]]:
        import faiss  # Lazy import

        index_path, meta_path = self._get_user_paths(user_id)
        if index_path.exists() and meta_path.exists():
            try:
                index = faiss.read_index(str(index_path))
                metadata = json.loads(meta_path.read_text(encoding="utf-8"))
                return index, metadata
            except Exception as e:
                logger.error(f"Error loading FAISS index for {user_id}: {e}")

        # Start fresh
        index = faiss.IndexFlatL2(self.dimension)
        return index, []

    def _save_index(
        self, user_id: uuid.UUID, index: Any, metadata: list[dict[str, Any]]
    ) -> None:
        import faiss  # Lazy import

        index_path, meta_path = self._get_user_paths(user_id)
        faiss.write_index(index, str(index_path))
        meta_path.write_text(
            json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    def add(
        self,
        user_id: uuid.UUID,
        item_id: uuid.UUID,
        embedding: list[float],
        metadata: dict[str, Any],
    ) -> None:

        index, metadata_list = self._load_index(user_id)

        # Check if item_id already exists, if so, delete it first
        item_id_str = str(item_id)
        existing_idx = next(
            (i for i, m in enumerate(metadata_list) if m.get("item_id") == item_id_str),
            None,
        )
        if existing_idx is not None:
            self.delete(user_id, item_id)
            index, metadata_list = self._load_index(user_id)

        # Add new embedding
        vectors = np.array([embedding], dtype=np.float32)
        index.add(vectors)
        metadata_list.append({"item_id": item_id_str, "metadata": metadata})

        self._save_index(user_id, index, metadata_list)
        logger.info(f"Vector added to FAISS for user {user_id}, item {item_id}")

    def delete(self, user_id: uuid.UUID, item_id: uuid.UUID) -> None:
        import faiss  # Lazy import

        index, metadata_list = self._load_index(user_id)
        item_id_str = str(item_id)

        keep_indices = [
            i for i, m in enumerate(metadata_list) if m.get("item_id") != item_id_str
        ]
        if len(keep_indices) == len(metadata_list):
            return  # Not found

        # Rebuild index from remaining (memories are typically low volume per user)
        # To rebuild, we extract vectors from original index if possible,
        # but IndexFlatL2 allows self.reconstruct_n or we can just reconstruct them.
        new_index = faiss.IndexFlatL2(self.dimension)
        new_metadata = []

        if keep_indices:
            # Reconstruct remaining vectors
            rem_vectors = []
            for idx in keep_indices:
                vec = index.reconstruct(idx)
                rem_vectors.append(vec)
                new_metadata.append(metadata_list[idx])

            new_index.add(np.array(rem_vectors, dtype=np.float32))

        self._save_index(user_id, new_index, new_metadata)
        logger.info(f"Vector deleted from FAISS for user {user_id}, item {item_id}")

    def search(
        self,
        user_id: uuid.UUID,
        embedding: list[float],
        k: int = 5,
        threshold: float = 0.8,
    ) -> list[dict[str, Any]]:
        index, metadata_list = self._load_index(user_id)

        if index.ntotal == 0:
            return []

        k = min(k, index.ntotal)
        query_vec = np.array([embedding], dtype=np.float32)
        distances, indices = index.search(query_vec, k)

        results = []
        for dist, idx in zip(distances[0], indices[0], strict=False):
            if idx < 0 or idx >= len(metadata_list):
                continue

            # Flat L2 distance is squared L2 distance.
            # Convert to similarity metric. For flat L2, smaller distance = higher similarity.
            # Example conversion: similarity = 1 / (1 + dist) or similar.
            # Let's check against a converted threshold or directly expose distance/similarity.
            similarity = 1.0 / (1.0 + float(dist))
            if similarity >= threshold:
                meta = metadata_list[idx]
                results.append(
                    {
                        "item_id": meta["item_id"],
                        "metadata": meta["metadata"],
                        "score": similarity,
                    }
                )

        return results
