"""
Configurable sliding-window text chunker for the RAG pipeline.
"""

import logging

logger = logging.getLogger("app.knowledge.chunker")


class TextChunker:
    """
    Splits a long text into overlapping chunks suitable for embedding.

    Chunk boundaries are word-aligned to avoid splitting mid-word.
    Overlap is measured in characters to ensure context continuity.
    """

    def __init__(self, chunk_size: int = 512, chunk_overlap: int = 64) -> None:
        """
        Args:
            chunk_size: Maximum character length of each chunk.
            chunk_overlap: Number of overlap characters between consecutive chunks.
        """
        if chunk_size <= 0:
            raise ValueError("chunk_size must be a positive integer.")
        if chunk_overlap < 0 or chunk_overlap >= chunk_size:
            raise ValueError("chunk_overlap must be >= 0 and < chunk_size.")

        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def chunk(self, text: str) -> list[str]:
        """
        Split text into overlapping chunks.

        Args:
            text: Raw extracted text to be chunked.

        Returns:
            List of non-empty text chunk strings.
        """
        if not text or not text.strip():
            return []

        text = text.strip()
        chunks: list[str] = []
        start = 0
        text_len = len(text)

        while start < text_len:
            end = min(start + self.chunk_size, text_len)

            # Extend to the next word boundary if not at end of text
            if end < text_len:
                boundary = text.rfind(" ", start, end)
                if boundary > start:
                    end = boundary

            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)

            # Step forward by (chunk_size - chunk_overlap) to create sliding window
            step = self.chunk_size - self.chunk_overlap
            start += max(step, 1)

        logger.debug(f"Chunked text ({text_len} chars) into {len(chunks)} chunks.")
        return chunks


def build_chunker_from_settings() -> TextChunker:
    """Factory that instantiates a TextChunker from application settings."""
    from app.core.config.settings import settings

    return TextChunker(
        chunk_size=settings.KNOWLEDGE_CHUNK_SIZE,
        chunk_overlap=settings.KNOWLEDGE_CHUNK_OVERLAP,
    )
