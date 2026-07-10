"""Assistant exceptions mapped to HTTP responses."""

from app.core.exceptions.custom import AppException


class AssistantException(AppException):
    """Base exception for assistant-related issues."""

    def __init__(
        self,
        message: str = "Assistant processing failed.",
        status_code: int = 500,
    ) -> None:
        super().__init__(status_code=status_code, message=message)
