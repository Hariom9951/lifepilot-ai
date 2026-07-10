"""
Text extraction service supporting PDF, DOCX, TXT, and Markdown files.
Follows the Single Responsibility Principle — one class per concern.
"""
import logging
from pathlib import Path

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
        """
        Extract and return raw text content from a file.

        Args:
            file_path: Absolute path to the stored file.
            mime_type: MIME type string used to select the extractor strategy.

        Returns:
            Extracted plain text content.

        Raises:
            ValueError: If MIME type is not supported.
            RuntimeError: If extraction fails.
        """
        strategy = SUPPORTED_MIME_TYPES.get(mime_type)
        if strategy is None:
            raise ValueError(f"Unsupported MIME type for extraction: {mime_type}")

        logger.info(f"Extracting text from {file_path.name} using strategy: {strategy}")

        try:
            if strategy == "pdf":
                return self._extract_pdf(file_path)
            elif strategy == "docx":
                return self._extract_docx(file_path)
            else:
                return self._extract_text(file_path)
        except Exception as exc:
            logger.exception(f"Text extraction failed for {file_path.name}: {exc}")
            raise RuntimeError(f"Text extraction failed: {exc}") from exc

    def _extract_pdf(self, file_path: Path) -> str:
        """Extract text from a PDF file using pypdf."""
        import pypdf  # Lazy import to avoid startup cost

        text_parts: list[str] = []
        with open(file_path, "rb") as f:
            reader = pypdf.PdfReader(f)
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text.strip())

        return "\n\n".join(text_parts)

    def _extract_docx(self, file_path: Path) -> str:
        """Extract text from a DOCX file using python-docx."""
        import docx  # Lazy import

        document = docx.Document(str(file_path))
        paragraphs = [p.text.strip() for p in document.paragraphs if p.text.strip()]
        return "\n\n".join(paragraphs)

    def _extract_text(self, file_path: Path) -> str:
        """Read plain text / Markdown files with UTF-8 encoding."""
        return file_path.read_text(encoding="utf-8", errors="replace")


# Module-level singleton
text_extractor = TextExtractor()
