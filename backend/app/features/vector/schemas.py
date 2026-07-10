from typing import Any

from pydantic import BaseModel, Field


class ChunkInput(BaseModel):
    id: str | None = Field(None, description="Optional unique identifier for the chunk")
    content: str = Field(..., description="The textual chunk content")
    document_id: str | None = Field(None, description="Optional document ID link")
    source: str | None = Field(None, description="Optional source label")
    metadata: dict[str, Any] | None = Field(
        None, description="Optional metadata fields"
    )


class VectorIndexRequest(BaseModel):
    chunks: list[ChunkInput] = Field(
        ..., min_length=1, description="List of chunks to index"
    )


class VectorIndexItem(BaseModel):
    id: str
    content: str
    document_id: str | None
    source: str | None
    metadata: dict[str, Any]


class VectorIndexResponse(BaseModel):
    indexed_chunks: list[VectorIndexItem] = Field(
        ..., description="List of successfully indexed chunks"
    )


class VectorSearchRequest(BaseModel):
    query: str = Field(..., description="Hybrid retrieval search query string")
    limit: int = Field(
        5, ge=1, le=100, description="Retrieve Top-K matching candidates"
    )
    semantic_weight: float = Field(
        0.7, ge=0.0, le=1.0, description="Semantic cosine score coefficient"
    )
    keyword_weight: float = Field(
        0.3, ge=0.0, le=1.0, description="BM25 scoring weight coefficient"
    )
    metadata_filter: dict[str, Any] | None = Field(
        None, description="Additional custom filtering keys"
    )


class VectorSearchResultItem(BaseModel):
    chunk_id: str
    score: float
    content: str
    metadata: dict[str, Any]


class VectorSearchResponse(BaseModel):
    results: list[VectorSearchResultItem] = Field(
        ..., description="Deduplicated hybrid search result candidates"
    )


class VectorStatusResponse(BaseModel):
    provider: str
    chunks_count: int
