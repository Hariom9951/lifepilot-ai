from typing import Any, Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class SuccessResponse(BaseModel, Generic[T]):
    """
    Standard generic success API response template.
    """

    success: bool = Field(default=True)
    message: str = Field(default="Operation completed successfully.")
    data: T | None = Field(default=None)


class ErrorDetails(BaseModel):
    """
    Validation or processing error details.
    """

    loc: list[str] | None = None
    msg: str
    type: str


class ErrorResponse(BaseModel):
    """
    Standard error API response template.
    """

    success: bool = Field(default=False)
    message: str = Field(default="An error occurred processing the request.")
    errors: list[ErrorDetails] | list[str] | Any = Field(default_factory=list)
