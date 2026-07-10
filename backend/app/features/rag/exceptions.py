from app.core.exceptions.custom import AppException


class RAGException(AppException):
    """Base exception class for RAG features."""

    def __init__(
        self, message: str = "RAG processing failed.", status_code: int = 500
    ) -> None:
        super().__init__(status_code=status_code, message=message)


class DocumentIngestionError(RAGException):
    """Exception raised when document ingestion or chunking fails."""

    def __init__(self, message: str = "Failed to ingest document.") -> None:
        super().__init__(message=message, status_code=400)
