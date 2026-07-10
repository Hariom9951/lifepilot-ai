
from sqlalchemy import JSON, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database.mixins import Base, TimestampMixin, UUIDMixin


class EmbeddingCache(Base, UUIDMixin, TimestampMixin):
    """
    SQLAlchemy model to cache computed embedding vectors.
    """

    __tablename__ = "embedding_caches"

    text_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    model_name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    embedding: Mapped[list[float]] = mapped_column(JSON, nullable=False)

    __table_args__ = (
        UniqueConstraint(
            "text_hash", "model_name", name="uq_embedding_caches_hash_model"
        ),
    )
