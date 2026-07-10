"""
Text extraction service supporting PDF, DOCX, TXT, and Markdown files.
Follows the Single Responsibility Principle — one class per concern.
"""

import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger("app.knowledge.extractor")

# Supported MIME types mapped to extraction strategy keys
SUPPORTED_MIME_TYPES: dict[str, str] = {
    "application/pdf": "pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "docx",
    "text/plain": "text",
    "text/markdown": "text",
    "text/x-markdown": "text",
}


class TextExtractor:
    """
    Stateless service that extracts raw text from uploaded documents.
    Dispatches extraction logic based on MIME type.
    """

    def extract(self, file_path: Path, mime_type: str) -> str:
        text, _ = self.extract_with_metadata(file_path, mime_type)
        return text

    def extract_with_metadata(
        self, file_path: Path, mime_type: str
    ) -> tuple[str, dict[str, Any]]:
        """
        Extract text and metadata (title, author, page count, word count, character count).
        """
        strategy = SUPPORTED_MIME_TYPES.get(mime_type)
        if strategy is None:
            raise ValueError(f"Unsupported MIME type for extraction: {mime_type}")

        logger.info(
            f"Extracting text/metadata from {file_path.name} using strategy: {strategy}"
        )

        try:
            if strategy == "pdf":
                return self._extract_pdf_with_meta(file_path)
            elif strategy == "docx":
                return self._extract_docx_with_meta(file_path)
            else:
                return self._extract_text_with_meta(file_path)
        except Exception as exc:
            logger.exception(
                f"Text/metadata extraction failed for {file_path.name}: {exc}"
            )
            raise RuntimeError(f"Text extraction failed: {exc}") from exc

    def _extract_pdf_with_meta(self, file_path: Path) -> tuple[str, dict[str, Any]]:
        import pypdf

        text_parts = []
        meta = {"page_count": 0, "title": "", "author": ""}
        with open(file_path, "rb") as f:
            reader = pypdf.PdfReader(f)
            meta["page_count"] = len(reader.pages)
            if reader.metadata:
                meta["title"] = str(reader.metadata.get("/Title") or "")
                meta["author"] = str(reader.metadata.get("/Author") or "")
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text.strip())

        text = "\n\n".join(text_parts)
        meta["word_count"] = len(text.split())
        meta["character_count"] = len(text)
        return text, meta

    def _extract_docx_with_meta(self, file_path: Path) -> tuple[str, dict[str, Any]]:
        import docx

        doc = docx.Document(str(file_path))
        paragraphs = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
        text = "\n\n".join(paragraphs)
        meta = {
            "page_count": max(1, len(paragraphs) // 15),
            "title": str(doc.core_properties.title or ""),
            "author": str(doc.core_properties.author or ""),
            "word_count": len(text.split()),
            "character_count": len(text),
        }
        return text, meta

    def _extract_text_with_meta(self, file_path: Path) -> tuple[str, dict[str, Any]]:
        text = file_path.read_text(encoding="utf-8", errors="replace")
        meta = {
            "page_count": 1,
            "title": file_path.stem,
            "author": "Unknown",
            "word_count": len(text.split()),
            "character_count": len(text),
        }
        return text, meta


# Module-level singleton
text_extractor = TextExtractor()
