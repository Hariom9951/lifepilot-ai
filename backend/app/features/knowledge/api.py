import uuid
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, File, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.responses.schemas import SuccessResponse
from app.core.database.session import get_db_session
from app.features.auth.dependencies import get_current_user
from app.features.auth.models import User
from app.features.auth.schemas import MessageResponse
from app.features.knowledge.schemas import (
    DocumentListResponse,
    DocumentResponse,
    DocumentSearchRequest,
    DocumentSearchResponse,
    DocumentStatusResponse,
)
from app.features.knowledge.services import KnowledgeService

# Define routers for both prefixes
documents_router = APIRouter(prefix="/documents", tags=["Documents"])
knowledge_router = APIRouter(prefix="/knowledge", tags=["Knowledge"])


# -------------------------------------------------------------------------
# Upload Document
# -------------------------------------------------------------------------


@documents_router.post(
    "/upload",
    response_model=SuccessResponse[DocumentResponse],
    status_code=status.HTTP_202_ACCEPTED,
    summary="Upload a new personal RAG document",
)
@knowledge_router.post(
    "/upload",
    response_model=SuccessResponse[DocumentResponse],
    status_code=status.HTTP_202_ACCEPTED,
    summary="Upload a new personal RAG document (legacy path)",
)
async def upload_document(
    background_tasks: BackgroundTasks,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    file: Annotated[UploadFile, File(description="PDF, DOCX, TXT, or Markdown file")],
) -> SuccessResponse[DocumentResponse]:
    doc = await KnowledgeService.upload_document(db, current_user.id, file)
    background_tasks.add_task(KnowledgeService.process_document_background, doc.id)
    return SuccessResponse(
        message="Document uploaded successfully. Processing queued.",
        data=DocumentResponse.model_validate(doc),
    )


# -------------------------------------------------------------------------
# List Documents
# -------------------------------------------------------------------------


@documents_router.get(
    "",
    response_model=SuccessResponse[DocumentListResponse],
    status_code=status.HTTP_200_OK,
    summary="List all personal RAG documents",
)
@knowledge_router.get(
    "/documents",
    response_model=SuccessResponse[DocumentListResponse],
    status_code=status.HTTP_200_OK,
    summary="List all personal RAG documents (legacy path)",
)
async def list_documents(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> SuccessResponse[DocumentListResponse]:
    docs = await KnowledgeService.list_documents(db, current_user.id)
    return SuccessResponse(
        message="Documents retrieved successfully.",
        data=DocumentListResponse(
            total=len(docs),
            items=[DocumentResponse.model_validate(d) for d in docs],
        ),
    )


# -------------------------------------------------------------------------
# Get Document Details
# -------------------------------------------------------------------------


@documents_router.get(
    "/{document_id}",
    response_model=SuccessResponse[DocumentResponse],
    status_code=status.HTTP_200_OK,
    summary="Retrieve details of a specific document",
)
@knowledge_router.get(
    "/{document_id}",
    response_model=SuccessResponse[DocumentResponse],
    status_code=status.HTTP_200_OK,
    summary="Retrieve details of a specific document (legacy path)",
)
async def get_document(
    document_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> SuccessResponse[DocumentResponse]:
    doc = await KnowledgeService.get_document(db, document_id, current_user.id)
    return SuccessResponse(
        message="Document details retrieved.",
        data=DocumentResponse.model_validate(doc),
    )


# -------------------------------------------------------------------------
# Poll Document Status
# -------------------------------------------------------------------------


@documents_router.get(
    "/status/{document_id}",
    response_model=SuccessResponse[DocumentStatusResponse],
    status_code=status.HTTP_200_OK,
    summary="Get processing status of a document",
)
@knowledge_router.get(
    "/status/{document_id}",
    response_model=SuccessResponse[DocumentStatusResponse],
    status_code=status.HTTP_200_OK,
    summary="Get processing status of a document (legacy path)",
)
async def get_document_status(
    document_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> SuccessResponse[DocumentStatusResponse]:
    doc = await KnowledgeService.get_status(db, document_id, current_user.id)
    return SuccessResponse(
        message="Document status retrieved.",
        data=DocumentStatusResponse.model_validate(doc),
    )


# -------------------------------------------------------------------------
# Delete Document
# -------------------------------------------------------------------------


@documents_router.delete(
    "/{document_id}",
    response_model=SuccessResponse[MessageResponse],
    status_code=status.HTTP_200_OK,
    summary="Delete a document and all its indexed chunks",
)
@knowledge_router.delete(
    "/{document_id}",
    response_model=SuccessResponse[MessageResponse],
    status_code=status.HTTP_200_OK,
    summary="Delete a document and all its indexed chunks (legacy path)",
)
async def delete_document(
    document_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> SuccessResponse[MessageResponse]:
    await KnowledgeService.delete_document(db, document_id, current_user.id)
    return SuccessResponse(
        message="Document deleted successfully.",
        data=MessageResponse(
            success=True, message="Document and vector chunks removed."
        ),
    )


# -------------------------------------------------------------------------
# Force Process Document
# -------------------------------------------------------------------------


@documents_router.post(
    "/process",
    response_model=SuccessResponse[MessageResponse],
    status_code=status.HTTP_202_ACCEPTED,
    summary="Trigger manual background processing or reprocessing of a document",
)
@knowledge_router.post(
    "/process",
    response_model=SuccessResponse[MessageResponse],
    status_code=status.HTTP_202_ACCEPTED,
    summary="Trigger manual background processing or reprocessing of a document (legacy path)",
)
async def process_document(
    payload: dict,
    background_tasks: BackgroundTasks,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> SuccessResponse[MessageResponse]:
    doc_id_str = payload.get("document_id")
    if not doc_id_str:
        from fastapi import HTTPException

        raise HTTPException(status_code=400, detail="Missing document_id in payload.")

    try:
        doc_id = uuid.UUID(doc_id_str)
    except ValueError as err:
        from fastapi import HTTPException

        raise HTTPException(
            status_code=400, detail="Invalid UUID format for document_id."
        ) from err

    # Enforce ownership check
    await KnowledgeService.get_document(db, doc_id, current_user.id)

    # Queue background processor task
    background_tasks.add_task(KnowledgeService.process_document_background, doc_id)
    return SuccessResponse(
        message="Manual document processing queued.",
        data=MessageResponse(
            success=True, message="Processing task started in background."
        ),
    )


# -------------------------------------------------------------------------
# Search Documents
# -------------------------------------------------------------------------


@documents_router.post(
    "/search",
    response_model=SuccessResponse[DocumentSearchResponse],
    status_code=status.HTTP_200_OK,
    summary="Perform vector-similarity hybrid search over document chunks",
)
@knowledge_router.post(
    "/search",
    response_model=SuccessResponse[DocumentSearchResponse],
    status_code=status.HTTP_200_OK,
    summary="Perform vector-similarity hybrid search over document chunks (legacy path)",
)
async def search_documents(
    payload: DocumentSearchRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> SuccessResponse[DocumentSearchResponse]:
    search_results = await KnowledgeService.search_documents(
        db=db,
        user_id=current_user.id,
        query=payload.query,
        limit=payload.limit,
        similarity_threshold=payload.similarity_threshold,
        category=payload.category,
        metadata_filter=payload.metadata_filter,
    )
    return SuccessResponse(
        message="Document search complete.",
        data=DocumentSearchResponse(results=search_results),
    )


# -------------------------------------------------------------------------
# Reindex Documents
# -------------------------------------------------------------------------


@documents_router.post(
    "/reindex",
    response_model=SuccessResponse[MessageResponse],
    status_code=status.HTTP_200_OK,
    summary="Queue re-processing of all user documents",
)
@knowledge_router.post(
    "/reindex",
    response_model=SuccessResponse[MessageResponse],
    status_code=status.HTTP_200_OK,
    summary="Queue re-processing of all user documents (legacy path)",
)
async def reindex_documents(
    background_tasks: BackgroundTasks,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> SuccessResponse[MessageResponse]:
    reindexed_count = await KnowledgeService.reindex_user_documents(db, current_user.id)
    # Queue processing tasks in background
    docs = await KnowledgeService.list_documents(db, current_user.id)
    for doc in docs:
        background_tasks.add_task(KnowledgeService.process_document_background, doc.id)

    return SuccessResponse(
        message="All user documents queued for reindexing.",
        data=MessageResponse(
            success=True,
            message=f"Reindexed {reindexed_count} documents in background.",
        ),
    )
