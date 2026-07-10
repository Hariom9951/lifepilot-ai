"""Assistant API routers implementing chat and history logs management."""

from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.responses.schemas import SuccessResponse
from app.core.database.session import get_db_session
from app.features.assistant.dependencies import get_current_user
from app.features.assistant.schemas import (
    ChatHistoryItem,
    ChatHistoryResponse,
    ChatRequest,
    ChatResponse,
)
from app.features.assistant.services import AssistantService
from app.features.auth.models import User

router = APIRouter(prefix="/assistant", tags=["Assistant"])


@router.post(
    "/chat",
    response_model=SuccessResponse[ChatResponse],
    status_code=status.HTTP_200_OK,
    summary="Submit user query to assistant conversational channel",
)
async def process_chat(
    payload: ChatRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> SuccessResponse[ChatResponse]:
    """
    Classifies intent of query, runs tools against DB context tables,
    computes response recommendations/actions, and persists chat exchange logs.
    """
    response_data = await AssistantService.process_chat(
        db=db,
        user_id=current_user.id,
        full_name=current_user.full_name,
        message=payload.message,
        conversation_id=payload.conversation_id,
    )
    await db.commit()
    return SuccessResponse(
        message="Assistant chat processed successfully.",
        data=response_data,
    )


@router.get(
    "/history",
    response_model=SuccessResponse[ChatHistoryResponse],
    status_code=status.HTTP_200_OK,
    summary="List recent chat messages history for logged-in user",
)
async def list_chat_history(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    limit: int = 50,
    offset: int = 0,
) -> SuccessResponse[ChatHistoryResponse]:
    """Retrieves paginated chat history exchanges logged for the current user."""
    records = await AssistantService.get_history(
        db=db, user_id=current_user.id, limit=limit, offset=offset
    )

    items = [
        ChatHistoryItem(
            id=chat.id,
            conversation_id=chat.conversation_id,
            user_message=chat.user_message,
            assistant_message=chat.assistant_message,
            recommendations=chat.recommendations or [],
            actions=list(chat.actions),
            created_at=chat.created_at,
        )
        for chat in records
    ]

    return SuccessResponse(
        message="Assistant chat history retrieved successfully.",
        data=ChatHistoryResponse(items=items),
    )


@router.delete(
    "/history",
    response_model=SuccessResponse[dict],
    status_code=status.HTTP_200_OK,
    summary="Delete all chat history logs for logged-in user",
)
async def clear_chat_history(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> SuccessResponse[dict]:
    """Deletes all conversational assistant chat entries registered under user session."""
    await AssistantService.clear_history(db=db, user_id=current_user.id)
    await db.commit()
    return SuccessResponse(
        message="Assistant chat history cleared successfully.",
        data={},
    )
