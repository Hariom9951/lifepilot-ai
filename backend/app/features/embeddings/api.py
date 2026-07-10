from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.responses.schemas import SuccessResponse
from app.core.database.session import get_db_session
from app.features.auth.dependencies import get_current_user
from app.features.auth.models import User
from app.features.auth.schemas import MessageResponse
from app.features.embeddings.cache import EmbeddingCacheManager
from app.features.embeddings.providers import MODEL_DIMENSIONS, get_active_provider
from app.features.embeddings.schemas import (
    EmbeddingsGenerateRequest,
    EmbeddingsGenerateResponse,
    EmbeddingsProvidersResponse,
    EmbeddingsStatusResponse,
    ProviderDetail,
)
from app.features.embeddings.services import EmbeddingEngineService

router = APIRouter(prefix="/embeddings", tags=["Embeddings"])


@router.post(
    "/generate",
    response_model=SuccessResponse[EmbeddingsGenerateResponse],
    status_code=status.HTTP_200_OK,
    summary="Generate high-performance embeddings for text inputs",
)
async def generate_embeddings(
    payload: EmbeddingsGenerateRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> SuccessResponse[EmbeddingsGenerateResponse]:
    """
    Computes embedding vectors for a list of text inputs.
    Utilizes persistent content-hash caching to bypass regeneration of existing lines.
    """
    vectors = await EmbeddingEngineService.generate_embeddings(db, payload.texts)
    return SuccessResponse(
        message="Embeddings generated successfully.",
        data=EmbeddingsGenerateResponse(embeddings=vectors),
    )


@router.post(
    "/rebuild",
    response_model=SuccessResponse[MessageResponse],
    status_code=status.HTTP_200_OK,
    summary="Clear persistent embedding caches to trigger fresh rebuilds",
)
async def rebuild_embeddings(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> SuccessResponse[MessageResponse]:
    """
    Truncates the embedding cache records forcing regenerations across subsequent processes.
    """
    rows_cleared = await EmbeddingCacheManager.clear_cache(db)
    await db.commit()
    return SuccessResponse(
        message="Embedding cache cleared.",
        data=MessageResponse(
            success=True, message=f"Purged {rows_cleared} cached embedding items."
        ),
    )


@router.get(
    "/providers",
    response_model=SuccessResponse[EmbeddingsProvidersResponse],
    status_code=status.HTTP_200_OK,
    summary="Retrieve list of configured embedding providers and details",
)
async def list_providers(
    current_user: Annotated[User, Depends(get_current_user)],
) -> SuccessResponse[EmbeddingsProvidersResponse]:
    """
    Returns available sentence-transformers embedding providers with their metadata.
    """
    active_provider = get_active_provider()
    active_model = active_provider.model_name

    provider_details = []
    for model_name, dimension in MODEL_DIMENSIONS.items():
        provider_details.append(
            ProviderDetail(
                model_name=model_name,
                dimension=dimension,
                is_active=(model_name == active_model),
            )
        )

    return SuccessResponse(
        message="Supported embedding providers list.",
        data=EmbeddingsProvidersResponse(
            providers=provider_details, active_device=active_provider.get_device()
        ),
    )


@router.get(
    "/status",
    response_model=SuccessResponse[EmbeddingsStatusResponse],
    status_code=status.HTTP_200_OK,
    summary="Get cache hit rates and hardware/GPU utilization statistics",
)
async def get_embeddings_status(
    current_user: Annotated[User, Depends(get_current_user)],
) -> SuccessResponse[EmbeddingsStatusResponse]:
    """
    Returns telemetry metrics covering requests, cache hits/misses, and VRAM memory footprint.
    """
    metrics = EmbeddingEngineService.get_metrics()
    return SuccessResponse(
        message="Embeddings status metrics retrieved.",
        data=EmbeddingsStatusResponse.model_validate(metrics),
    )
