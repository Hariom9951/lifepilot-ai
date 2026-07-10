import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.features.knowledge.models import DocumentStatus


class DocumentResponse(BaseModel):
    """
    Full document metadata returned in API responses.
    """

    id: uuid.UUID
    user_id: uuid.UUID
    original_filename: str
    mime_type: str
    file_size: int
    status: DocumentStatus
    chunk_count: int
    error_message: str | None = None
    processed_at: datetime | None = None
    retry_count: int
    retries_exhausted: bool
    metadata_json: dict | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class DocumentStatusResponse(BaseModel):
    """
    Minimal status-only schema for polling.
    """

    id: uuid.UUID
    original_filename: str
    status: DocumentStatus
    chunk_count: int
    error_message: str | None = None
    processed_at: datetime | None = None

    model_config = {"from_attributes": True}


class DocumentListResponse(BaseModel):
    """
    Paginated document list metadata.
    """

    total: int = Field(default=0)
    items: list[DocumentResponse] = Field(default_factory=list)


class DocumentSearchRequest(BaseModel):
    query: str = Field(..., min_length=1)
    limit: int = Field(5, ge=1, le=50)
    similarity_threshold: float = Field(0.5, ge=0.0, le=1.0)
    category: str | None = None
    metadata_filter: dict | None = None


class DocumentSearchItem(BaseModel):
    document_id: uuid.UUID
    chunk_text: str
    score: float
    metadata: dict


class DocumentSearchResponse(BaseModel):
    results: list[DocumentSearchItem]
