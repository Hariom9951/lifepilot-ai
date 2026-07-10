"""Assistant feature models for chat history persistence in PostgreSQL."""

import uuid

from sqlalchemy import JSON, ForeignKey, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database.mixins import Base, TimestampMixin, UUIDMixin


class AssistantChat(Base, UUIDMixin, TimestampMixin):
    """
    SQLAlchemy model representing a message exchange in the AI Assistant.
    Each record persists a single query-response pair grouped by conversation_id.
    """

    __tablename__ = "assistant_chats"

    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    conversation_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        nullable=False,
        index=True,
    )
    user_message: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    assistant_message: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    # Stored as a list of recommendation strings for UI cards
    recommendations: Mapped[list[str]] = mapped_column(
        JSON,
        default=list,
        server_default="[]",
        nullable=False,
    )
    # Stored as a list of action items: [{"type": "task", "label": "Start project", "payload": {}}]
    actions: Mapped[list[dict]] = mapped_column(
        JSON,
        default=list,
        server_default="[]",
        nullable=False,
    )

    # Lazy loaded relationship back to User
    user: Mapped["User"] = relationship(  # type: ignore[name-defined] # noqa: F821
        "User",
        back_populates=None,
        lazy="noload",
    )
