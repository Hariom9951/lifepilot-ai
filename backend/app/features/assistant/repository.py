"""Assistant database repository handling async SQL operations."""

import uuid
from typing import Any

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.features.assistant.models import AssistantChat


class AssistantRepository:
    """
    Repository class providing static methods for managing Assistant chat logs.
    Follows the repository design pattern of LifePilot AI.
    """

    @staticmethod
    async def create_chat_exchange(
        db: AsyncSession,
        user_id: uuid.UUID,
        conversation_id: uuid.UUID,
        user_message: str,
        assistant_message: str,
        recommendations: list[str],
        actions: list[dict[str, Any]],
    ) -> AssistantChat:
        """Create and persist a new chat exchange record in PostgreSQL."""
        chat = AssistantChat(
            user_id=user_id,
            conversation_id=conversation_id,
            user_message=user_message,
            assistant_message=assistant_message,
            recommendations=recommendations,
            actions=actions,
        )
        db.add(chat)
        await db.flush()
        return chat

    @staticmethod
    async def list_history_by_user(
        db: AsyncSession,
        user_id: uuid.UUID,
        limit: int = 50,
        offset: int = 0,
    ) -> list[AssistantChat]:
        """Retrieve recent chat history for a user, ordered by creation date descending."""
        stmt = (
            select(AssistantChat)
            .where(AssistantChat.user_id == user_id)
            .order_by(AssistantChat.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await db.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def clear_history_by_user(db: AsyncSession, user_id: uuid.UUID) -> None:
        """Delete all chat logs for a user from PostgreSQL."""
        stmt = delete(AssistantChat).where(AssistantChat.user_id == user_id)
        await db.execute(stmt)
        await db.flush()
