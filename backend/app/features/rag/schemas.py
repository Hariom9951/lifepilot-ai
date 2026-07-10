import uuid
from typing import Any

from pydantic import BaseModel, Field


class RAGSearchRequest(BaseModel):
    """Payload to query the RAG search pipeline."""

    query: str = Field(..., description="The query to search the knowledge base for.")
    limit: int = Field(5, ge=1, le=50, description="Top-k matching chunks to retrieve.")
    score_threshold: float = Field(
        0.35, ge=0.0, le=1.0, description="Similarity score threshold filter."
    )
    metadata_filter: dict[str, Any] | None = Field(
        None, description="Key-value filters to restrict vector matches."
    )


class RAGSearchMatch(BaseModel):
    """Represents a single matched chunk result."""

    content: str = Field(..., description="Text content segment of the chunk.")
    score: float = Field(..., description="Similarity confidence score.")
    document: str = Field(
        ..., description="Original filename or memory source identifier."
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Metadata dictionary associated with chunk."
    )


class RAGSearchResponse(BaseModel):
    """The matched results return payload."""

    query: str
    matches: list[RAGSearchMatch]


class RAGIndexRequest(BaseModel):
    """Trigger payload for incremental/complete RAG reindexing."""

    document_ids: list[uuid.UUID] | None = Field(
        None, description="List of specific document IDs to re-index."
    )
    notes: bool = Field(
        True, description="Trigger incremental indexing on stored user memories."
    )
    journals: bool = Field(True, description="Incremental indexing on user journals.")


class RAGIndexResponse(BaseModel):
    """Result of indexing trigger."""

    indexed_count: int
    message: str
