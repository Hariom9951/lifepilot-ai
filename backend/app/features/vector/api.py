from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.responses.schemas import SuccessResponse
from app.core.database.session import get_db_session
from app.features.auth.dependencies import get_current_user
from app.features.auth.models import User
from app.features.auth.schemas import MessageResponse
from app.features.vector.repositories import DocumentChunkRepository
from app.features.vector.schemas import (
    VectorIndexRequest,
    VectorIndexResponse,
    VectorSearchRequest,
    VectorSearchResponse,
    VectorStatusResponse,
)
from app.features.vector.services import HybridRetrievalService

router = APIRouter(prefix="/vector", tags=["Vector Store"])


@router.post(
    "/index",
    response_model=SuccessResponse[VectorIndexResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Index document text chunks in hybrid storage system",
)
async def index_chunks(
    payload: VectorIndexRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> SuccessResponse[VectorIndexResponse]:
    """
    Ingests and embeds document chunks in the active vector DB and SQL database.
    """
    chunks_list = [c.model_dump() for c in payload.chunks]
    indexed = await HybridRetrievalService.batch_index_chunks(
        db, current_user.id, chunks_list
    )
    await db.commit()
    return SuccessResponse(
        message="Chunks indexed successfully.",
        data=VectorIndexResponse(indexed_chunks=indexed),
    )


@router.post(
    "/search",
    response_model=SuccessResponse[VectorSearchResponse],
    status_code=status.HTTP_200_OK,
    summary="Perform semantic & BM25 hybrid score-fused query search",
)
async def search_hybrid(
    payload: VectorSearchRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> SuccessResponse[VectorSearchResponse]:
    """
    Queries vector index and BM25 store, fusing results using weighted parameters.
    """
    hits = await HybridRetrievalService.hybrid_search(
        db=db,
        user_id=current_user.id,
        query=payload.query,
        limit=payload.limit,
        semantic_weight=payload.semantic_weight,
        keyword_weight=payload.keyword_weight,
        metadata_filter=payload.metadata_filter,
    )
    return SuccessResponse(
        message="Hybrid search executed successfully.",
        data=VectorSearchResponse(results=hits),
    )


@router.delete(
    "/{chunk_id}",
    response_model=SuccessResponse[MessageResponse],
    status_code=status.HTTP_200_OK,
    summary="Delete a single text chunk by UUID ID",
)
async def delete_chunk(
    chunk_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> SuccessResponse[MessageResponse]:
    """
    Purges a chunk ID from active vector provider indices and SQL document storage.
    """
    import uuid

    try:
        cid = uuid.UUID(chunk_id)
    except ValueError:
        return SuccessResponse(
            message="Invalid UUID ID format.",
            data=MessageResponse(
                success=False, message="Chunk ID must be a valid UUID."
            ),
        )

    deleted = await HybridRetrievalService.delete_chunk(db, current_user.id, cid)
    await db.commit()

    if deleted:
        return SuccessResponse(
            message="Chunk deleted.",
            data=MessageResponse(
                success=True, message=f"Successfully purged chunk ID {chunk_id}."
            ),
        )
    return SuccessResponse(
        message="Chunk not found.",
        data=MessageResponse(
            success=False,
            message=f"No chunk record matching ID {chunk_id} in database.",
        ),
    )


@router.post(
    "/rebuild",
    response_model=SuccessResponse[MessageResponse],
    status_code=status.HTTP_200_OK,
    summary="Rebuild active vector storage index from SQL chunk source records",
)
async def rebuild_index(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> SuccessResponse[MessageResponse]:
    """
    Clears active vector database, recalculates embeddings, and re-adds all user SQL chunks.
    """
    count = await HybridRetrievalService.rebuild_index(db, current_user.id)
    await db.commit()
    return SuccessResponse(
        message="Vector database index rebuild complete.",
        data=MessageResponse(
            success=True,
            message=f"Reindexed {count} document text chunks in vector store.",
        ),
    )


@router.get(
    "/status",
    response_model=SuccessResponse[VectorStatusResponse],
    status_code=status.HTTP_200_OK,
    summary="Retrieve vector store provider type and text chunk statistics",
)
async def get_vector_status(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> SuccessResponse[VectorStatusResponse]:
    """
    Telemetry statistics regarding current active vector database provider name and document/chunk counts.
    """
    from app.core.config.settings import settings

    chunks = await DocumentChunkRepository.get_user_chunks(db, current_user.id)
    return SuccessResponse(
        message="Vector store status retrieved.",
        data=VectorStatusResponse(
            provider=settings.VECTOR_PROVIDER,
            chunks_count=len(chunks),
        ),
    )
