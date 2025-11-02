from pydantic import BaseModel, Field
from typing import Generic, TypeVar, List


T = TypeVar("T")


class PageDto(BaseModel, Generic[T]):
    items: List[T]
    current_page: int = Field(alias="currentPage", example=1)
    size: int = Field(alias="size", example=20)
    total_count: int = Field(alias="totalCount", example=0)
    total_pages: int = Field(alias="totalPages", example=0)
    has_next: bool = Field(alias="hasNext", example=False)
    has_prev: bool = Field(alias="hasPrev", example=False)

    model_config = {
        "from_attributes": True,
        "populate_by_name": True,
    }
