"""create_knowledge_documents_table

Revision ID: a1b2c3d4e5f6
Revises: b2c762756fab
Create Date: 2026-07-10 10:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: str | Sequence[str] | None = "b2c762756fab"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema — create documents table for knowledge/RAG feature."""
    op.create_table(
        "documents",
        # Primary key (UUID)
        sa.Column("id", sa.Uuid(), nullable=False),
        # Foreign key to users table
        sa.Column("user_id", sa.Uuid(), nullable=False),
        # File metadata
        sa.Column("original_filename", sa.String(length=255), nullable=False),
        sa.Column("storage_filename", sa.String(length=255), nullable=False),
        sa.Column("mime_type", sa.String(length=100), nullable=False),
        sa.Column("file_size", sa.BigInteger(), nullable=False),
        # Processing lifecycle
        sa.Column(
            "status",
            sa.Enum("uploaded", "processing", "ready", "failed", name="documentstatus"),
            server_default="uploaded",
            nullable=False,
        ),
        sa.Column("chunk_count", sa.Integer(), default=0, nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("extracted_text_path", sa.String(length=500), nullable=True),
        sa.Column(
            "processed_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        # Timestamps (from TimestampMixin)
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        # Constraints
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("storage_filename"),
    )
    # Indexes for fast queries
    op.create_index("ix_documents_user_id", "documents", ["user_id"])
    op.create_index("ix_documents_status", "documents", ["status"])


def downgrade() -> None:
    """Downgrade schema — drop documents table and enum."""
    op.drop_index("ix_documents_status", table_name="documents")
    op.drop_index("ix_documents_user_id", table_name="documents")
    op.drop_table("documents")
    # Drop the enum type (PostgreSQL specific)
    sa.Enum(name="documentstatus").drop(op.get_bind(), checkfirst=True)
