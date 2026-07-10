import logging
import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.features.knowledge.models import Document
from app.features.rag.ingestion import RAGIngestionService
from app.features.rag.repository import RAGRepository
from app.features.rag.retriever import RAGRetriever
from app.features.rag.vector_store import RAGVectorStore

logger = logging.getLogger("app.rag.services")


class RAGService:
    """Core RAG service coordinating indexing workflows and similarity retrieval queries."""

    @classmethod
    async def search_knowledge_base(
        cls,
        db: AsyncSession,
        user_id: uuid.UUID,
        query: str,
        limit: int = 5,
        score_threshold: float = 0.35,
        metadata_filter: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """Query RAG context matches across user notes, journals, and files."""
        return await RAGRetriever.retrieve(
            db=db,
            user_id=user_id,
            query=query,
            limit=limit,
            score_threshold=score_threshold,
            metadata_filter=metadata_filter,
        )

    @classmethod
    async def index_user_knowledge(
        cls,
        db: AsyncSession,
        user_id: uuid.UUID,
        document_ids: list[uuid.UUID] | None = None,
        index_notes: bool = True,
        index_journals: bool = True,
    ) -> int:
        """Trigger incremental indexing on user documents and memory structures."""
        total_indexed = 0

        # Incremental notes/journals ingestion
        if index_notes or index_journals:
            memory_count = await RAGIngestionService.ingest_user_memories(db, user_id)
            total_indexed += memory_count

        # Incremental document ingestion
        if document_ids:
            for doc_id in document_ids:
                doc_count = await RAGIngestionService.ingest_document(
                    db, user_id, doc_id
                )
                total_indexed += doc_count
        else:
            stmt = select(Document).where(Document.user_id == user_id)
            res = await db.execute(stmt)
            docs = res.scalars().all()
            for doc in docs:
                if doc.chunk_count == 0 or doc.status == "uploaded":
                    doc_count = await RAGIngestionService.ingest_document(
                        db, user_id, doc.id
                    )
                    total_indexed += doc_count

        return total_indexed

    @classmethod
    async def reindex_all_user_knowledge(
        cls, db: AsyncSession, user_id: uuid.UUID
    ) -> int:
        """Re-indexes the entire vector engine by clearing local databases and parsing everything."""
        # 1. Clear database representation of chunks
        await RAGRepository.clear_all_chunks(db, user_id)

        # 2. Clear vector store
        RAGVectorStore.clear(user_id)

        # 3. Index everything from scratch
        total_indexed = 0

        memory_count = await RAGIngestionService.ingest_user_memories(db, user_id)
        total_indexed += memory_count

        stmt = select(Document).where(Document.user_id == user_id)
        res = await db.execute(stmt)
        docs = res.scalars().all()
        for doc in docs:
            doc_count = await RAGIngestionService.ingest_document(db, user_id, doc.id)
            total_indexed += doc_count

        logger.info(
            f"Full reindex complete for user {user_id}. Total chunks: {total_indexed}"
        )
        return total_indexed
