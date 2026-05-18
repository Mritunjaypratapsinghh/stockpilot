"""Pagination utility — cursor and offset-based pagination for API endpoints."""

from typing import Any

from beanie import Document
from fastapi import Query


class PaginationParams:
    """FastAPI dependency for pagination query params."""

    def __init__(self, page: int = Query(1, ge=1), limit: int = Query(50, ge=1, le=200)):
        self.page = page
        self.limit = limit
        self.skip = (page - 1) * limit


def paginated_response(items: list[Any], total: int, page: int, limit: int) -> dict:
    """Standard paginated response envelope."""
    return {
        "items": items,
        "total": total,
        "page": page,
        "limit": limit,
        "pages": (total + limit - 1) // limit if limit > 0 else 0,
        "has_next": page * limit < total,
    }


async def paginate_query(model: type[Document], query: dict, page: int = 1,
                         limit: int = 50, sort: str = "-created_at") -> dict:
    """Execute paginated query on a Beanie model. Returns standard envelope."""
    total = await model.find(query).count()
    skip = (page - 1) * limit
    items = await model.find(query).sort(sort).skip(skip).limit(limit).to_list()
    return paginated_response(items, total, page, limit)
