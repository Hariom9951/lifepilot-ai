import json
import logging
import uuid
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

import numpy as np

from app.core.config.settings import settings

logger = logging.getLogger("app.vector.providers")


class BaseVectorStoreProvider(ABC):
    """
    Unified abstract provider interface defining database operations
    for swappable vector storages.
    """

    @abstractmethod
    def add_chunks(
        self,
        user_id: uuid.UUID,
        chunk_ids: list[str],
        embeddings: list[list[float]],
        metadatas: list[dict[str, Any]],
    ) -> None:
        """
        Store multiple vector embedding representations along with custom metadata tags.
        """
        pass

    @abstractmethod
    def search(
        self,
        user_id: uuid.UUID,
        query_vector: list[float],
        limit: int = 5,
        metadata_filter: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """
        Perform semantic similarity match retrieval.
        """
        pass

    @abstractmethod
    def delete_chunks(self, user_id: uuid.UUID, chunk_ids: list[str]) -> None:
        """
        Remove chunk records by their unique IDs.
        """
        pass

    @abstractmethod
    def clear(self, user_id: uuid.UUID) -> None:
        """
        Purges all chunk records belonging to a user owner.
        """
        pass


class ChromaVectorStoreProvider(BaseVectorStoreProvider):
    """
    ChromaDB implementation supporting disk-based isolation per user.
    """

    def __init__(self, persist_directory: str) -> None:
        import chromadb  # Lazy import

        self.client = chromadb.PersistentClient(path=persist_directory)

    def _get_collection(self, user_id: uuid.UUID) -> Any:
        # Collection names must be alphanumeric/dashes/underscores, between 3-63 chars
        collection_name = f"user_{str(user_id).replace('-', '_')}"
        return self.client.get_or_create_collection(name=collection_name)

    def add_chunks(
        self,
        user_id: uuid.UUID,
        chunk_ids: list[str],
        embeddings: list[list[float]],
        metadatas: list[dict[str, Any]],
    ) -> None:
        if not chunk_ids:
            return
        collection = self._get_collection(user_id)
        # Prepare metadata: Chroma expects primitive values (str, int, float, bool)
        processed_metadatas = []
        for meta in metadatas:
            flat_meta = {}
            for k, v in meta.items():
                if isinstance(v, list | dict):
                    flat_meta[k] = json.dumps(v)
                else:
                    flat_meta[k] = v
            processed_metadatas.append(flat_meta)

        # Chroma requires document content parameter. We fallback to empty strings as SQL retains texts.
        documents = [meta.get("text", "") for meta in metadatas]

        collection.add(
            ids=chunk_ids,
            embeddings=embeddings,
            metadatas=processed_metadatas,
            documents=documents,
        )

    def search(
        self,
        user_id: uuid.UUID,
        query_vector: list[float],
        limit: int = 5,
        metadata_filter: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        collection = self._get_collection(user_id)

        # Prepare where filters
        where_clause = None
        if metadata_filter:
            flat_filter = {}
            for k, v in metadata_filter.items():
                if isinstance(v, list | dict):
                    flat_filter[k] = json.dumps(v)
                else:
                    flat_filter[k] = v

            if len(flat_filter) == 1:
                where_clause = flat_filter
            elif len(flat_filter) > 1:
                where_clause = {"$and": [{k: v} for k, v in flat_filter.items()]}

        res = collection.query(
            query_embeddings=[query_vector],
            n_results=limit,
            where=where_clause,
        )

        results = []
        ids = res.get("ids", [[]])[0]
        distances = res.get("distances", [[]])[0]
        metadatas = res.get("metadatas", [[]])[0]

        for chunk_id, dist, meta in zip(ids, distances, metadatas, strict=False):
            # Normalize score (Chroma uses L2 distance by default, we convert to pseudo-similarity)
            # similarity = 1 / (1 + distance)
            score = 1.0 / (1.0 + float(dist))

            # Rehydrate nested metadata fields if needed
            nested_meta = {}
            for k, v in meta.items():
                if isinstance(v, str) and (v.startswith("[") or v.startswith("{")):
                    try:
                        nested_meta[k] = json.loads(v)
                    except ValueError:
                        nested_meta[k] = v
                else:
                    nested_meta[k] = v

            results.append(
                {
                    "chunk_id": chunk_id,
                    "score": score,
                    "metadata": nested_meta,
                    "text": nested_meta.get("text", ""),
                }
            )
        return results

    def delete_chunks(self, user_id: uuid.UUID, chunk_ids: list[str]) -> None:
        if not chunk_ids:
            return
        collection = self._get_collection(user_id)
        collection.delete(ids=chunk_ids)

    def clear(self, user_id: uuid.UUID) -> None:
        collection_name = f"user_{str(user_id).replace('-', '_')}"
        try:
            self.client.delete_collection(name=collection_name)
        except Exception:
            pass


class FAISSVectorStoreProvider(BaseVectorStoreProvider):
    """
    FAISS implementation storing index and metadata details locally on disk.
    """

    INDEX_FILENAME = "index.faiss"
    META_FILENAME = "metadata.json"

    def __init__(self, base_dir: Path, dimension: int = 384) -> None:
        self.base_dir = base_dir
        self.dimension = dimension

    def _get_user_paths(self, user_id: uuid.UUID) -> tuple[Path, Path]:
        user_dir = self.base_dir / "documents" / str(user_id)
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

        index = faiss.IndexFlatIP(
            self.dimension
        )  # Inner Product (Cosine-friendly if vectors are normalized)
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

    def add_chunks(
        self,
        user_id: uuid.UUID,
        chunk_ids: list[str],
        embeddings: list[list[float]],
        metadatas: list[dict[str, Any]],
    ) -> None:
        if not chunk_ids:
            return
        index, meta_list = self._load_index(user_id)

        # L2 normalize embeddings for flat IP (cosine matching)
        norm_vectors = []
        for vec in embeddings:
            arr = np.array(vec, dtype=np.float32)
            norm = np.linalg.norm(arr)
            if norm > 0:
                arr = arr / norm
            norm_vectors.append(arr)

        index.add(np.array(norm_vectors, dtype=np.float32))

        for chunk_id, meta in zip(chunk_ids, metadatas, strict=False):
            meta_list.append({"chunk_id": chunk_id, "metadata": meta})

        self._save_index(user_id, index, meta_list)

    def search(
        self,
        user_id: uuid.UUID,
        query_vector: list[float],
        limit: int = 5,
        metadata_filter: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        import faiss  # Lazy import

        index, meta_list = self._load_index(user_id)
        if index.ntotal == 0:
            return []

        # Normalize query vector
        arr = np.array(query_vector, dtype=np.float32).reshape(1, -1)
        faiss.normalize_L2(arr)

        distances, indices = index.search(arr, min(limit * 2, index.ntotal))

        results = []
        for dist, idx in zip(distances[0], indices[0], strict=False):
            if idx == -1 or idx >= len(meta_list):
                continue
            meta = meta_list[idx]

            # Apply metadata filters manually
            if metadata_filter:
                match = True
                chunk_meta = meta.get("metadata", {})
                for k, v in metadata_filter.items():
                    if chunk_meta.get(k) != v:
                        match = False
                        break
                if not match:
                    continue

            results.append(
                {
                    "chunk_id": meta["chunk_id"],
                    "score": float(dist),
                    "metadata": meta["metadata"],
                    "text": meta["metadata"].get("text", ""),
                }
            )

        # Sort and limit
        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:limit]

    def delete_chunks(self, user_id: uuid.UUID, chunk_ids: list[str]) -> None:
        import faiss  # Lazy import

        index, meta_list = self._load_index(user_id)
        if not meta_list:
            return

        chunk_set = set(chunk_ids)
        keep_indices = [
            i for i, m in enumerate(meta_list) if m["chunk_id"] not in chunk_set
        ]

        if len(keep_indices) == len(meta_list):
            return

        new_index = faiss.IndexFlatIP(self.dimension)
        new_meta = []

        if keep_indices:
            vectors = []
            for idx in keep_indices:
                vec = index.reconstruct(idx)
                vectors.append(vec)
                new_meta.append(meta_list[idx])
            new_index.add(np.array(vectors, dtype=np.float32))

        self._save_index(user_id, new_index, new_meta)

    def clear(self, user_id: uuid.UUID) -> None:
        index_path, meta_path = self._get_user_paths(user_id)
        if index_path.exists():
            index_path.unlink()
        if meta_path.exists():
            meta_path.unlink()


class QdrantVectorStoreProvider(BaseVectorStoreProvider):
    """
    Qdrant implementation allowing remote/local database connections.
    """

    def __init__(self, url: str, dimension: int = 384) -> None:
        from qdrant_client import QdrantClient  # Lazy import

        self.client = (
            QdrantClient(url=url)
            if url.startswith("http")
            else QdrantClient(":memory:")
        )
        self.dimension = dimension

    def _ensure_collection(self, collection_name: str) -> None:
        from qdrant_client.models import Distance, VectorParams  # Lazy import

        if not self.client.collection_exists(collection_name):
            self.client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(
                    size=self.dimension, distance=Distance.COSINE
                ),
            )

    def _get_collection_name(self, user_id: uuid.UUID) -> str:
        return f"user_{str(user_id).replace('-', '_')}"

    def add_chunks(
        self,
        user_id: uuid.UUID,
        chunk_ids: list[str],
        embeddings: list[list[float]],
        metadatas: list[dict[str, Any]],
    ) -> None:
        from qdrant_client.models import PointStruct  # Lazy import

        collection = self._get_collection_name(user_id)
        self._ensure_collection(collection)

        points = []
        for cid, vec, meta in zip(chunk_ids, embeddings, metadatas, strict=False):
            # Qdrant expects points with int/uuid string representation
            points.append(
                PointStruct(
                    id=cid,
                    vector=vec,
                    payload=meta,
                )
            )
        self.client.upsert(collection_name=collection, points=points)

    def search(
        self,
        user_id: uuid.UUID,
        query_vector: list[float],
        limit: int = 5,
        metadata_filter: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        from qdrant_client.models import (  # Lazy import
            FieldCondition,
            Filter,
            MatchValue,
        )

        collection = self._get_collection_name(user_id)
        self._ensure_collection(collection)

        query_filter = None
        if metadata_filter:
            conditions = []
            for k, v in metadata_filter.items():
                conditions.append(FieldCondition(key=k, match=MatchValue(value=v)))
            query_filter = Filter(must=conditions)

        if hasattr(self.client, "search"):
            res = self.client.search(
                collection_name=collection,
                query_vector=query_vector,
                query_filter=query_filter,
                limit=limit,
            )
        else:
            query_res = self.client.query_points(
                collection_name=collection,
                query=query_vector,
                query_filter=query_filter,
                limit=limit,
            )
            res = query_res.points

        return [
            {
                "chunk_id": str(hit.id),
                "score": float(hit.score),
                "metadata": hit.payload or {},
                "text": (hit.payload or {}).get("text", ""),
            }
            for hit in res
        ]

    def delete_chunks(self, user_id: uuid.UUID, chunk_ids: list[str]) -> None:
        from qdrant_client.models import PointIdsList  # Lazy import

        collection = self._get_collection_name(user_id)
        self._ensure_collection(collection)
        self.client.delete(
            collection_name=collection, points_selector=PointIdsList(points=chunk_ids)
        )

    def clear(self, user_id: uuid.UUID) -> None:
        collection = self._get_collection_name(user_id)
        try:
            self.client.delete_collection(collection_name=collection)
        except Exception:
            pass


# -----------------------------------------------------------------------------
# Factory Accessor
# -----------------------------------------------------------------------------

_vector_store_provider: BaseVectorStoreProvider | None = None


def get_vector_store_provider() -> BaseVectorStoreProvider:
    """
    Instantiates the configured swappable vector storage client.
    """
    global _vector_store_provider
    if _vector_store_provider is None:
        provider_name = getattr(settings, "VECTOR_PROVIDER", "chroma").lower()
        if provider_name == "faiss":
            _vector_store_provider = FAISSVectorStoreProvider(
                base_dir=Path(settings.KNOWLEDGE_VECTOR_DIR), dimension=384
            )
        elif provider_name == "qdrant":
            _vector_store_provider = QdrantVectorStoreProvider(
                url=settings.QDRANT_URL, dimension=384
            )
        else:
            _vector_store_provider = ChromaVectorStoreProvider(
                persist_directory=settings.CHROMA_DB_PATH
            )
    return _vector_store_provider


def set_vector_store_provider(provider: BaseVectorStoreProvider | None) -> None:
    global _vector_store_provider
    _vector_store_provider = provider
