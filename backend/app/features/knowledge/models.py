import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    BigInteger,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database.mixins import Base, TimestampMixin, UUIDMixin


class DocumentStatus(str, enum.Enum):
    """
    Lifecycle states for an uploaded knowledge document.
    """

    UPLOADED = "uploaded"
    PROCESSING = "processing"
    READY = "ready"
    FAILED = "failed"


class Document(Base, UUIDMixin, TimestampMixin):
    """
    SQLAlchemy model for user-uploaded knowledge documents.
    """

    __tablename__ = "documents"

    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    storage_filename: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    file_size: Mapped[int] = mapped_column(BigInteger, nullable=False)
    status: Mapped[DocumentStatus] = mapped_column(
        Enum(DocumentStatus),
        default=DocumentStatus.UPLOADED,
        server_default=DocumentStatus.UPLOADED.value,
        nullable=False,
        index=True,
    )
    chunk_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    extracted_text_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    processed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relationships (lazy to avoid circular import issues)
    user: Mapped["User"] = relationship(  # type: ignore[name-defined]  # noqa: F821
        "User", back_populates=None, lazy="noload"
    )
