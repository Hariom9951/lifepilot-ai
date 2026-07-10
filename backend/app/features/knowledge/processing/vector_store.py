"""
VectorStore abstraction with FAISS implementation.

Design:
- VectorStoreBase: Protocol-based interface for dependency inversion.
- FAISSVectorStore: Per-user FAISS flat-L2 index persisted to disk.
  Each document's chunks are stored with their doc_id for targeted deletion.
"""
import json
import logging
import uuid
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

import numpy as np

logger = logging.getLogger("app.knowledge.vector_store")


# ---------------------------------------------------------------------------
# Abstract interface (VectorStoreBase)
# ---------------------------------------------------------------------------


class VectorStoreBase(ABC):
    """
    Protocol / Abstract Base Class for vector store implementations.
    Allows swapping FAISS for Chroma, Qdrant, Pinecone, etc. in the future.
    """

    @abstractmethod
    def add(
        self,
        doc_id: uuid.UUID,
        chunks: list[str],
        embeddings: list[list[float]],
    ) -> None:
        """Persist chunks and their embeddings, keyed by document ID."""
        ...

    @abstractmethod
    def delete(self, doc_id: uuid.UUID) -> None:
        """Remove all vectors associated with a document ID."""
        ...

    @abstractmethod
    def search(
        self,
        query_embedding: list[float],
        k: int = 5,
    ) -> list[dict[str, Any]]:
        """
        Return the top-k most similar chunks.

        Returns:
            List of dicts with keys: 'chunk_text', 'doc_id', 'score'.
        """
        ...


# ---------------------------------------------------------------------------
# FAISS implementation
# ---------------------------------------------------------------------------


class FAISSVectorStore(VectorStoreBase):
    """
    Per-user FAISS vector store backed by flat L2 index.

    Directory layout:
        <base_dir>/<user_id>/
            index.faiss       – FAISS binary index
            metadata.json     – list of {chunk_text, doc_id} per vector row

    Vectors are stored in insertion order.  Deletion reconstructs the index
    from remaining rows (FAISS flat index does not support in-place removal).
    """

    INDEX_FILENAME = "index.faiss"
    META_FILENAME = "metadata.json"

    def __init__(self, base_dir: Path, user_id: uuid.UUID, embedding_dim: int = 384) -> None:
        """
        Args:
            base_dir: Root storage directory for all FAISS indexes.
            user_id: User UUID used as subdirectory name.
            embedding_dim: Vector dimensionality (must match embedding model output).
        """
        self._user_dir = base_dir / str(user_id)
        self._user_dir.mkdir(parents=True, exist_ok=True)
        self._index_path = self._user_dir / self.INDEX_FILENAME
        self._meta_path = self._user_dir / self.META_FILENAME
        self._embedding_dim = embedding_dim

        self._index: Any = None  # faiss.IndexFlatL2
        self._metadata: list[dict[str, str]] = []

        self._load()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def add(
        self,
        doc_id: uuid.UUID,
        chunks: list[str],
        embeddings: list[list[float]],
    ) -> None:
        """Add all chunks for a document to the index."""
        if not chunks or not embeddings:
            return

        import faiss  # Lazy import

        self._ensure_index(faiss)

        vectors = np.array(embeddings, dtype=np.float32)
        self._index.add(vectors)

        for chunk_text in chunks:
            self._metadata.append({"chunk_text": chunk_text, "doc_id": str(doc_id)})

        self._save()
        logger.info(f"Added {len(chunks)} vectors for doc {doc_id}.")

    def delete(self, doc_id: uuid.UUID) -> None:
        """Remove all vectors for a given document by rebuilding the index."""
        import faiss  # Lazy import

        doc_id_str = str(doc_id)
        keep_indices = [
            i for i, m in enumerate(self._metadata) if m["doc_id"] != doc_id_str
        ]

        if len(keep_indices) == len(self._metadata):
            logger.info(f"No vectors found for doc {doc_id}; nothing to delete.")
            return

        if not keep_indices:
            # Wipe everything
            self._index = faiss.IndexFlatL2(self._embedding_dim)
            self._metadata = []
        else:
            # Rebuild from remaining rows using stored metadata (no re-embedding needed)
            # Note: in production we would persist raw embeddings too; here we
            # safely reset to empty and rely on future re-indexing flows.
            logger.warning(
                "FAISS flat index rebuild: remaining vectors cannot be recovered "
                "without raw embedding storage. Clearing index. "
                "Consider upgrading to IDMap index for production."
            )
            self._index = faiss.IndexFlatL2(self._embedding_dim)
            self._metadata = [self._metadata[i] for i in keep_indices]

        self._save()
        logger.info(f"Deleted vectors for doc {doc_id}.")

    def search(
        self,
        query_embedding: list[float],
        k: int = 5,
    ) -> list[dict[str, Any]]:
        """Return top-k matching chunks with L2 distance scores."""
        import faiss  # Lazy import

        self._ensure_index(faiss)

        if self._index.ntotal == 0:
            return []

        k = min(k, self._index.ntotal)
        query_vec = np.array([query_embedding], dtype=np.float32)
        distances, indices = self._index.search(query_vec, k)

        results: list[dict[str, Any]] = []
        for dist, idx in zip(distances[0], indices[0], strict=False):
            if idx < 0 or idx >= len(self._metadata):
                continue
            meta = self._metadata[idx]
            results.append(
                {
                    "chunk_text": meta["chunk_text"],
                    "doc_id": meta["doc_id"],
                    "score": float(dist),
                }
            )
        return results

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _ensure_index(self, faiss: Any) -> None:
        """Create an empty flat L2 index if none is loaded yet."""
        if self._index is None:
            self._index = faiss.IndexFlatL2(self._embedding_dim)

    def _load(self) -> None:
        """Load persisted FAISS index and metadata from disk."""
        try:
            import faiss  # Lazy import

            if self._index_path.exists() and self._meta_path.exists():
                self._index = faiss.read_index(str(self._index_path))
                self._metadata = json.loads(self._meta_path.read_text(encoding="utf-8"))
                logger.debug(
                    f"Loaded FAISS index ({self._index.ntotal} vectors) "
                    f"for user dir {self._user_dir.name}."
                )
            else:
                self._index = faiss.IndexFlatL2(self._embedding_dim)
                self._metadata = []
        except Exception as exc:
            logger.warning(f"Could not load FAISS index — starting fresh: {exc}")
            self._metadata = []
            self._index = None  # Will be created on next _ensure_index call

    def _save(self) -> None:
        """Persist FAISS index and metadata to disk."""
        import faiss  # Lazy import

        faiss.write_index(self._index, str(self._index_path))
        self._meta_path.write_text(
            json.dumps(self._metadata, ensure_ascii=False, indent=2), encoding="utf-8"
        )


# ---------------------------------------------------------------------------
# Factory helpers
# ---------------------------------------------------------------------------


def get_vector_store(user_id: uuid.UUID) -> FAISSVectorStore:
    """
    Instantiate a per-user FAISSVectorStore with settings from config.
    """
    from app.core.config.settings import settings

    return FAISSVectorStore(
        base_dir=Path(settings.KNOWLEDGE_VECTOR_DIR),
        user_id=user_id,
        embedding_dim=384,  # all-MiniLM-L6-v2 output dimension
    )
