"""
Knowledge API router — 4 secured endpoints for document management.
"""
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
    DocumentStatusResponse,
)
from app.features.knowledge.services import KnowledgeService

router = APIRouter(prefix="/knowledge", tags=["Knowledge"])


@router.post(
    "/upload",
    response_model=SuccessResponse[DocumentResponse],
    status_code=status.HTTP_202_ACCEPTED,
    summary="Upload a personal knowledge document for async processing",
)
async def upload_document(
    background_tasks: BackgroundTasks,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    file: Annotated[UploadFile, File(description="PDF, DOCX, TXT, or Markdown file")],
) -> SuccessResponse[DocumentResponse]:
    """
    Upload a document. The file is saved immediately and text extraction +
    embedding is queued as a background task. Returns status=uploaded.
    """
    doc = await KnowledgeService.upload_document(db, current_user.id, file)

    # Queue background processing after the response is sent
    background_tasks.add_task(
        KnowledgeService.process_document_background, doc.id
    )

    return SuccessResponse(
        message="Document uploaded successfully. Processing queued.",
        data=DocumentResponse.model_validate(doc),
    )


@router.get(
    "/documents",
    response_model=SuccessResponse[DocumentListResponse],
    status_code=status.HTTP_200_OK,
    summary="List all documents owned by the current user",
)
async def list_documents(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> SuccessResponse[DocumentListResponse]:
    """
    Returns all documents for the authenticated user ordered by upload date.
    """
    docs = await KnowledgeService.list_documents(db, current_user.id)
    return SuccessResponse(
        message="Documents retrieved successfully.",
        data=DocumentListResponse(
            total=len(docs),
            items=[DocumentResponse.model_validate(d) for d in docs],
        ),
    )


@router.get(
    "/status/{document_id}",
    response_model=SuccessResponse[DocumentStatusResponse],
    status_code=status.HTTP_200_OK,
    summary="Poll the processing status of a specific document",
)
async def get_document_status(
    document_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> SuccessResponse[DocumentStatusResponse]:
    """
    Returns the current processing status of a document owned by the user.
    Poll this endpoint after upload to detect when processing reaches 'ready'.
    """
    doc = await KnowledgeService.get_status(db, document_id, current_user.id)
    return SuccessResponse(
        message="Document status retrieved.",
        data=DocumentStatusResponse.model_validate(doc),
    )


@router.delete(
    "/{document_id}",
    response_model=SuccessResponse[MessageResponse],
    status_code=status.HTTP_200_OK,
    summary="Delete a document and all associated vector embeddings",
)
async def delete_document(
    document_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> SuccessResponse[MessageResponse]:
    """
    Permanently deletes a document, its stored file, and its FAISS vectors.
    Only the document's owner may delete it.
    """
    await KnowledgeService.delete_document(db, document_id, current_user.id)
    return SuccessResponse(
        message="Document deleted successfully.",
        data=MessageResponse(success=True, message="Document and embeddings removed."),
    )
