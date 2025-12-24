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
