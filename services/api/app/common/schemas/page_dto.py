import math
from typing import Generic, List, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class PageDto(BaseModel, Generic[T]):
    items: List[T]
    current_page: int = Field(..., alias="currentPage")
    size: int = Field(...)
    total_count: int = Field(..., alias="totalCount")
    total_pages: int = Field(..., alias="totalPages")
    has_next: bool = Field(..., alias="hasNext")
    has_prev: bool = Field(..., alias="hasPrev")

    model_config = {
        "from_attributes": True,
        "populate_by_name": True,
    }

    @classmethod
    def create(
        cls, items: List[T], page: int, size: int, total_count: int
    ) -> "PageDto[T]":
        """PageDto를 간편하게 생성하는 클래스 메서드"""
        total_pages = math.ceil(total_count / size) if total_count > 0 else 0
        has_next = page < total_pages
        has_prev = page > 1

        return cls(
            items=items,
            current_page=page,
            size=size,
            total_count=total_count,
            total_pages=total_pages,
            has_next=has_next,
            has_prev=has_prev,
        )
