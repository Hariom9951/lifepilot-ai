import uuid
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.responses.schemas import SuccessResponse
from app.core.database.session import get_db_session
from app.features.auth.dependencies import get_current_user
from app.features.auth.models import User
from app.features.auth.schemas import MessageResponse
from app.features.memory.schemas import (
    ArchiveMemoryRequest,
    ConversationSessionCreate,
    ConversationSessionResponse,
    ConversationSummaryResponse,
    MemoryCreate,
    MemoryResponse,
    MemorySearchRequest,
    MemorySearchResponse,
    MemoryUpdate,
    MergeMemoryRequest,
)
from app.features.memory.services import MemoryService
from app.features.memory.workers import run_conversation_summarization

router = APIRouter(prefix="/memory", tags=["Memory"])


@router.post(
    "",
    response_model=SuccessResponse[MemoryResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Create a new long-term personal memory record",
)
async def create_memory(
    payload: MemoryCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> SuccessResponse[MemoryResponse]:
    memory = await MemoryService.create_memory(
        db=db,
        user_id=current_user.id,
        content=payload.content,
        category_name=payload.category_name,
        tags=payload.tags,
    )
    return SuccessResponse(
        message="Memory created and vector indexed successfully.",
        data=MemoryResponse.model_validate(memory),
    )


@router.get(
    "",
    response_model=SuccessResponse[list[MemoryResponse]],
    status_code=status.HTTP_200_OK,
    summary="List memories with optional tag and category filters",
)
async def list_memories(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    category: Annotated[
        str | None, Query(description="Filter by category name")
    ] = None,
    tags: Annotated[list[str] | None, Query(description="Filter by tag names")] = None,
    is_archived: Annotated[
        bool | None, Query(description="Filter by archived status")
    ] = False,
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 100,
) -> SuccessResponse[list[MemoryResponse]]:
    memories = await MemoryService.list_memories(
        db=db,
        user_id=current_user.id,
        category_name=category,
        tag_names=tags,
        is_archived=is_archived,
        skip=skip,
        limit=limit,
    )
    return SuccessResponse(
        message="Memories retrieved successfully.",
        data=[MemoryResponse.model_validate(m) for m in memories],
    )


@router.get(
    "/{memory_id}",
    response_model=SuccessResponse[MemoryResponse],
    status_code=status.HTTP_200_OK,
    summary="Get single memory detail",
)
async def get_memory(
    memory_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> SuccessResponse[MemoryResponse]:
    # Reuse list logic to enforce user ownership check
    memories = await MemoryService.list_memories(
        db=db, user_id=current_user.id, is_archived=None
    )
    memory = next((m for m in memories if m.id == memory_id), None)
    if not memory:
        from app.features.memory.exceptions import MemoryNotFoundError

        raise MemoryNotFoundError()

    return SuccessResponse(
        message="Memory details retrieved successfully.",
        data=MemoryResponse.model_validate(memory),
    )


@router.patch(
    "/{memory_id}",
    response_model=SuccessResponse[MemoryResponse],
    status_code=status.HTTP_200_OK,
    summary="Update content, tags, category or metadata of a memory",
)
async def update_memory(
    memory_id: uuid.UUID,
    payload: MemoryUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> SuccessResponse[MemoryResponse]:
    updated_memory = await MemoryService.update_memory(
        db=db,
        memory_id=memory_id,
        user_id=current_user.id,
        content=payload.content,
        category_name=payload.category_name,
        tags=payload.tags,
        importance_score=payload.importance_score,
        is_archived=payload.is_archived,
    )
    return SuccessResponse(
        message="Memory record updated successfully.",
        data=MemoryResponse.model_validate(updated_memory),
    )


@router.delete(
    "/{memory_id}",
    response_model=SuccessResponse[MessageResponse],
    status_code=status.HTTP_200_OK,
    summary="Permanently delete a memory record and its vector mappings",
)
async def delete_memory(
    memory_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> SuccessResponse[MessageResponse]:
    await MemoryService.delete_memory(
        db=db, memory_id=memory_id, user_id=current_user.id
    )
    return SuccessResponse(
        message="Memory and semantic vectors deleted successfully.",
        data=MessageResponse(success=True, message="Deleted memory successfully."),
    )


@router.post(
    "/search",
    response_model=SuccessResponse[MemorySearchResponse],
    status_code=status.HTTP_200_OK,
    summary="Vector-similarity search with hybrid filters",
)
async def search_memories(
    payload: MemorySearchRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> SuccessResponse[MemorySearchResponse]:
    results = await MemoryService.search_memory(
        db=db,
        user_id=current_user.id,
        query=payload.query,
        limit=payload.limit,
        similarity_threshold=payload.similarity_threshold,
        category=payload.category,
        tags=payload.tags,
    )

    response_items = []
    for item in results:
        response_items.append(
            {
                "memory": MemoryResponse.model_validate(item["memory"]),
                "score": item["score"],
            }
        )

    return SuccessResponse(
        message="Similarity search complete.",
        data=MemorySearchResponse(results=response_items),
    )


@router.post(
    "/archive",
    response_model=SuccessResponse[MemoryResponse],
    status_code=status.HTTP_200_OK,
    summary="Archive a long-term memory to keep it out of active search",
)
async def archive_memory(
    payload: ArchiveMemoryRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> SuccessResponse[MemoryResponse]:
    archived = await MemoryService.archive_memory(
        db=db, memory_id=payload.memory_id, user_id=current_user.id
    )
    return SuccessResponse(
        message="Memory successfully archived.",
        data=MemoryResponse.model_validate(archived),
    )


@router.post(
    "/summarize",
    response_model=SuccessResponse[ConversationSummaryResponse],
    status_code=status.HTTP_202_ACCEPTED,
    summary="Queue asynchronous summarization for a conversation session",
)
async def summarize_conversation(
    session_id: uuid.UUID,
    background_tasks: BackgroundTasks,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> SuccessResponse[ConversationSummaryResponse]:
    # Synchronously create record for response, then trigger worker task
    summary = await MemoryService.summarize_conversation(
        db=db, session_id=session_id, user_id=current_user.id
    )

    background_tasks.add_task(
        run_conversation_summarization, session_id, current_user.id
    )

    return SuccessResponse(
        message="Conversation summarization started.",
        data=ConversationSummaryResponse.model_validate(summary),
    )


@router.post(
    "/merge",
    response_model=SuccessResponse[MemoryResponse],
    status_code=status.HTTP_200_OK,
    summary="Merge two duplicate memories, combining content, score, and tags",
)
async def merge_memories(
    payload: MergeMemoryRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> SuccessResponse[MemoryResponse]:
    merged_memory = await MemoryService.merge_duplicate_memory(
        db=db,
        user_id=current_user.id,
        memory_id_1=payload.memory_id_1,
        memory_id_2=payload.memory_id_2,
    )
    return SuccessResponse(
        message="Duplicate memory records merged successfully.",
        data=MemoryResponse.model_validate(merged_memory),
    )


# -------------------------------------------------------------------------
# Short-Term / Conversation Session REST APIs
# -------------------------------------------------------------------------


@router.post(
    "/session",
    response_model=SuccessResponse[ConversationSessionResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Create a new conversation session (cached short-term memory)",
)
async def create_session(
    payload: ConversationSessionCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> SuccessResponse[ConversationSessionResponse]:
    session = await MemoryService.create_session(
        db=db,
        user_id=current_user.id,
        title=payload.title,
        ttl_seconds=payload.ttl_seconds,
    )
    return SuccessResponse(
        message="Conversation session created.",
        data=ConversationSessionResponse.model_validate(session),
    )
