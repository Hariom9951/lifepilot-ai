import logging
import uuid
from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config.settings import settings
from app.features.knowledge.models import Document, DocumentStatus
from app.features.knowledge.processing.extractors import text_extractor
from app.features.knowledge.processing.storage import LocalStorageProvider
from app.features.memory.models import UserMemory
from app.features.rag.chunking import RAGChunker
from app.features.rag.embedding import RAGEmbeddingEngine
from app.features.rag.vector_store import RAGVectorStore
from app.features.vector.repositories import DocumentChunkRepository

logger = logging.getLogger("app.rag.ingestion")


class RAGIngestionService:
    """Orchestrates parsing, chunking, embedding, and storing files/notes."""

    @classmethod
    async def ingest_document(
        cls, db: AsyncSession, user_id: uuid.UUID, doc_id: uuid.UUID
    ) -> int:
        """
        Parses, chunks, embeds, and saves an uploaded knowledge document.
        """
        doc_stmt = select(Document).where(
            and_(Document.id == doc_id, Document.user_id == user_id)
        )
        res = await db.execute(doc_stmt)
        doc = res.scalar_one_or_none()
        if not doc:
            logger.error(f"Document {doc_id} not found for RAG ingestion.")
            return 0

        doc.status = DocumentStatus.PROCESSING
        await db.commit()

        temp_dir = Path("./storage/tmp")
        temp_dir.mkdir(parents=True, exist_ok=True)
        temp_path = temp_dir / doc.storage_filename

        try:
            storage = LocalStorageProvider()
            file_bytes = storage.load_file(doc.storage_filename)
            temp_path.write_bytes(file_bytes)

            text, meta = text_extractor.extract_with_metadata(temp_path, doc.mime_type)

            if temp_path.exists():
                temp_path.unlink()

            await cls.delete_document_chunks(db, user_id, doc_id)

            chunk_size = getattr(settings, "KNOWLEDGE_CHUNK_SIZE", 512)
            chunk_overlap = getattr(settings, "KNOWLEDGE_CHUNK_OVERLAP", 64)
            chunks = RAGChunker.chunk_document(
                text=text,
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
                source=doc.original_filename,
                document_id=doc_id,
                metadata={
                    "original_filename": doc.original_filename,
                    "mime_type": doc.mime_type,
                    **(meta or {}),
                },
                timestamp=doc.created_at,
            )

            if not chunks:
                doc.status = DocumentStatus.READY
                await db.commit()
                return 0

            texts = [c["content"] for c in chunks]
            embeddings = await RAGEmbeddingEngine.get_embeddings(db, texts)

            processed_chunks = []
            chunk_ids = []
            metadatas = []

            for chunk, _ in zip(chunks, embeddings, strict=False):
                processed_chunks.append(
                    {
                        "id": chunk["id"],
                        "content": chunk["content"],
                        "document_id": doc_id,
                        "source": chunk["source"],
                        "metadata": chunk["metadata"],
                    }
                )
                chunk_ids.append(str(chunk["id"]))
                metadatas.append({**chunk["metadata"], "text": chunk["content"]})

            await DocumentChunkRepository.batch_add_chunks(
                db, user_id, processed_chunks
            )
            RAGVectorStore.add_chunks(user_id, chunk_ids, embeddings, metadatas)

            doc.status = DocumentStatus.READY
            doc.chunk_count = len(chunks)
            doc.processed_at = datetime.now(UTC)
            await db.commit()

            logger.info(f"Ingested document {doc.original_filename} successfully.")
            return len(chunks)

        except Exception as e:
            logger.exception(f"Failed to ingest document {doc_id}: {e}")
            if temp_path.exists():
                temp_path.unlink()
            doc.status = DocumentStatus.FAILED
            doc.error_message = str(e)
            await db.commit()
            return 0

    @classmethod
    async def ingest_user_memories(cls, db: AsyncSession, user_id: uuid.UUID) -> int:
        """
        Retrieves user memory notes and performs incremental indexing.
        """
        mem_stmt = select(UserMemory).where(
            and_(UserMemory.user_id == user_id, UserMemory.is_archived.is_(False))
        )
        res = await db.execute(mem_stmt)
        memories = res.scalars().all()

        all_chunks = await DocumentChunkRepository.get_user_chunks(db, user_id)
        indexed_memory_ids = set()
        for chunk in all_chunks:
            meta = chunk.metadata_json or {}
            if "memory_id" in meta:
                indexed_memory_ids.add(meta["memory_id"])

        new_memories = [m for m in memories if str(m.id) not in indexed_memory_ids]
        if not new_memories:
            return 0

        chunk_size = getattr(settings, "KNOWLEDGE_CHUNK_SIZE", 512)
        chunk_overlap = getattr(settings, "KNOWLEDGE_CHUNK_OVERLAP", 64)
        indexed_count = 0

        for memory in new_memories:
            source_tag = "memory"
            category_name = "Note"
            if memory.category:
                category_name = memory.category.name

            chunks = RAGChunker.chunk_document(
                text=memory.content,
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
                source=source_tag,
                document_id=None,
                metadata={
                    "memory_id": str(memory.id),
                    "category": category_name,
                    "importance_score": memory.importance_score,
                },
                timestamp=memory.created_at,
            )

            if not chunks:
                continue

            texts = [c["content"] for c in chunks]
            embeddings = await RAGEmbeddingEngine.get_embeddings(db, texts)

            processed_chunks = []
            chunk_ids = []
            metadatas = []

            for chunk, _ in zip(chunks, embeddings, strict=False):
                processed_chunks.append(
                    {
                        "id": chunk["id"],
                        "content": chunk["content"],
                        "document_id": None,
                        "source": chunk["source"],
                        "metadata": chunk["metadata"],
                    }
                )
                chunk_ids.append(str(chunk["id"]))
                metadatas.append({**chunk["metadata"], "text": chunk["content"]})

            await DocumentChunkRepository.batch_add_chunks(
                db, user_id, processed_chunks
            )
            RAGVectorStore.add_chunks(user_id, chunk_ids, embeddings, metadatas)
            indexed_count += len(chunks)

        await db.commit()
        return indexed_count

    @classmethod
    async def delete_document_chunks(
        cls, db: AsyncSession, user_id: uuid.UUID, doc_id: uuid.UUID
    ) -> None:
        """
        Remove SQL and Vector Store representations of a document's chunks.
        """
        chunks = await DocumentChunkRepository.get_user_chunks(
            db, user_id, {"document_id": str(doc_id)}
        )
        chunk_ids = [str(c.id) for c in chunks]

        await DocumentChunkRepository.delete_by_document(db, doc_id)

        if chunk_ids:
            RAGVectorStore.delete_chunks(user_id, chunk_ids)
