import json
import logging
import uuid
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config.settings import settings
from app.core.database.redis import redis_manager
from app.features.memory.embeddings import EmbeddingProvider, MockEmbeddingProvider
from app.features.memory.exceptions import MemoryNotFoundError, SessionNotFoundError
from app.features.memory.models import (
    ConversationMessage,
    ConversationSession,
    ConversationSummary,
    MemoryCategory,
    MemoryTag,
    UserMemory,
)
from app.features.memory.vector_providers import BaseVectorProvider, FAISSVectorProvider

logger = logging.getLogger("app.memory.services")

# Default providers
_embedding_provider: EmbeddingProvider = MockEmbeddingProvider(dimension=384)
_vector_provider: BaseVectorProvider = FAISSVectorProvider(
    base_dir=Path(settings.KNOWLEDGE_VECTOR_DIR), dimension=384
)


class MemoryService:
    """
    Core Memory Engine coordinating Short-Term (Redis), Long-Term (SQL), and Semantic (Vector) memories.
    """

    @classmethod
    def get_embedding_provider(cls) -> EmbeddingProvider:
        return _embedding_provider

    @classmethod
    def set_embedding_provider(cls, provider: EmbeddingProvider) -> None:
        global _embedding_provider
        _embedding_provider = provider

    @classmethod
    def get_vector_provider(cls) -> BaseVectorProvider:
        return _vector_provider

    @classmethod
    def set_vector_provider(cls, provider: BaseVectorProvider) -> None:
        global _vector_provider
        _vector_provider = provider

    # -------------------------------------------------------------------------
    # Long-Term / Semantic Memory Methods
    # -------------------------------------------------------------------------

    @classmethod
    def calculate_importance(cls, content: str) -> float:
        """
        Calculate importance score of a memory content based on heuristics.
        Score ranges from 1.0 to 10.0.
        """
        score = 1.0

        # Heuristic 1: Length boost
        words = content.split()
        if len(words) > 20:
            score += 2.0
        elif len(words) > 8:
            score += 1.0

        # Heuristic 2: Keyword matches
        keywords = {
            "remember": 3.0,
            "never": 2.5,
            "always": 2.5,
            "like": 1.5,
            "love": 2.0,
            "hate": 2.0,
            "important": 3.0,
            "must": 2.0,
            "prefer": 2.0,
            "favorite": 2.5,
            "avoid": 2.0,
        }

        content_lower = content.lower()
        for kw, val in keywords.items():
            if kw in content_lower:
                score += val

        return min(10.0, score)

    @classmethod
    def _resolve_category(cls, user_id: uuid.UUID, category_name: str) -> str:
        """Helper to normalize category names."""
        return category_name.strip().title()

    @classmethod
    async def get_or_create_category(
        cls, db: AsyncSession, user_id: uuid.UUID, category_name: str
    ) -> MemoryCategory:
        normalized = cls._resolve_category(user_id, category_name)
        # Check global system categories (user_id is Null) or user specific categories
        stmt = select(MemoryCategory).where(
            and_(
                MemoryCategory.name == normalized,
                (MemoryCategory.user_id == user_id)
                | (MemoryCategory.user_id.is_(None)),
            )
        )
        res = await db.execute(stmt)
        cat = res.scalar_one_or_none()
        if not cat:
            cat = MemoryCategory(user_id=user_id, name=normalized)
            db.add(cat)
            await db.flush()
        return cat

    @classmethod
    async def get_or_create_tags(
        cls, db: AsyncSession, user_id: uuid.UUID, tag_names: list[str]
    ) -> list[MemoryTag]:
        tags = []
        for name in tag_names:
            normalized = name.strip().lower()
            if not normalized:
                continue
            stmt = select(MemoryTag).where(
                and_(MemoryTag.name == normalized, MemoryTag.user_id == user_id)
            )
            res = await db.execute(stmt)
            tag = res.scalar_one_or_none()
            if not tag:
                tag = MemoryTag(user_id=user_id, name=normalized)
                db.add(tag)
                await db.flush()
            tags.append(tag)
        return tags

    @classmethod
    async def create_memory(
        cls,
        db: AsyncSession,
        user_id: uuid.UUID,
        content: str,
        category_name: str | None = None,
        tags: list[str] | None = None,
    ) -> UserMemory:
        # Calculate score
        importance = cls.calculate_importance(content)

        # Resolve category if any
        category_id = None
        if category_name:
            cat = await cls.get_or_create_category(db, user_id, category_name)
            category_id = cat.id

        # Resolve tags
        resolved_tags = []
        if tags:
            resolved_tags = await cls.get_or_create_tags(db, user_id, tags)

        # Create record
        memory = UserMemory(
            user_id=user_id,
            content=content.strip(),
            importance_score=importance,
            category_id=category_id,
            is_archived=False,
        )
        if resolved_tags:
            memory.tags = resolved_tags

        db.add(memory)
        await db.flush()

        # Vector semantic persist
        emb_provider = cls.get_embedding_provider()
        embedding = emb_provider.generate_embedding(content)

        vec_provider = cls.get_vector_provider()
        vec_metadata = {
            "content": content,
            "category": category_name or "",
            "tags": tags or [],
        }
        vec_provider.add(user_id, memory.id, embedding, vec_metadata)

        await db.commit()
        # Eager load relationships for response
        stmt = (
            select(UserMemory)
            .where(UserMemory.id == memory.id)
            .options(selectinload(UserMemory.category), selectinload(UserMemory.tags))
        )
        res = await db.execute(stmt)
        return res.scalar_one()

    @classmethod
    async def update_memory(
        cls,
        db: AsyncSession,
        memory_id: uuid.UUID,
        user_id: uuid.UUID,
        content: str | None = None,
        category_name: str | None = None,
        tags: list[str] | None = None,
        importance_score: float | None = None,
        is_archived: bool | None = None,
    ) -> UserMemory:
        stmt = (
            select(UserMemory)
            .where(and_(UserMemory.id == memory_id, UserMemory.user_id == user_id))
            .options(selectinload(UserMemory.category), selectinload(UserMemory.tags))
        )
        res = await db.execute(stmt)
        memory = res.scalar_one_or_none()
        if not memory:
            raise MemoryNotFoundError()

        content_changed = False
        if content is not None:
            new_content = content.strip()
            if memory.content != new_content:
                memory.content = new_content
                content_changed = True
                # Automatically update importance unless explicitly provided
                if importance_score is None:
                    memory.importance_score = cls.calculate_importance(new_content)

        if importance_score is not None:
            memory.importance_score = importance_score

        if is_archived is not None:
            memory.is_archived = is_archived

        # Handle category
        if category_name is not None:
            if category_name.strip() == "":
                memory.category_id = None
            else:
                cat = await cls.get_or_create_category(db, user_id, category_name)
                memory.category_id = cat.id

        # Handle tags
        if tags is not None:
            resolved_tags = await cls.get_or_create_tags(db, user_id, tags)
            memory.tags = resolved_tags

        db.add(memory)
        await db.flush()

        # Update Vector Db if content changed
        if content_changed:
            emb_provider = cls.get_embedding_provider()
            embedding = emb_provider.generate_embedding(memory.content)
            vec_provider = cls.get_vector_provider()

            # Retrieve active category and tag text for vector metadata
            cat_name = ""
            if memory.category_id:
                # Reload category
                cat_stmt = select(MemoryCategory).where(
                    MemoryCategory.id == memory.category_id
                )
                cat_res = await db.execute(cat_stmt)
                cat_obj = cat_res.scalar_one_or_none()
                if cat_obj:
                    cat_name = cat_obj.name

            tag_names = [t.name for t in memory.tags]
            vec_metadata = {
                "content": memory.content,
                "category": cat_name,
                "tags": tag_names,
            }
            vec_provider.add(user_id, memory.id, embedding, vec_metadata)

        await db.commit()

        # Reload object with loaded relationships
        reload_stmt = (
            select(UserMemory)
            .where(UserMemory.id == memory.id)
            .options(selectinload(UserMemory.category), selectinload(UserMemory.tags))
        )
        res = await db.execute(reload_stmt)
        return res.scalar_one()

    @classmethod
    async def delete_memory(
        cls, db: AsyncSession, memory_id: uuid.UUID, user_id: uuid.UUID
    ) -> None:
        stmt = select(UserMemory).where(
            and_(UserMemory.id == memory_id, UserMemory.user_id == user_id)
        )
        res = await db.execute(stmt)
        memory = res.scalar_one_or_none()
        if not memory:
            raise MemoryNotFoundError()

        # Remove vector semantic memory
        try:
            vec_provider = cls.get_vector_provider()
            vec_provider.delete(user_id, memory_id)
        except Exception as e:
            logger.error(f"Error deleting vector mapping for item {memory_id}: {e}")

        # Delete database record
        await db.delete(memory)
        await db.commit()

    @classmethod
    async def archive_memory(
        cls, db: AsyncSession, memory_id: uuid.UUID, user_id: uuid.UUID
    ) -> UserMemory:
        return await cls.update_memory(db, memory_id, user_id, is_archived=True)

    @classmethod
    async def list_memories(
        cls,
        db: AsyncSession,
        user_id: uuid.UUID,
        category_name: str | None = None,
        tag_names: list[str] | None = None,
        is_archived: bool | None = False,
        skip: int = 0,
        limit: int = 100,
    ) -> list[UserMemory]:
        query = select(UserMemory).where(UserMemory.user_id == user_id)

        if is_archived is not None:
            query = query.where(UserMemory.is_archived == is_archived)

        if category_name:
            normalized_cat = category_name.strip().title()
            query = query.join(UserMemory.category).where(
                MemoryCategory.name == normalized_cat
            )

        if tag_names:
            normalized_tags = [t.strip().lower() for t in tag_names if t.strip()]
            if normalized_tags:
                query = query.join(UserMemory.tags).where(
                    MemoryTag.name.in_(normalized_tags)
                )

        query = (
            query.options(
                selectinload(UserMemory.category), selectinload(UserMemory.tags)
            )
            .order_by(UserMemory.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        res = await db.execute(query)
        return list(res.scalars().all())

    @classmethod
    async def search_memory(
        cls,
        db: AsyncSession,
        user_id: uuid.UUID,
        query: str,
        limit: int = 5,
        similarity_threshold: float = 0.5,
        category: str | None = None,
        tags: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        # Generate query embedding
        emb_provider = cls.get_embedding_provider()
        query_vector = emb_provider.generate_embedding(query)

        # Vector search top results (k=50 to allow hybrid SQL filtering post-search)
        vec_provider = cls.get_vector_provider()
        search_results = vec_provider.search(
            user_id=user_id,
            embedding=query_vector,
            k=50,
            threshold=similarity_threshold,
        )

        if not search_results:
            return []

        # Map memory ids to similarity scores
        scores_map = {uuid.UUID(res["item_id"]): res["score"] for res in search_results}

        # Query database matching scores_map memory IDs and applying SQL category/tag/archive filters
        stmt = (
            select(UserMemory)
            .where(
                and_(
                    UserMemory.id.in_(scores_map.keys()),
                    UserMemory.user_id == user_id,
                    UserMemory.is_archived.is_(False),
                )
            )
            .options(selectinload(UserMemory.category), selectinload(UserMemory.tags))
        )

        if category:
            stmt = stmt.join(UserMemory.category).where(
                MemoryCategory.name == category.strip().title()
            )

        if tags:
            tag_list = [t.strip().lower() for t in tags if t.strip()]
            if tag_list:
                stmt = stmt.join(UserMemory.tags).where(MemoryTag.name.in_(tag_list))

        db_res = await db.execute(stmt)
        memories = db_res.scalars().all()

        # Build list matching score
        results_list = []
        for mem in memories:
            score = scores_map.get(mem.id, 0.0)
            results_list.append({"memory": mem, "score": score})

        # Sort by similarity score descending
        results_list.sort(key=lambda x: x["score"], reverse=True)
        return results_list[:limit]

    @classmethod
    async def merge_duplicate_memory(
        cls,
        db: AsyncSession,
        user_id: uuid.UUID,
        memory_id_1: uuid.UUID,
        memory_id_2: uuid.UUID,
    ) -> UserMemory:
        # Load both memories
        stmt_1 = (
            select(UserMemory)
            .where(and_(UserMemory.id == memory_id_1, UserMemory.user_id == user_id))
            .options(selectinload(UserMemory.category), selectinload(UserMemory.tags))
        )
        res1 = await db.execute(stmt_1)
        mem1 = res1.scalar_one_or_none()

        stmt_2 = (
            select(UserMemory)
            .where(and_(UserMemory.id == memory_id_2, UserMemory.user_id == user_id))
            .options(selectinload(UserMemory.category), selectinload(UserMemory.tags))
        )
        res2 = await db.execute(stmt_2)
        mem2 = res2.scalar_one_or_none()

        if not mem1 or not mem2:
            raise MemoryNotFoundError(
                "One or both memory ids not found or unauthorized."
            )

        # Combine contents
        merged_content = f"{mem1.content} | {mem2.content}"

        # Combine tags
        tag_names = list(set([t.name for t in mem1.tags] + [t.name for t in mem2.tags]))

        # Combined importance score: average of the two
        merged_importance = (mem1.importance_score + mem2.importance_score) / 2.0

        # Get categories (prefer mem1 category if set, else mem2 category)
        category_name = None
        if mem1.category:
            category_name = mem1.category.name
        elif mem2.category:
            category_name = mem2.category.name

        # Update mem1 with merged fields
        await cls.update_memory(
            db=db,
            memory_id=memory_id_1,
            user_id=user_id,
            content=merged_content,
            category_name=category_name,
            tags=tag_names,
            importance_score=merged_importance,
        )

        # Delete mem2
        await cls.delete_memory(db, memory_id_2, user_id)
        await db.commit()

        # Reload updated mem1
        stmt_reload = (
            select(UserMemory)
            .where(UserMemory.id == memory_id_1)
            .options(selectinload(UserMemory.category), selectinload(UserMemory.tags))
        )
        res = await db.execute(stmt_reload)
        return res.scalar_one()

    # -------------------------------------------------------------------------
    # Short-Term Memory Cache Methods (Redis)
    # -------------------------------------------------------------------------

    @classmethod
    def _session_cache_key(cls, session_id: uuid.UUID) -> str:
        return f"session:{session_id}:cache"

    @classmethod
    async def cache_session_data(
        cls, session_id: uuid.UUID, data: dict[str, Any], ttl_seconds: int = 3600
    ) -> None:
        """
        Store session cache metadata inside Redis.
        Silently skipped when Redis is not configured.
        """
        if not redis_manager.is_configured:
            return
        try:
            client = redis_manager.get_client()
            if client is None:
                return
            key = cls._session_cache_key(session_id)
            await client.set(key, json.dumps(data), ex=ttl_seconds)
        except Exception as e:
            logger.error(f"Error caching short term session data in Redis: {e}")

    @classmethod
    async def get_cached_session_data(
        cls, session_id: uuid.UUID
    ) -> dict[str, Any] | None:
        """
        Retrieve session cache metadata from Redis.
        Returns None (cache miss) when Redis is not configured.
        """
        if not redis_manager.is_configured:
            return None
        try:
            client = redis_manager.get_client()
            if client is None:
                return None
            key = cls._session_cache_key(session_id)
            cached = await client.get(key)
            if cached:
                return json.loads(cached)
        except Exception as e:
            logger.error(f"Error fetching cached session from Redis: {e}")
        return None

    # -------------------------------------------------------------------------
    # Conversation Session / Message Methods (PostgreSQL + Redis Cache)
    # -------------------------------------------------------------------------

    @classmethod
    async def create_session(
        cls,
        db: AsyncSession,
        user_id: uuid.UUID,
        title: str | None = None,
        ttl_seconds: int | None = None,
    ) -> ConversationSession:
        expires_at = None
        if ttl_seconds:
            expires_at = datetime.now(UTC) + timedelta(seconds=ttl_seconds)

        session = ConversationSession(
            user_id=user_id,
            title=title
            or f"Conversation - {datetime.now(UTC).strftime('%Y-%m-%d %H:%M')}",
            expires_at=expires_at,
        )
        db.add(session)
        await db.commit()
        await db.refresh(session)

        # Cache session immediately
        session_data = {
            "id": str(session.id),
            "user_id": str(session.user_id),
            "title": session.title,
            "expires_at": expires_at.isoformat() if expires_at else None,
            "created_at": session.created_at.isoformat(),
        }
        await cls.cache_session_data(session.id, session_data, ttl_seconds or 3600)

        # Reload with messages
        stmt = (
            select(ConversationSession)
            .where(ConversationSession.id == session.id)
            .options(selectinload(ConversationSession.messages))
        )
        res = await db.execute(stmt)
        return res.scalar_one()

    @classmethod
    async def add_message(
        cls,
        db: AsyncSession,
        session_id: uuid.UUID,
        user_id: uuid.UUID,
        role: str,
        content: str,
    ) -> ConversationMessage:
        # Confirm session ownership
        stmt = select(ConversationSession).where(
            and_(
                ConversationSession.id == session_id,
                ConversationSession.user_id == user_id,
            )
        )
        res = await db.execute(stmt)
        session = res.scalar_one_or_none()
        if not session:
            raise SessionNotFoundError()

        # Verify session is not expired
        if session.expires_at:
            expires_at = session.expires_at
            if expires_at.tzinfo is None:
                expires_at = expires_at.replace(tzinfo=UTC)

            # Compare aware datetimes
            if expires_at < datetime.now(UTC):
                raise SessionNotFoundError("Conversation session has expired.")

        msg = ConversationMessage(
            session_id=session_id,
            role=role,
            content=content,
        )
        db.add(msg)
        await db.commit()
        await db.refresh(msg)

        # Evict / refresh cached session data to keep cache coherent
        cached = await cls.get_cached_session_data(session_id)
        if cached:
            # Re-cache with updated messages
            # For simplicity, we can extend the TTL by default duration or keep original
            ttl = 3600
            if session.expires_at:
                delta = session.expires_at - datetime.now(UTC)
                ttl = int(delta.total_seconds())
                if ttl <= 0:
                    ttl = 1

            await cls.cache_session_data(session_id, cached, ttl)

        return msg

    @classmethod
    async def get_session(
        cls, db: AsyncSession, session_id: uuid.UUID, user_id: uuid.UUID
    ) -> ConversationSession:
        stmt = (
            select(ConversationSession)
            .where(
                and_(
                    ConversationSession.id == session_id,
                    ConversationSession.user_id == user_id,
                )
            )
            .options(selectinload(ConversationSession.messages))
        )
        res = await db.execute(stmt)
        session = res.scalar_one_or_none()
        if not session:
            raise SessionNotFoundError()
        return session

    @classmethod
    async def summarize_conversation(
        cls, db: AsyncSession, session_id: uuid.UUID, user_id: uuid.UUID
    ) -> ConversationSummary:
        # Enforce ownership and load session with messages
        stmt = (
            select(ConversationSession)
            .where(
                and_(
                    ConversationSession.id == session_id,
                    ConversationSession.user_id == user_id,
                )
            )
            .options(selectinload(ConversationSession.messages))
        )
        res = await db.execute(stmt)
        session = res.scalar_one_or_none()
        if not session:
            raise SessionNotFoundError()

        # Refresh messages to ensure freshly added messages are loaded
        await db.refresh(session, ["messages"])

        messages = session.messages
        if not messages:
            summary_text = "No conversation messages available to summarize."
        else:
            # Concise summary heuristics: list user prompts / general overview
            user_inputs = [msg.content for msg in messages if msg.role == "user"]
            topic_keywords = []
            for text in user_inputs:
                words = [
                    w
                    for w in text.split()
                    if len(w) > 4
                    and w.lower() not in {"about", "there", "their", "would"}
                ]
                topic_keywords.extend(words[:3])

            topic_str = ", ".join(list(set(topic_keywords))[:5])
            summary_text = (
                f"Summary of {len(messages)} messages. "
                f"Discussion topics mentioned: {topic_str if topic_str else 'General chat'}."
            )

        summary = ConversationSummary(session_id=session_id, summary=summary_text)
        db.add(summary)
        await db.commit()
        await db.refresh(summary)

        # Cache summary to Redis (silently skipped when Redis is not configured)
        if redis_manager.is_configured:
            try:
                client = redis_manager.get_client()
                if client is not None:
                    summary_key = f"session:{session_id}:summary"
                    await client.set(summary_key, summary_text, ex=7200)  # 2 hours cache
            except Exception as e:
                logger.error(f"Error caching session summary: {e}")

        return summary
