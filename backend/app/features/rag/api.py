from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database.session import get_db_session
from app.features.auth.dependencies import get_current_user
from app.features.auth.models import User
from app.features.rag.schemas import (
    RAGIndexRequest,
    RAGIndexResponse,
    RAGSearchMatch,
    RAGSearchRequest,
    RAGSearchResponse,
)
from app.features.rag.services import RAGService

router = APIRouter(prefix="/rag", tags=["RAG Context Search"])


@router.post(
    "/search",
    response_model=RAGSearchResponse,
    status_code=status.HTTP_200_OK,
)
async def search_rag(
    payload: RAGSearchRequest,
    db: Annotated[AsyncSession, Depends(get_db_session)],
    user: Annotated[User, Depends(get_current_user)],
):
    """
    Executes a hybrid semantic vector search with keyword overlap reranking
    across the user's uploaded documents and notes.
    """
    results = await RAGService.search_knowledge_base(
        db=db,
        user_id=user.id,
        query=payload.query,
        limit=payload.limit,
        score_threshold=payload.score_threshold,
        metadata_filter=payload.metadata_filter,
    )
    matches = [
        RAGSearchMatch(
            content=res["content"],
            score=res["score"],
            document=res["document"],
            metadata=res["metadata"],
        )
        for res in results
    ]
    return RAGSearchResponse(query=payload.query, matches=matches)


@router.post(
    "/index",
    response_model=RAGIndexResponse,
    status_code=status.HTTP_200_OK,
)
async def trigger_indexing(
    payload: RAGIndexRequest | None = None,
    reindex: bool = Query(
        False, description="Force a full rebuild of the vector index from scratch."
    ),
    db: Annotated[AsyncSession, Depends(get_db_session)] = None,  # type: ignore
    user: Annotated[User, Depends(get_current_user)] = None,  # type: ignore
):
    """
    Triggers incremental chunking and embedding, or forces a complete vector store rebuild.
    """
    if reindex:
        count = await RAGService.reindex_all_user_knowledge(db, user.id)
        msg = "Successfully rebuilt the full knowledge base index."
    else:
        doc_ids = payload.document_ids if payload else None
        notes = payload.notes if payload else True
        journals = payload.journals if payload else True

        count = await RAGService.index_user_knowledge(
            db=db,
            user_id=user.id,
            document_ids=doc_ids,
            index_notes=notes,
            index_journals=journals,
        )
        msg = f"Incremental indexing complete. Processed {count} new chunks."

    return RAGIndexResponse(indexed_count=count, message=msg)
