import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.features.knowledge.models import Document, DocumentStatus


class DocumentRepository:
    """
    Asynchronous Repository for Document entities.
    All methods are static to align with the project's repository pattern.
    """

    @staticmethod
    async def create(db: AsyncSession, document_data: dict[str, Any]) -> Document:
        """Persist a new Document record and return it."""
        doc = Document(**document_data)
        db.add(doc)
        await db.flush()
        return doc

    @staticmethod
    async def get_by_id(db: AsyncSession, doc_id: uuid.UUID) -> Document | None:
        """Fetch a document by primary key without ownership check."""
        stmt = select(Document).where(Document.id == doc_id)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_id_and_user(
        db: AsyncSession, doc_id: uuid.UUID, user_id: uuid.UUID
    ) -> Document | None:
        """Fetch a document ensuring it belongs to the requesting user."""
        stmt = select(Document).where(
            Document.id == doc_id, Document.user_id == user_id
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def list_by_user(db: AsyncSession, user_id: uuid.UUID) -> list[Document]:
        """Return all documents for a user ordered by creation date descending."""
        stmt = (
            select(Document)
            .where(Document.user_id == user_id)
            .order_by(Document.created_at.desc())
        )
        result = await db.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def count_by_user(db: AsyncSession, user_id: uuid.UUID) -> int:
        """Return total document count for a user."""
        stmt = (
            select(func.count())
            .select_from(Document)
            .where(Document.user_id == user_id)
        )
        result = await db.execute(stmt)
        return result.scalar_one()

    @staticmethod
    async def update_status(
        db: AsyncSession,
        doc_id: uuid.UUID,
        status: DocumentStatus,
        chunk_count: int = 0,
        error_message: str | None = None,
        processed_at: datetime | None = None,
    ) -> None:
        """Update document processing status and related fields atomically."""
        values: dict[str, Any] = {"status": status}
        if chunk_count:
            values["chunk_count"] = chunk_count
        if error_message is not None:
            values["error_message"] = error_message
        if processed_at is not None:
            values["processed_at"] = processed_at

        stmt = update(Document).where(Document.id == doc_id).values(**values)
        await db.execute(stmt)
        await db.flush()

    @staticmethod
    async def delete(db: AsyncSession, doc_id: uuid.UUID) -> None:
        """Hard-delete a document record by primary key."""
        stmt = delete(Document).where(Document.id == doc_id)
        await db.execute(stmt)
        await db.flush()

    @staticmethod
    async def mark_processing(db: AsyncSession, doc_id: uuid.UUID) -> None:
        """Convenience method to set status to PROCESSING."""
        stmt = (
            update(Document)
            .where(Document.id == doc_id)
            .values(status=DocumentStatus.PROCESSING)
        )
        await db.execute(stmt)
        await db.flush()

    @staticmethod
    async def mark_failed(
        db: AsyncSession, doc_id: uuid.UUID, error_message: str
    ) -> None:
        """Convenience method to set status to FAILED with an error message."""
        stmt = (
            update(Document)
            .where(Document.id == doc_id)
            .values(
                status=DocumentStatus.FAILED,
                error_message=error_message,
                processed_at=datetime.now(UTC),
            )
        )
        await db.execute(stmt)
        await db.flush()

    @staticmethod
    async def mark_ready(db: AsyncSession, doc_id: uuid.UUID, chunk_count: int) -> None:
        """Convenience method to set status to READY with chunk count."""
        stmt = (
            update(Document)
            .where(Document.id == doc_id)
            .values(
                status=DocumentStatus.READY,
                chunk_count=chunk_count,
                processed_at=datetime.now(UTC),
            )
        )
        await db.execute(stmt)
        await db.flush()
