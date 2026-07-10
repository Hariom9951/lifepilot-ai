import logging
import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.features.embeddings.services import EmbeddingEngineService
from app.features.vector.providers import get_vector_store_provider
from app.features.vector.repositories import DocumentChunkRepository

logger = logging.getLogger("app.vector.services")


class HybridRetrievalService:
    """
    Orchestration service combining vector search capabilities with keyword-based BM25 indexes
    to execute hybrid retrievals.
    """

    @classmethod
    async def index_chunk(
        cls,
        db: AsyncSession,
        user_id: uuid.UUID,
        content: str,
        document_id: uuid.UUID | None = None,
        source: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Saves a text chunk, generates vector embeddings, and stores details in both
        relational SQL database and active vector engine.
        """
        chunk_id = uuid.uuid4()

        # 1. Generate Embeddings
        embeddings = await EmbeddingEngineService.generate_embeddings(db, [content])
        vector = embeddings[0]

        # 2. SQL Save
        await DocumentChunkRepository.add_chunk(
            db=db,
            chunk_id=chunk_id,
            user_id=user_id,
            content=content,
            document_id=document_id,
            source=source,
            metadata_json=metadata,
        )

        # 3. Vector Store Save
        vector_provider = get_vector_store_provider()
        payload_metadata = {
            **(metadata or {}),
            "text": content,
            "source": source or "",
            "document_id": str(document_id) if document_id else "",
            "created_at": datetime.now(UTC).isoformat(),
        }
        vector_provider.add_chunks(
            user_id=user_id,
            chunk_ids=[str(chunk_id)],
            embeddings=[vector],
            metadatas=[payload_metadata],
        )

        return {
            "id": str(chunk_id),
            "content": content,
            "document_id": str(document_id) if document_id else None,
            "source": source,
            "metadata": metadata,
        }

    @classmethod
    async def batch_index_chunks(
        cls,
        db: AsyncSession,
        user_id: uuid.UUID,
        chunks: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """
        Indexes multiple text chunks simultaneously to optimize database transaction overhead.
        """
        if not chunks:
            return []

        # Prepare ids and texts
        processed_chunks = []
        texts = []
        for chunk in chunks:
            cid = chunk.get("id") or str(uuid.uuid4())
            texts.append(chunk["content"])
            processed_chunks.append(
                {
                    "id": uuid.UUID(cid) if isinstance(cid, str) else cid,
                    "content": chunk["content"],
                    "document_id": chunk.get("document_id"),
                    "source": chunk.get("source"),
                    "metadata": chunk.get("metadata") or {},
                }
            )

        # 1. Generate Embeddings in batch
        embeddings = await EmbeddingEngineService.generate_embeddings(db, texts)

        # 2. Batch Save SQL
        await DocumentChunkRepository.batch_add_chunks(db, user_id, processed_chunks)

        # 3. Batch Save Vector Store
        chunk_ids = [str(c["id"]) for c in processed_chunks]
        payloads = []
        for c in processed_chunks:
            meta = {
                **c["metadata"],
                "text": c["content"],
                "source": c["source"] or "",
                "document_id": str(c["document_id"]) if c["document_id"] else "",
                "created_at": datetime.now(UTC).isoformat(),
            }
            payloads.append(meta)

        vector_provider = get_vector_store_provider()
        vector_provider.add_chunks(
            user_id=user_id,
            chunk_ids=chunk_ids,
            embeddings=embeddings,
            metadatas=payloads,
        )

        return [
            {
                "id": str(c["id"]),
                "content": c["content"],
                "document_id": str(c["document_id"]) if c["document_id"] else None,
                "source": c["source"],
                "metadata": c["metadata"],
            }
            for c in processed_chunks
        ]

    @classmethod
    async def delete_chunk(
        cls, db: AsyncSession, user_id: uuid.UUID, chunk_id: uuid.UUID
    ) -> bool:
        """
        Deletes a single chunk from SQL and vector database.
        """
        deleted_sql = await DocumentChunkRepository.delete_chunk(db, chunk_id)

        vector_provider = get_vector_store_provider()
        vector_provider.delete_chunks(user_id, [str(chunk_id)])

        return deleted_sql

    @classmethod
    async def delete_by_document(
        cls, db: AsyncSession, user_id: uuid.UUID, document_id: uuid.UUID
    ) -> int:
        """
        Deletes all chunks belonging to a document ID from SQL and vector databases.
        """
        # Fetch chunk IDs to delete from vector store
        chunks = await DocumentChunkRepository.get_user_chunks(
            db, user_id, {"document_id": str(document_id)}
        )
        cids = [str(c.id) for c in chunks]

        # SQL Delete
        count = await DocumentChunkRepository.delete_by_document(db, document_id)

        # Vector Store Delete
        if cids:
            vector_provider = get_vector_store_provider()
            vector_provider.delete_chunks(user_id, cids)

        return count

    @classmethod
    async def rebuild_index(cls, db: AsyncSession, user_id: uuid.UUID) -> int:
        """
        Truncates the vector index for a user and re-populates it from SQL.
        """
        # Clear vector index
        vector_provider = get_vector_store_provider()
        vector_provider.clear(user_id)

        # Fetch all SQL records
        chunks = await DocumentChunkRepository.get_user_chunks(db, user_id)
        if not chunks:
            return 0

        # Batch indexing into vector store
        texts = [c.content for c in chunks]
        embeddings = await EmbeddingEngineService.generate_embeddings(db, texts)

        chunk_ids = [str(c.id) for c in chunks]
        metadatas = []
        for c in chunks:
            meta = {
                **(c.metadata_json or {}),
                "text": c.content,
                "source": c.source or "",
                "document_id": str(c.document_id) if c.document_id else "",
                "created_at": (
                    c.created_at.isoformat()
                    if c.created_at
                    else datetime.now(UTC).isoformat()
                ),
            }
            metadatas.append(meta)

        vector_provider.add_chunks(
            user_id=user_id,
            chunk_ids=chunk_ids,
            embeddings=embeddings,
            metadatas=metadatas,
        )

        return len(chunks)

    # -------------------------------------------------------------------------
    # Hybrid Retrieval Score Fusion
    # -------------------------------------------------------------------------

    @classmethod
    async def hybrid_search(
        cls,
        db: AsyncSession,
        user_id: uuid.UUID,
        query: str,
        limit: int = 5,
        semantic_weight: float = 0.7,
        keyword_weight: float = 0.3,
        metadata_filter: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """
        Retrieves candidates using semantic vector queries and keyword BM25 queries,
        computes fused normalized scores, and sorts the top-K responses.
        """
        # Step 1: Semantic Vector Search
        query_embeddings = await EmbeddingEngineService.generate_embeddings(db, [query])
        query_vector = query_embeddings[0]

        vector_provider = get_vector_store_provider()
        vector_hits = vector_provider.search(
            user_id=user_id,
            query_vector=query_vector,
            limit=limit * 2,
            metadata_filter=metadata_filter,
        )

        # Step 2: Fetch SQL chunks for Keyword BM25 calculations
        sql_chunks = await DocumentChunkRepository.get_user_chunks(
            db, user_id, metadata_filter
        )

        bm25_scores = {}
        if sql_chunks:
            from rank_bm25 import BM25Okapi  # Lazy import

            # Simple whitespace tokenization
            corpus = [doc.content.lower().split() for doc in sql_chunks]
            bm25 = BM25Okapi(corpus)

            tokenized_query = query.lower().split()
            scores = bm25.get_scores(tokenized_query)

            # Normalize BM25 scores between [0.0, 1.0]
            max_score = max(scores) if len(scores) > 0 else 0.0
            min_score = min(scores) if len(scores) > 0 else 0.0
            range_score = max_score - min_score

            for doc, score in zip(sql_chunks, scores, strict=False):
                normalized = (
                    (score - min_score) / range_score
                    if range_score > 0
                    else (1.0 if score > 0 else 0.0)
                )
                bm25_scores[str(doc.id)] = {"score": normalized, "chunk": doc}

        # Step 3: Fused scoring matching
        all_candidate_ids = set(bm25_scores.keys()) | {
            hit["chunk_id"] for hit in vector_hits
        }

        fused_results = []
        for cid in all_candidate_ids:
            # Semantic contribution
            vector_hit = next((h for h in vector_hits if h["chunk_id"] == cid), None)
            sem_score = vector_hit["score"] if vector_hit else 0.0

            # BM25 contribution
            bm25_hit = bm25_scores.get(cid)
            key_score = bm25_hit["score"] if bm25_hit else 0.0

            # Weighted sum fusion
            fused_score = (semantic_weight * sem_score) + (keyword_weight * key_score)

            # Metadata extraction
            if vector_hit:
                metadata = vector_hit["metadata"]
                content = vector_hit["text"]
            else:
                db_chunk = bm25_hit["chunk"]
                metadata = db_chunk.metadata_json or {}
                content = db_chunk.content

            fused_results.append(
                {
                    "chunk_id": cid,
                    "score": fused_score,
                    "content": content,
                    "metadata": metadata,
                }
            )

        # Step 4: Sort and limit
        fused_results.sort(key=lambda x: x["score"], reverse=True)
        return fused_results[:limit]
