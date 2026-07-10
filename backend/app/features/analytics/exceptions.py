"""Analytics module custom exceptions."""

from app.core.exceptions.custom import AppException


class AnalyticsDataUnavailableError(AppException):
    def __init__(
        self,
        message: str = "Analytics data is not available for this user yet.",
    ) -> None:
        super().__init__(status_code=404, message=message)
