import logging
import time
from typing import Any

import torch

from app.features.embeddings.providers import (
    MODEL_DIMENSIONS,
    SentenceTransformersProvider,
    get_device,
)

logger = logging.getLogger("app.embeddings.benchmarks")


def run_benchmark(sample_texts: list[str] | None = None) -> list[dict[str, Any]]:
    """
    Benchmarks speed, latency, dimensions, and memory usage across all 4 production models.
    """
    if not sample_texts:
        sample_texts = [
            "LifePilot AI remembers users across conversations.",
            "Retrieval-Augmented Generation processes documents like PDF and Word files.",
            "Vector databases flat indexes perform hybrid metadata filtering similarity calculations.",
            "Enterprise modular clean code requires high test coverage and observability metrics.",
        ]

    results = []
    device = get_device()

    logger.info(f"Starting embeddings benchmark on active device: {device}")

    for model_name in MODEL_DIMENSIONS.keys():
        logger.info(f"Benchmarking model: {model_name}")

        # Track VRAM before loading
        vram_before = 0.0
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            vram_before = torch.cuda.memory_allocated() / (1024 * 1024)

        start_load = time.perf_counter()
        try:
            provider = SentenceTransformersProvider(model_name=model_name)
            # Force load model
            provider._load_model()
            load_time_ms = (time.perf_counter() - start_load) * 1000

            # Track VRAM after loading
            vram_after = 0.0
            if torch.cuda.is_available():
                vram_after = torch.cuda.memory_allocated() / (1024 * 1024)
            memory_usage_mb = max(0.0, vram_after - vram_before)

            # Benchmark single encoding latency
            latencies = []
            for text in sample_texts:
                t0 = time.perf_counter()
                provider.generate_embedding(text)
                latencies.append((time.perf_counter() - t0) * 1000)
            avg_single_latency_ms = sum(latencies) / len(latencies)

            # Benchmark batch encoding throughput
            t0 = time.perf_counter()
            provider.batch_embedding(sample_texts)
            batch_time_ms = (time.perf_counter() - t0) * 1000
            throughput_texts_per_sec = len(sample_texts) / (batch_time_ms / 1000)

            results.append(
                {
                    "model_name": model_name,
                    "dimension": provider.get_dimension(),
                    "device": device,
                    "load_time_ms": load_time_ms,
                    "memory_vram_usage_mb": memory_usage_mb,
                    "avg_single_latency_ms": avg_single_latency_ms,
                    "batch_throughput_texts_per_sec": throughput_texts_per_sec,
                    "status": "success",
                }
            )
        except Exception as e:
            logger.error(f"Failed to benchmark model {model_name}: {e}")
            results.append(
                {
                    "model_name": model_name,
                    "dimension": MODEL_DIMENSIONS[model_name],
                    "device": device,
                    "load_time_ms": 0.0,
                    "memory_vram_usage_mb": 0.0,
                    "avg_single_latency_ms": 0.0,
                    "batch_throughput_texts_per_sec": 0.0,
                    "status": f"failed: {e}",
                }
            )

    return results
