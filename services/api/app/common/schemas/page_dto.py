import math
from typing import Generic, List, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class PageDto(BaseModel, Generic[T]):
    items: List[T]
    current_page: int = Field(..., serialization_alias="currentPage", examples=[1])
    size: int = Field(..., examples=[20])
    total_count: int = Field(..., serialization_alias="totalCount", examples=[0])
    total_pages: int = Field(..., serialization_alias="totalPages", examples=[0])
    has_next: bool = Field(..., serialization_alias="hasNext", examples=[False])
    has_prev: bool = Field(..., serialization_alias="hasPrev", examples=[False])

    model_config = {
        "from_attributes": True,
        "populate_by_name": True,
    }

    @classmethod
    def create(
        cls,
        items: List[T],
        page: int,
        size: int,
        total_count: int,
    ) -> "PageDto[T]":
        """
        PageDto를 간편하게 생성하는 클래스 메서드

        Args:
            items: 페이지의 아이템 리스트
            page: 현재 페이지 번호 (1부터 시작)
            size: 페이지 크기
            total_count: 전체 아이템 개수

        Returns:
            PageDto 인스턴스 (total_pages, has_next, has_prev 자동 계산)

        Example:
            >>> items = [item1, item2, item3]
            >>> page_dto = PageDto.create(items, page=1, size=20, total_count=100)
        """
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
