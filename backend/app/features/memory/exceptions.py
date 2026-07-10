from app.core.exceptions.custom import NotFoundError


class MemoryNotFoundError(NotFoundError):
    """
    Exception raised when a specific memory resource is not found or does not belong to the user.
    """

    def __init__(self, message: str = "Memory resource not found.") -> None:
        super().__init__(message=message)


class SessionNotFoundError(NotFoundError):
    """
    Exception raised when a specific conversation session is not found or does not belong to the user.
    """

    def __init__(self, message: str = "Conversation session not found.") -> None:
        super().__init__(message=message)


class CategoryNotFoundError(NotFoundError):
    """
    Exception raised when a category is not found.
    """

    def __init__(self, message: str = "Memory category not found.") -> None:
        super().__init__(message=message)
