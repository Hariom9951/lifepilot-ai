import uuid

from sqlalchemy import JSON, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database.mixins import Base, TimestampMixin, UUIDMixin


class VectorDocumentChunk(Base, UUIDMixin, TimestampMixin):
    """
    SQLAlchemy model to persist document chunks, user owners,
    sources, and metadata attributes for hybrid keyword searches.
    """

    __tablename__ = "vector_document_chunks"

    document_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("documents.id", ondelete="CASCADE"), nullable=True, index=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    source: Mapped[str | None] = mapped_column(String(255), nullable=True)

    metadata_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
