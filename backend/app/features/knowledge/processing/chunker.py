import logging
import re
from abc import ABC, abstractmethod
from enum import Enum

logger = logging.getLogger("app.knowledge.chunker")


class ChunkingStrategy(str, Enum):
    FIXED = "fixed"
    RECURSIVE = "recursive"
    PARAGRAPH = "paragraph"
    SENTENCE = "sentence"


class BaseChunker(ABC):
    """
    Abstract base class for chunking engines.
    """

    def __init__(self, chunk_size: int = 512, chunk_overlap: int = 64) -> None:
        if chunk_size <= 0:
            raise ValueError("chunk_size must be positive.")
        if chunk_overlap < 0 or chunk_overlap >= chunk_size:
            raise ValueError("chunk_overlap must be >= 0 and < chunk_size.")

        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    @abstractmethod
    def chunk(self, text: str) -> list[str]:
        """
        Split a string into list of text chunks.
        """
        pass


class FixedSizeChunker(BaseChunker):
    """
    Splits text using word-aligned sliding window of size and overlap.
    """

    def chunk(self, text: str) -> list[str]:
        if not text or not text.strip():
            return []

        text = text.strip()
        chunks: list[str] = []
        start = 0
        text_len = len(text)

        while start < text_len:
            end = min(start + self.chunk_size, text_len)

            # Extend to next word boundary if not at end of text
            if end < text_len:
                boundary = text.rfind(" ", start, end)
                if boundary > start:
                    end = boundary

            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)

            step = self.chunk_size - self.chunk_overlap
            start += max(step, 1)

        return chunks


class RecursiveChunker(BaseChunker):
    """
    Splits text recursively by separators: paragraphs, lines, words, then characters.
    """

    def __init__(
        self,
        chunk_size: int = 512,
        chunk_overlap: int = 64,
        separators: list[str] | None = None,
    ) -> None:
        super().__init__(chunk_size, chunk_overlap)
        self.separators = separators or ["\n\n", "\n", " ", ""]

    def chunk(self, text: str) -> list[str]:
        return self._split_text(text, self.separators)

    def _split_text(self, text: str, separators: list[str]) -> list[str]:
        if not text or not text.strip():
            return []

        # Find current separator
        separator = separators[-1]
        for sep in separators:
            if sep == "":
                separator = sep
                break
            if sep in text:
                separator = sep
                break

        # Split text by separator
        splits = text.split(separator) if separator != "" else list(text)
        splits = [s.strip() for s in splits if s.strip()]

        chunks: list[str] = []
        current_chunk: list[str] = []
        current_length = 0

        for split in splits:
            split_len = len(split)
            # If a single split exceeds chunk_size, split it recursively using remaining separators
            if split_len > self.chunk_size:
                if len(separators) > 1:
                    remaining_seps = [s for s in separators if s != separator]
                    sub_chunks = self._split_text(split, remaining_seps)
                    for sc in sub_chunks:
                        chunks.append(sc)
                else:
                    # Last separator, force truncate
                    chunks.append(split[: self.chunk_size])
                continue

            # Check if adding split exceeds chunk size
            if (
                current_length + split_len + (len(separator) if current_chunk else 0)
                > self.chunk_size
            ):
                if current_chunk:
                    chunks.append(separator.join(current_chunk))
                # Create overlap buffer from existing chunk if overlap is configured
                overlap_buffer: list[str] = []
                overlap_len = 0
                for item in reversed(current_chunk):
                    if (
                        overlap_len
                        + len(item)
                        + (len(separator) if overlap_buffer else 0)
                        <= self.chunk_overlap
                    ):
                        overlap_buffer.insert(0, item)
                        overlap_len += len(item) + len(separator)
                    else:
                        break
                current_chunk = overlap_buffer + [split]
                current_length = sum(len(x) for x in current_chunk) + (
                    len(separator) * (len(current_chunk) - 1)
                )
            else:
                current_chunk.append(split)
                current_length += split_len + (
                    len(separator) if len(current_chunk) > 1 else 0
                )

        if current_chunk:
            chunks.append(separator.join(current_chunk))

        return [c.strip() for c in chunks if c.strip()]


class ParagraphChunker(BaseChunker):
    """
    Splits text by paragraphs (\n\n). Groups consecutive paragraphs under chunk_size.
    """

    def chunk(self, text: str) -> list[str]:
        if not text or not text.strip():
            return []

        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
        chunks: list[str] = []
        current_chunk = []
        current_len = 0

        for p in paragraphs:
            p_len = len(p)
            if p_len > self.chunk_size:
                # If a single paragraph is too large, use fallback fixed chunking on it
                if current_chunk:
                    chunks.append("\n\n".join(current_chunk))
                    current_chunk = []
                    current_len = 0
                fallback = FixedSizeChunker(self.chunk_size, self.chunk_overlap)
                chunks.extend(fallback.chunk(p))
                continue

            if current_len + p_len + (2 if current_chunk else 0) > self.chunk_size:
                if current_chunk:
                    chunks.append("\n\n".join(current_chunk))
                current_chunk = [p]
                current_len = p_len
            else:
                current_chunk.append(p)
                current_len += p_len + (2 if len(current_chunk) > 1 else 0)

        if current_chunk:
            chunks.append("\n\n".join(current_chunk))

        return chunks


class SentenceChunker(BaseChunker):
    """
    Splits text by sentences. Groups consecutive sentences under chunk_size.
    """

    def chunk(self, text: str) -> list[str]:
        if not text or not text.strip():
            return []

        # Simple sentence boundary regex (looks for ., !, ? followed by space and capital letter)
        sentences = re.split(r"(?<=[.!?])\s+", text.strip())
        sentences = [s.strip() for s in sentences if s.strip()]

        chunks: list[str] = []
        current_chunk = []
        current_len = 0

        for s in sentences:
            s_len = len(s)
            if s_len > self.chunk_size:
                # If a sentence is too large, use fallback fixed chunking
                if current_chunk:
                    chunks.append(" ".join(current_chunk))
                    current_chunk = []
                    current_len = 0
                fallback = FixedSizeChunker(self.chunk_size, self.chunk_overlap)
                chunks.extend(fallback.chunk(s))
                continue

            if current_len + s_len + (1 if current_chunk else 0) > self.chunk_size:
                if current_chunk:
                    chunks.append(" ".join(current_chunk))
                current_chunk = [s]
                current_len = s_len
            else:
                current_chunk.append(s)
                current_len += s_len + (1 if len(current_chunk) > 1 else 0)

        if current_chunk:
            chunks.append(" ".join(current_chunk))

        return chunks


def get_chunker(
    strategy: ChunkingStrategy, chunk_size: int, chunk_overlap: int
) -> BaseChunker:
    """
    Factory to return a chunker instance based on strategy type.
    """
    if strategy == ChunkingStrategy.RECURSIVE:
        return RecursiveChunker(chunk_size, chunk_overlap)
    elif strategy == ChunkingStrategy.PARAGRAPH:
        return ParagraphChunker(chunk_size, chunk_overlap)
    elif strategy == ChunkingStrategy.SENTENCE:
        return SentenceChunker(chunk_size, chunk_overlap)
    else:
        return FixedSizeChunker(chunk_size, chunk_overlap)
