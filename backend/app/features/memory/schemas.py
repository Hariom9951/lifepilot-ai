import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class MemoryCategoryResponse(BaseModel):
    id: uuid.UUID
    name: str

    class Config:
        from_attributes = True


class MemoryTagResponse(BaseModel):
    id: uuid.UUID
    name: str

    class Config:
        from_attributes = True


class MemoryResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    content: str
    importance_score: float
    is_archived: bool
    category: MemoryCategoryResponse | None = None
    tags: list[MemoryTagResponse] = []
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class MemoryCreate(BaseModel):
    content: str = Field(..., min_length=1, description="Memory raw content text")
    category_name: str | None = Field(
        None, max_length=100, description="Memory category name"
    )
    tags: list[str] = Field(
        default_factory=list, description="List of memory tag strings"
    )


class MemoryUpdate(BaseModel):
    content: str | None = Field(None, min_length=1)
    category_name: str | None = Field(None, max_length=100)
    tags: list[str] | None = None
    importance_score: float | None = None
    is_archived: bool | None = None


class MemorySearchItem(BaseModel):
    memory: MemoryResponse
    score: float


class MemorySearchResponse(BaseModel):
    results: list[MemorySearchItem]


class MemorySearchRequest(BaseModel):
    query: str = Field(..., min_length=1)
    limit: int = Field(5, ge=1, le=50)
    similarity_threshold: float = Field(0.5, ge=0.0, le=1.0)
    category: str | None = None
    tags: list[str] | None = None


class ArchiveMemoryRequest(BaseModel):
    memory_id: uuid.UUID


class MergeMemoryRequest(BaseModel):
    memory_id_1: uuid.UUID
    memory_id_2: uuid.UUID


class ConversationMessageResponse(BaseModel):
    id: uuid.UUID
    role: str
    content: str
    created_at: datetime

    class Config:
        from_attributes = True


class ConversationMessageCreate(BaseModel):
    role: str = Field(..., description="Message role (e.g. user, assistant)")
    content: str = Field(..., min_length=1, description="Message text content")


class ConversationSessionResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    title: str | None = None
    expires_at: datetime | None = None
    created_at: datetime
    updated_at: datetime
    messages: list[ConversationMessageResponse] = []

    class Config:
        from_attributes = True


class ConversationSessionCreate(BaseModel):
    title: str | None = Field(None, max_length=255)
    ttl_seconds: int | None = Field(None, ge=60, description="Time to live in seconds")


class ConversationSummaryResponse(BaseModel):
    id: uuid.UUID
    session_id: uuid.UUID
    summary: str
    created_at: datetime

    class Config:
        from_attributes = True
