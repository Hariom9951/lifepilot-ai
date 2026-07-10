import uuid

from sqlalchemy import and_, delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.features.knowledge.models import Document
from app.features.vector.models import VectorDocumentChunk


class RAGRepository:
    """Handles core database operations and fetches for RAG elements."""

    @classmethod
    async def get_indexed_documents(
        cls, db: AsyncSession, user_id: uuid.UUID
    ) -> list[Document]:
        """Fetch all stored document metadata records for a user."""
        stmt = select(Document).where(Document.user_id == user_id)
        res = await db.execute(stmt)
        return list(res.scalars().all())

    @classmethod
    async def delete_chunk_by_id(
        cls, db: AsyncSession, user_id: uuid.UUID, chunk_id: uuid.UUID
    ) -> bool:
        """Deletes a single vector chunk by ID and user owner constraint."""
        stmt = delete(VectorDocumentChunk).where(
            and_(
                VectorDocumentChunk.id == chunk_id,
                VectorDocumentChunk.user_id == user_id,
            )
        )
        res = await db.execute(stmt)
        await db.flush()
        return res.rowcount > 0

    @classmethod
    async def clear_all_chunks(cls, db: AsyncSession, user_id: uuid.UUID) -> int:
        """Purge all text chunk databases for a user."""
        stmt = delete(VectorDocumentChunk).where(VectorDocumentChunk.user_id == user_id)
        res = await db.execute(stmt)
        await db.flush()
        return res.rowcount
