from typing import Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class PaginationParams(BaseModel):
    """
    Standard pagination query parameters schema.
    """

    page: int = Field(default=1, ge=1, description="Page index (1-based)")
    limit: int = Field(default=20, ge=1, le=100, description="Items per page limit")

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.limit


class PageMetadata(BaseModel):
    """
    Pagination metadata for list responses.
    """

    total: int
    page: int
    limit: int
    pages: int


class PagedResponse(BaseModel, Generic[T]):
    """
    Paged list success API response template wrapper.
    """

    items: list[T]
    metadata: PageMetadata
