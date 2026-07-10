from pydantic import BaseModel, Field


class EmbeddingsGenerateRequest(BaseModel):
    texts: list[str] = Field(
        ..., min_length=1, description="List of texts to generate embeddings for"
    )


class EmbeddingsGenerateResponse(BaseModel):
    embeddings: list[list[float]] = Field(
        ..., description="List of generated float vector lists"
    )


class ProviderDetail(BaseModel):
    model_name: str
    dimension: int
    is_active: bool


class EmbeddingsProvidersResponse(BaseModel):
    providers: list[ProviderDetail]
    active_device: str


class GPUInfo(BaseModel):
    vram_allocated_mb: float
    vram_cached_mb: float
    device_name: str


class EmbeddingsStatusResponse(BaseModel):
    active_provider: str
    device: str
    dimension: int
    total_requests: int
    total_texts_processed: int
    cache_hit_ratio: float
    average_latency_ms: float
    gpu: GPUInfo
