import uuid
from datetime import UTC, datetime
from typing import Any


class RAGChunker:
    """Helper class to parse and chunk texts with preserved metadata attributes."""

    @staticmethod
    def chunk_document(
        text: str,
        chunk_size: int = 512,
        chunk_overlap: int = 64,
        source: str = "",
        document_id: uuid.UUID | None = None,
        metadata: dict[str, Any] | None = None,
        timestamp: datetime | None = None,
    ) -> list[dict[str, Any]]:
        """
        Chunk text segment and map with document IDs, source pathways, and timestamps.
        """
        from app.features.knowledge.processing.chunker import RecursiveChunker

        size = chunk_size if chunk_size > 0 else 512
        overlap = chunk_overlap if chunk_overlap >= 0 else 64
        if overlap >= size:
            overlap = size // 2

        chunker = RecursiveChunker(chunk_size=size, chunk_overlap=overlap)
        text_chunks = chunker.chunk(text)

        chunks_payload = []
        for i, chunk_text in enumerate(text_chunks):
            chunks_payload.append(
                {
                    "id": uuid.uuid4(),
                    "content": chunk_text,
                    "document_id": document_id,
                    "source": source,
                    "metadata": {
                        **(metadata or {}),
                        "document_id": str(document_id) if document_id else "",
                        "source": source,
                        "chunk_index": i,
                        "timestamp": (timestamp or datetime.now(UTC)).isoformat(),
                    },
                }
            )
        return chunks_payload
