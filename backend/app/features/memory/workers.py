import logging
import uuid
from datetime import UTC, datetime

from sqlalchemy import delete, select

from app.core.database.session import SessionLocal
from app.features.memory.models import ConversationSession, UserMemory
from app.features.memory.services import MemoryService

logger = logging.getLogger("app.memory.workers")


async def run_conversation_summarization(
    session_id: uuid.UUID, user_id: uuid.UUID
) -> None:
    """
    Background worker task to summarize a conversation session asynchronously.
    """
    logger.info(f"Background summarization worker triggered for session {session_id}")
    async with SessionLocal() as db:
        try:
            await MemoryService.summarize_conversation(db, session_id, user_id)
            logger.info(f"Background summarization complete for session {session_id}")
        except Exception as e:
            logger.error(
                f"Failed background conversation summarization for {session_id}: {e}"
            )


async def cleanup_expired_sessions() -> int:
    """
    Background worker to delete expired conversation sessions from Postgres.
    Returns count of deleted sessions.
    """
    logger.info("Background session cleanup worker triggered")
    now = datetime.now(UTC)
    async with SessionLocal() as db:
        try:
            stmt = delete(ConversationSession).where(
                ConversationSession.expires_at < now
            )
            result = await db.execute(stmt)
            await db.commit()
            deleted_count = result.rowcount
            logger.info(f"Evicted {deleted_count} expired conversation sessions.")
            return deleted_count
        except Exception as e:
            logger.error(f"Failed session eviction cleanup worker: {e}")
            return 0


async def run_importance_score_decay(decay_factor: float = 0.95) -> int:
    """
    Background worker to decay importance scores over time for non-archived memories.
    Simulates memory decay over time. Updates PostgreSQL and the Vector Store.
    """
    logger.info(f"Background score decay worker triggered with factor {decay_factor}")
    async with SessionLocal() as db:
        try:
            # Query all non-archived memories
            stmt = select(UserMemory).where(UserMemory.is_archived.is_(False))
            res = await db.execute(stmt)
            memories = res.scalars().all()

            updated_count = 0
            for mem in memories:
                # Minimum score threshold is 1.0
                new_score = max(1.0, mem.importance_score * decay_factor)
                if new_score != mem.importance_score:
                    mem.importance_score = new_score
                    db.add(mem)
                    updated_count += 1

            if updated_count > 0:
                await db.commit()

            logger.info(f"Decayed importance score for {updated_count} memories.")
            return updated_count
        except Exception as e:
            logger.error(f"Failed score decay worker: {e}")
            return 0
