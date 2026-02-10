from typing import Generic, List, Optional, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class StandardResponse(BaseModel, Generic[T]):
    success: bool
    message: str
    data: Optional[T] = None
    errors: Optional[List[str]] = None

    @classmethod
    def ok(cls, data: T = None, message: str = "Success") -> "StandardResponse[T]":
        return cls(success=True, message=message, data=data)

    @classmethod
    def error(cls, message: str, errors: List[str] = None) -> "StandardResponse":
        return cls(success=False, message=message, errors=errors)


class PaginationParams(BaseModel):
    page: int = 1
    limit: int = 20

    @property
    def skip(self) -> int:
        return (self.page - 1) * self.limit


class PaginatedResponse(BaseModel, Generic[T]):
    items: List[T]
    total: int
    page: int
    limit: int
    pages: int

    @classmethod
    def create(cls, items: List[T], total: int, params: PaginationParams) -> "PaginatedResponse[T]":
        return cls(
            items=items,
            total=total,
            page=params.page,
            limit=params.limit,
            pages=(total + params.limit - 1) // params.limit,
        )
