from app.core.exceptions.custom import AppException


class DocumentNotFoundError(AppException):
    """Raised when a document record does not exist or belongs to another user."""

    def __init__(self, message: str = "Document not found.") -> None:
        super().__init__(status_code=404, message=message)


class UnsupportedFileTypeError(AppException):
    """Raised when an upload MIME type is not in the accepted list."""

    def __init__(self, message: str = "File type is not supported.") -> None:
        super().__init__(status_code=415, message=message)


class FileTooLargeError(AppException):
    """Raised when uploaded file exceeds the configured size limit."""

    def __init__(self, message: str = "File exceeds maximum allowed size.") -> None:
        super().__init__(status_code=413, message=message)


class ProcessingError(AppException):
    """Raised when document processing pipeline encounters a fatal error."""

    def __init__(self, message: str = "Document processing failed.") -> None:
        super().__init__(status_code=500, message=message)
