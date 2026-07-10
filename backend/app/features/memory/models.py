import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    String,
    Table,
    Text,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database.mixins import Base, TimestampMixin, UUIDMixin

# Many-to-many association table for Memories and Tags
memory_tag_association = Table(
    "memory_tag_association",
    Base.metadata,
    Column(
        "memory_id",
        Uuid,
        ForeignKey("users_memories.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "tag_id",
        Uuid,
        ForeignKey("memory_tags.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)


class MemoryCategory(Base, UUIDMixin, TimestampMixin):
    """
    SQLAlchemy model for memory categories.
    """

    __tablename__ = "memory_categories"

    user_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)

    # Relationships
    memories: Mapped[list["UserMemory"]] = relationship(
        "UserMemory", back_populates="category", cascade="all, delete-orphan"
    )


class MemoryTag(Base, UUIDMixin, TimestampMixin):
    """
    SQLAlchemy model for memory tags.
    """

    __tablename__ = "memory_tags"

    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)

    # Relationships
    memories: Mapped[list["UserMemory"]] = relationship(
        "UserMemory", secondary=memory_tag_association, back_populates="tags"
    )


class UserMemory(Base, UUIDMixin, TimestampMixin):
    """
    SQLAlchemy model for user-specific long-term memories.
    """

    __tablename__ = "users_memories"

    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    importance_score: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    category_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("memory_categories.id", ondelete="SET NULL"), nullable=True
    )
    is_archived: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Relationships
    category: Mapped[MemoryCategory | None] = relationship(
        "MemoryCategory", back_populates="memories"
    )
    tags: Mapped[list[MemoryTag]] = relationship(
        "MemoryTag", secondary=memory_tag_association, back_populates="memories"
    )


class ConversationSession(Base, UUIDMixin, TimestampMixin):
    """
    SQLAlchemy model for conversation sessions (short-term memory).
    """

    __tablename__ = "conversation_sessions"

    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relationships
    messages: Mapped[list["ConversationMessage"]] = relationship(
        "ConversationMessage", back_populates="session", cascade="all, delete-orphan"
    )
    summaries: Mapped[list["ConversationSummary"]] = relationship(
        "ConversationSummary", back_populates="session", cascade="all, delete-orphan"
    )


class ConversationMessage(Base, UUIDMixin, TimestampMixin):
    """
    SQLAlchemy model for conversation messages.
    """

    __tablename__ = "conversation_messages"

    session_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("conversation_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    role: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # system, user, assistant
    content: Mapped[str] = mapped_column(Text, nullable=False)

    # Relationships
    session: Mapped[ConversationSession] = relationship(
        "ConversationSession", back_populates="messages"
    )


class ConversationSummary(Base, UUIDMixin, TimestampMixin):
    """
    SQLAlchemy model for conversation summaries.
    """

    __tablename__ = "conversation_summaries"

    session_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("conversation_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    summary: Mapped[str] = mapped_column(Text, nullable=False)

    # Relationships
    session: Mapped[ConversationSession] = relationship(
        "ConversationSession", back_populates="summaries"
    )
