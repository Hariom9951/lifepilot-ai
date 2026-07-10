from typing import Any


class AppException(Exception):
    """
    Base class for all custom application exceptions.
    """

    def __init__(
        self, status_code: int, message: str, errors: Any | None = None
    ) -> None:
        self.status_code = status_code
        self.message = message
        self.errors = errors or []
        super().__init__(message)


class NotFoundError(AppException):
    def __init__(
        self, message: str = "Resource not found.", errors: Any | None = None
    ) -> None:
        super().__init__(status_code=404, message=message, errors=errors)


class ConflictError(AppException):
    def __init__(
        self, message: str = "Resource conflict occurred.", errors: Any | None = None
    ) -> None:
        super().__init__(status_code=409, message=message, errors=errors)


class UnauthorizedError(AppException):
    def __init__(
        self, message: str = "Authentication failed.", errors: Any | None = None
    ) -> None:
        super().__init__(status_code=401, message=message, errors=errors)


class ForbiddenError(AppException):
    def __init__(
        self, message: str = "Permission denied.", errors: Any | None = None
    ) -> None:
        super().__init__(status_code=403, message=message, errors=errors)


class ValidationError(AppException):
    def __init__(
        self, message: str = "Validation failed.", errors: Any | None = None
    ) -> None:
        super().__init__(status_code=422, message=message, errors=errors)


class DatabaseError(AppException):
    def __init__(
        self,
        message: str = "Database transaction failed.",
        errors: Any | None = None,
    ) -> None:
        super().__init__(status_code=500, message=message, errors=errors)


class InternalServerError(AppException):
    def __init__(
        self,
        message: str = "Internal server error occurred.",
        errors: Any | None = None,
    ) -> None:
        super().__init__(status_code=500, message=message, errors=errors)
