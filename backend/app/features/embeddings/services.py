import hashlib
import logging
import math
import time
from typing import Any

import torch
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config.settings import settings
from app.features.embeddings.cache import EmbeddingCacheManager
from app.features.embeddings.providers import get_active_provider

logger = logging.getLogger("app.embeddings.services")

# Local metrics tracking
_metrics = {
    "total_requests": 0,
    "total_texts_processed": 0,
    "cache_hits": 0,
    "cache_misses": 0,
    "total_latency_ms": 0.0,
}


def dot_product(a: list[float], b: list[float]) -> float:
    """Calculates the dot product between two vectors."""
    return sum(x * y for x, y in zip(a, b, strict=False))


def cosine_similarity(a: list[float], b: list[float]) -> float:
    """Calculates the cosine similarity between two vectors."""
    numerator = dot_product(a, b)
    denominator_a = math.sqrt(sum(x * x for x in a))
    denominator_b = math.sqrt(sum(x * x for x in b))
    if denominator_a == 0 or denominator_b == 0:
        return 0.0
    return numerator / (denominator_a * denominator_b)


class EmbeddingEngineService:
    """
    Core orchestrator managing embedding caching, batching, similarity search math, and execution metrics.
    """

    @classmethod
    async def generate_embeddings(
        cls, db: AsyncSession, texts: list[str]
    ) -> list[list[float]]:
        """
        Retrieves cached embeddings or generates new vectors in batches.
        Updates cache hits/misses, text statistics, and latency metrics.
        """
        if not texts:
            return []

        start_time = time.perf_counter()
        provider = get_active_provider()
        model_name = provider.model_name

        # 1. Fetch from Cache
        cache_hits = await EmbeddingCacheManager.get_bulk_cached_embeddings(
            db, texts, model_name
        )

        missing_texts = []
        for text in texts:
            if text not in cache_hits:
                missing_texts.append(text)

        # 2. Update Cache Metrics
        _metrics["total_requests"] += 1
        _metrics["total_texts_processed"] += len(texts)
        _metrics["cache_hits"] += len(texts) - len(missing_texts)
        _metrics["cache_misses"] += len(missing_texts)

        # 3. Generate Missing Embeddings (Batched & Streamed)
        generated_embeddings = []
        if missing_texts:
            logger.info(
                f"Generating embeddings for {len(missing_texts)} missing cache lines."
            )
            # Set batch size from settings or default
            batch_size = getattr(settings, "EMBEDDING_BATCH_SIZE", 32)

            # Stream/Yield progressive batches
            for batch_vectors in provider.stream_embeddings(missing_texts, batch_size):
                generated_embeddings.extend(batch_vectors)

            # Persist newly generated embeddings to cache
            await EmbeddingCacheManager.save_bulk_embeddings(
                db, missing_texts, generated_embeddings, model_name
            )

        # 4. Map back to original order
        missing_index = 0
        final_embeddings = []
        for text in texts:
            if text in cache_hits:
                final_embeddings.append(cache_hits[text])
            else:
                final_embeddings.append(generated_embeddings[missing_index])
                missing_index += 1

        # Track latency
        latency_ms = (time.perf_counter() - start_time) * 1000
        _metrics["total_latency_ms"] += latency_ms

        logger.info(
            f"Generated {len(texts)} embeddings (Hits: {len(texts) - len(missing_texts)}/Misses: {len(missing_texts)}) "
            f"in {latency_ms:.2f}ms"
        )
        return final_embeddings

    @classmethod
    def get_metrics(cls) -> dict[str, Any]:
        """
        Gathers runtime cache hit rates, average latencies, and active GPU utilization details.
        """
        # Calculate Cache Hit Ratio
        total = _metrics["cache_hits"] + _metrics["cache_misses"]
        hit_ratio = (_metrics["cache_hits"] / total) if total > 0 else 0.0

        # Calculate Average Latency
        avg_latency = (
            (_metrics["total_latency_ms"] / _metrics["total_requests"])
            if _metrics["total_requests"] > 0
            else 0.0
        )

        gpu_info = {"vram_allocated_mb": 0.0, "vram_cached_mb": 0.0, "device_name": ""}
        if torch.cuda.is_available():
            gpu_info["vram_allocated_mb"] = torch.cuda.memory_allocated() / (
                1024 * 1024
            )
            gpu_info["vram_cached_mb"] = torch.cuda.memory_reserved() / (1024 * 1024)
            gpu_info["device_name"] = torch.cuda.get_device_name(0)

        provider = get_active_provider()

        return {
            "active_provider": provider.model_name,
            "device": provider.get_device(),
            "dimension": provider.get_dimension(),
            "total_requests": _metrics["total_requests"],
            "total_texts_processed": _metrics["total_texts_processed"],
            "cache_hit_ratio": hit_ratio,
            "average_latency_ms": avg_latency,
            "gpu": gpu_info,
        }

    # -------------------------------------------------------------------------
    # Semantic Search Engine
    # -------------------------------------------------------------------------

    @classmethod
    def semantic_search(
        cls,
        query_embedding: list[float],
        candidates: list[dict[str, Any]],
        limit: int = 5,
        score_threshold: float = 0.5,
        metric: str = "cosine",
        metadata_filter: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """
        Calculates similarity scoring, prunes via threshold, removes duplicates, and filters metadata.
        """
        results = []
        seen_contents = set()

        for item in candidates:
            item_vector = item.get("embedding")
            if not item_vector:
                continue

            # Calculate score based on metric
            if metric == "dot_product":
                score = dot_product(query_embedding, item_vector)
            else:
                score = cosine_similarity(query_embedding, item_vector)

            # Apply score threshold filter
            if score < score_threshold:
                continue

            # Apply metadata filters
            metadata = item.get("metadata", {})
            if metadata_filter:
                match = True
                for k, v in metadata_filter.items():
                    if metadata.get(k) != v:
                        match = False
                        break
                if not match:
                    continue

            # Apply duplicate content filtering (checking text chunk if present)
            content = item.get("text") or item.get("content") or ""
            if content:
                content_hash = (
                    hashlib.sha256(content.encode("utf-8")).hexdigest()
                    if isinstance(content, str)
                    else str(content)
                )
                if content_hash in seen_contents:
                    continue
                seen_contents.add(content_hash)

            # Store result
            res_item = {**item}
            # Remove embedding vector from output payload to save bandwidth
            if "embedding" in res_item:
                del res_item["embedding"]
            res_item["score"] = score
            results.append(res_item)

        # Sort descending by score and slice by limit
        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:limit]
