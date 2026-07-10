import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.features.rag.embedding import RAGEmbeddingEngine
from app.features.rag.reranker import RAGReranker
from app.features.rag.vector_store import RAGVectorStore


class RAGRetriever:
    """Orchestrates query embedding, similarity matching, and scoring optimization."""

    @classmethod
    async def retrieve(
        cls,
        db: AsyncSession,
        user_id: uuid.UUID,
        query: str,
        limit: int = 5,
        score_threshold: float = 0.35,
        metadata_filter: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """
        Retrieves matching document chunks from the vector database.
        """
        # 1. Embed query text
        embeddings = await RAGEmbeddingEngine.get_embeddings(db, [query])
        query_vector = embeddings[0]

        # 2. Vector search (retrieve double candidates for reranking)
        raw_matches = RAGVectorStore.search(
            user_id=user_id,
            query_vector=query_vector,
            limit=limit * 2,
            metadata_filter=metadata_filter,
        )

        # 3. Format matches
        matches = []
        for hit in raw_matches:
            meta = hit.get("metadata") or {}
            doc_name = (
                meta.get("source")
                or meta.get("original_filename")
                or meta.get("document_id")
                or "unknown"
            )

            text_content = hit.get("text") or meta.get("text") or ""

            matches.append(
                {
                    "content": text_content,
                    "score": hit.get("score") or 0.0,
                    "document": doc_name,
                    "metadata": meta,
                }
            )

        # 4. Filter by score threshold
        filtered_matches = [m for m in matches if m["score"] >= score_threshold]

        # 5. Rerank matches local-first
        reranked_matches = RAGReranker.rerank(query, filtered_matches, top_n=limit)
        return reranked_matches
