"""Assistant service layer coordinating orchestrator and database queries."""

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.features.assistant.models import AssistantChat
from app.features.assistant.orchestrator import AssistantOrchestrator
from app.features.assistant.repository import AssistantRepository
from app.features.assistant.schemas import ChatResponse


class AssistantService:
    """
    Service layer class containing class methods for assistant queries and log operations.
    Follows project architectural conventions.
    """

    @classmethod
    async def process_chat(
        cls,
        db: AsyncSession,
        user_id: uuid.UUID,
        full_name: str,
        message: str,
        conversation_id: uuid.UUID | None = None,
    ) -> ChatResponse:
        """Processes the chat input through intent classification, planner execution, and saves exchange logs."""
        return await AssistantOrchestrator.process_chat(
            db=db,
            user_id=user_id,
            full_name=full_name,
            message=message,
            conversation_id=conversation_id,
        )

    @classmethod
    async def get_history(
        cls,
        db: AsyncSession,
        user_id: uuid.UUID,
        limit: int = 50,
        offset: int = 0,
    ) -> list[AssistantChat]:
        """Retrieves paginated chat history logs for a specific user from the database."""
        return await AssistantRepository.list_history_by_user(
            db=db, user_id=user_id, limit=limit, offset=offset
        )

    @classmethod
    async def clear_history(
        cls,
        db: AsyncSession,
        user_id: uuid.UUID,
    ) -> None:
        """Deletes all persistent chat history entries for a specific user."""
        await AssistantRepository.clear_history_by_user(db=db, user_id=user_id)
