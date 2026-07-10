import uuid
from typing import Any

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.features.vector.models import VectorDocumentChunk


class DocumentChunkRepository:
    """
    SQL persistence repository managing CRUD operations for
    relational representation of document chunks in PostgreSQL.
    """

    @classmethod
    async def add_chunk(
        self,
        db: AsyncSession,
        chunk_id: uuid.UUID,
        user_id: uuid.UUID,
        content: str,
        document_id: uuid.UUID | None = None,
        source: str | None = None,
        metadata_json: dict[str, Any] | None = None,
    ) -> VectorDocumentChunk:
        """
        Saves a single document chunk record.
        """
        db_chunk = VectorDocumentChunk(
            id=chunk_id,
            document_id=document_id,
            user_id=user_id,
            content=content,
            source=source,
            metadata_json=metadata_json or {},
        )
        db.add(db_chunk)
        await db.flush()
        return db_chunk

    @classmethod
    async def batch_add_chunks(
        self,
        db: AsyncSession,
        user_id: uuid.UUID,
        chunks: list[dict[str, Any]],
    ) -> list[VectorDocumentChunk]:
        """
        Saves multiple document chunk records in a single database transaction.
        """
        db_chunks = []
        for chunk in chunks:
            chunk_id = chunk.get("id") or uuid.uuid4()
            db_chunk = VectorDocumentChunk(
                id=chunk_id,
                document_id=chunk.get("document_id"),
                user_id=user_id,
                content=chunk["content"],
                source=chunk.get("source"),
                metadata_json=chunk.get("metadata") or {},
            )
            db.add(db_chunk)
            db_chunks.append(db_chunk)
        await db.flush()
        return db_chunks

    @classmethod
    async def get_chunk(
        cls, db: AsyncSession, chunk_id: uuid.UUID
    ) -> VectorDocumentChunk | None:
        """
        Retrieves a single chunk by ID.
        """
        stmt = select(VectorDocumentChunk).where(VectorDocumentChunk.id == chunk_id)
        res = await db.execute(stmt)
        return res.scalar_one_or_none()

    @classmethod
    async def get_user_chunks(
        cls,
        db: AsyncSession,
        user_id: uuid.UUID,
        metadata_filter: dict[str, Any] | None = None,
    ) -> list[VectorDocumentChunk]:
        """
        Fetches all text chunk database records matching optional metadata filters.
        Used for BM25 calculation constraints.
        """
        stmt = select(VectorDocumentChunk).where(VectorDocumentChunk.user_id == user_id)
        res = await db.execute(stmt)
        all_chunks = res.scalars().all()

        if not metadata_filter:
            return list(all_chunks)

        filtered_chunks = []
        for chunk in all_chunks:
            meta = chunk.metadata_json or {}
            match = True
            for k, v in metadata_filter.items():
                # Allow partial list matches or exact value checks
                if meta.get(k) != v:
                    match = False
                    break
            if match:
                filtered_chunks.append(chunk)

        return filtered_chunks

    @classmethod
    async def delete_chunk(cls, db: AsyncSession, chunk_id: uuid.UUID) -> bool:
        """
        Deletes a single document chunk.
        """
        stmt = delete(VectorDocumentChunk).where(VectorDocumentChunk.id == chunk_id)
        res = await db.execute(stmt)
        await db.flush()
        return res.rowcount > 0

    @classmethod
    async def delete_by_document(cls, db: AsyncSession, document_id: uuid.UUID) -> int:
        """
        Deletes all chunks belonging to a document ID.
        """
        stmt = delete(VectorDocumentChunk).where(
            VectorDocumentChunk.document_id == document_id
        )
        res = await db.execute(stmt)
        await db.flush()
        return res.rowcount

    @classmethod
    async def clear_user_chunks(cls, db: AsyncSession, user_id: uuid.UUID) -> int:
        """
        Clears all chunks belonging to a user owner.
        """
        stmt = delete(VectorDocumentChunk).where(VectorDocumentChunk.user_id == user_id)
        res = await db.execute(stmt)
        await db.flush()
        return res.rowcount
