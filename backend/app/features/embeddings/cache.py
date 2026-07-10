import hashlib
import logging
import uuid

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config.settings import settings
from app.features.embeddings.models import EmbeddingCache

logger = logging.getLogger("app.embeddings.cache")


class EmbeddingCacheManager:
    """
    Manager for computing content hashes and querying/saving to database cache.
    """

    @staticmethod
    def get_hash(text: str) -> str:
        """Computes SHA-256 hash of text."""
        return hashlib.sha256(text.encode("utf-8")).hexdigest()

    @classmethod
    async def get_cached_embedding(
        cls, db: AsyncSession, text: str, model_name: str
    ) -> list[float] | None:
        """
        Retrieves cached embedding for text and model if cache is enabled.
        """
        if not getattr(settings, "EMBEDDING_CACHE_ENABLED", True):
            return None

        text_hash = cls.get_hash(text)
        stmt = select(EmbeddingCache.embedding).where(
            and_(
                EmbeddingCache.text_hash == text_hash,
                EmbeddingCache.model_name == model_name,
            )
        )
        res = await db.execute(stmt)
        return res.scalar_one_or_none()

    @classmethod
    async def get_bulk_cached_embeddings(
        cls, db: AsyncSession, texts: list[str], model_name: str
    ) -> dict[str, list[float]]:
        """
        Bulk retrieves cached embeddings for list of texts to minimize database roundtrips.
        """
        if not texts or not getattr(settings, "EMBEDDING_CACHE_ENABLED", True):
            return {}

        hash_to_text = {cls.get_hash(t): t for t in texts}
        hashes = list(hash_to_text.keys())

        stmt = select(EmbeddingCache.text_hash, EmbeddingCache.embedding).where(
            and_(
                EmbeddingCache.text_hash.in_(hashes),
                EmbeddingCache.model_name == model_name,
            )
        )
        res = await db.execute(stmt)

        cached_results = {}
        for text_hash, embedding in res.all():
            original_text = hash_to_text.get(text_hash)
            if original_text:
                cached_results[original_text] = embedding

        return cached_results

    @classmethod
    async def save_embedding(
        cls, db: AsyncSession, text: str, embedding: list[float], model_name: str
    ) -> None:
        """
        Saves computed embedding to cache.
        """
        if not getattr(settings, "EMBEDDING_CACHE_ENABLED", True):
            return

        text_hash = cls.get_hash(text)
        cache_data = {
            "id": uuid.uuid4(),
            "text_hash": text_hash,
            "model_name": model_name,
            "embedding": embedding,
        }

        # Check if already exists to avoid unique constraint violations
        stmt = select(EmbeddingCache.id).where(
            and_(
                EmbeddingCache.text_hash == text_hash,
                EmbeddingCache.model_name == model_name,
            )
        )
        existing = await db.execute(stmt)
        if existing.scalar_one_or_none():
            return

        db_item = EmbeddingCache(**cache_data)
        db.add(db_item)
        await db.flush()

    @classmethod
    async def save_bulk_embeddings(
        cls,
        db: AsyncSession,
        texts: list[str],
        embeddings: list[list[float]],
        model_name: str,
    ) -> None:
        """
        Saves bulk computed embeddings to database.
        """
        if not texts or not getattr(settings, "EMBEDDING_CACHE_ENABLED", True):
            return

        # Fetch existing hashes in database to filter out duplicates
        hash_to_text_emb = {
            cls.get_hash(t): (t, e) for t, e in zip(texts, embeddings, strict=False)
        }
        hashes = list(hash_to_text_emb.keys())

        stmt = select(EmbeddingCache.text_hash).where(
            and_(
                EmbeddingCache.text_hash.in_(hashes),
                EmbeddingCache.model_name == model_name,
            )
        )
        res = await db.execute(stmt)
        existing_hashes = set(res.scalars().all())

        new_items = []
        for text_hash, (_text, emb) in hash_to_text_emb.items():
            if text_hash not in existing_hashes:
                new_items.append(
                    EmbeddingCache(
                        id=uuid.uuid4(),
                        text_hash=text_hash,
                        model_name=model_name,
                        embedding=emb,
                    )
                )

        if new_items:
            db.add_all(new_items)
            await db.flush()
            logger.info(f"Cached {len(new_items)} new embeddings in database.")

    @classmethod
    async def clear_cache(cls, db: AsyncSession) -> int:
        """
        Clears the embedding cache table.
        """
        from sqlalchemy import delete

        stmt = delete(EmbeddingCache)
        res = await db.execute(stmt)
        await db.flush()
        return res.rowcount
